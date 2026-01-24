from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Admin, Product, Order, Review, Category
from datetime import datetime
import os
import uuid

app = Flask(__name__)

# ===== CONFIGURATION =====
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hairline-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///norahairline.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Fix for Render PostgreSQL URL
if 'DATABASE_URL' in os.environ:
    uri = os.environ.get('DATABASE_URL')
    if uri.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = uri.replace('postgres://', 'postgresql://', 1)

# ===== INITIALIZE =====
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ===== HELPER FUNCTIONS =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return f"/static/uploads/{unique_filename}"
    return None

# ===== CREATE DATABASE TABLES =====
with app.app_context():
    db.create_all()
    # Create default categories if they don't exist
    if not Category.query.first():
        default_categories = [
            Category(name='Hair Extensions', slug='hair', icon='fas fa-user'),
            Category(name='Wigs', slug='wigs', icon='fas fa-star'),
            Category(name='Hair Care', slug='care', icon='fas fa-spa'),
            Category(name='Accessories', slug='accessories', icon='fas fa-tshirt')
        ]
        for category in default_categories:
            db.session.add(category)
        db.session.commit()

# ===== PUBLIC ROUTES =====

# Home Page
@app.route('/')
def index():
    featured = Product.query.filter_by(featured=True).limit(8).all()
    latest = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    reviews = Review.query.filter_by(approved=True).order_by(Review.created_at.desc()).limit(5).all()
    
    # Get video products
    video_products = Product.query.filter(Product.video_url != None).limit(3).all()
    
    return render_template('index.html', 
                         featured=featured, 
                         latest=latest, 
                         reviews=reviews,
                         video_products=video_products)

# All Products Page
@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    sort = request.args.get('sort', 'newest')
    
    query = Product.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    # Sorting
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        # Would need order count for this - using rating for now
        query = query.order_by(Product.rating.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    products = query.all()
    categories = Category.query.all()
    
    return render_template('products.html', 
                         products=products, 
                         categories=categories,
                         selected_category=category,
                         sort=sort)

# Single Product Page
@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    related = Product.query.filter_by(category=product.category)\
                          .filter(Product.id != id)\
                          .limit(4).all()
    reviews = Review.query.filter_by(product_id=id, approved=True)\
                         .order_by(Review.created_at.desc()).all()
    
    return render_template('product_detail.html', 
                         product=product, 
                         related=related, 
                         reviews=reviews)

# Add Review
@app.route('/add-review/<int:product_id>', methods=['POST'])
def add_review(product_id):
    name = request.form.get('name')
    email = request.form.get('email')
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')
    
    review = Review(
        product_id=product_id,
        customer_name=name,
        customer_email=email,
        rating=rating,
        comment=comment,
        approved=False  # Admin must approve first
    )
    
    db.session.add(review)
    db.session.commit()
    
    # Update product rating
    product = Product.query.get(product_id)
    product_reviews = Review.query.filter_by(product_id=product_id, approved=True).all()
    if product_reviews:
        avg_rating = sum(r.rating for r in product_reviews) / len(product_reviews)
        product.rating = round(avg_rating, 1)
        db.session.commit()
    
    flash('Thank you for your review! It will appear after approval.', 'success')
    return redirect(url_for('product_detail', id=product_id))

# Quick Order (AJAX)
@app.route('/quick-order', methods=['POST'])
def quick_order():
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # In a real app, you'd save this to database
        # For now, just return success
        total = product.price * quantity
        
        return jsonify({
            'success': True,
            'message': f'Quick order received for {product.name}',
            'total': f'${total:.2f}'
        })
    except:
        return jsonify({'success': False, 'message': 'Error processing order'})

# Search Products
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        products = Product.query.filter(
            (Product.name.ilike(f'%{query}%')) | 
            (Product.description.ilike(f'%{query}%'))
        ).all()
    else:
        products = []
    
    return render_template('search.html', products=products, query=query)

# ===== ADMIN ROUTES =====

# Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('✅ Welcome to NoraHairLine Admin Dashboard!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid username or password', 'danger')
    
    return render_template('admin/login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='Pending').count(),
        'total_reviews': Review.query.count(),
        'pending_reviews': Review.query.filter_by(approved=False).count(),
        'recent_orders': Order.query.order_by(Order.created_at.desc()).limit(5).all(),
        'recent_reviews': Review.query.order_by(Review.created_at.desc()).limit(5).all()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

# Admin Products Management
@app.route('/admin/products')
@login_required
def admin_products():
    category = request.args.get('category', 'all')
    search_query = request.args.get('q', '')
    
    query = Product.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    
    products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()
    
    return render_template('admin/products.html', 
                         products=products, 
                         categories=categories,
                         selected_category=category,
                         search_query=search_query)

# Add Product
@app.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        featured = 'featured' in request.form
        stock = int(request.form.get('stock', 100))
        
        # Handle image upload
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                image_url = save_uploaded_file(file)
        
        # Handle video upload
        video_url = ''
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename:
                video_url = save_uploaded_file(video_file)
        
        # If no file uploaded, use URL from form
        if not image_url:
            image_url = request.form.get('image_url', '')
        
        if not video_url:
            video_url = request.form.get('video_url', '')
        
        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url,
            video_url=video_url,
            featured=featured,
            stock=stock,
            rating=5.0  # Default rating
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'✅ Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

# Edit Product
@app.route('/admin/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.category = request.form['category']
        product.featured = 'featured' in request.form
        product.stock = int(request.form.get('stock', 100))
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                product.image_url = save_uploaded_file(file)
        elif request.form.get('image_url'):
            product.image_url = request.form.get('image_url')
        
        # Handle video upload
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename:
                product.video_url = save_uploaded_file(video_file)
        elif request.form.get('video_url'):
            product.video_url = request.form.get('video_url')
        
        db.session.commit()
        flash(f'✅ Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html', product=product, categories=categories)

# Delete Product
@app.route('/admin/delete-product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    
    # Also delete associated reviews
    Review.query.filter_by(product_id=id).delete()
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'✅ Product "{name}" deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

# Manage Reviews
@app.route('/admin/reviews')
@login_required
def admin_reviews():
    status = request.args.get('status', 'all')
    
    query = Review.query
    
    if status == 'pending':
        query = query.filter_by(approved=False)
    elif status == 'approved':
        query = query.filter_by(approved=True)
    
    reviews = query.order_by(Review.created_at.desc()).all()
    
    return render_template('admin/reviews.html', reviews=reviews, status=status)

# Approve/Reject Review
@app.route('/admin/review/<int:id>/<action>')
@login_required
def review_action(id, action):
    review = Review.query.get_or_404(id)
    
    if action == 'approve':
        review.approved = True
        db.session.commit()
        
        # Update product rating
        product = Product.query.get(review.product_id)
        product_reviews = Review.query.filter_by(product_id=review.product_id, approved=True).all()
        if product_reviews:
            avg_rating = sum(r.rating for r in product_reviews) / len(product_reviews)
            product.rating = round(avg_rating, 1)
            db.session.commit()
        
        flash(f'✅ Review from {review.customer_name} approved!', 'success')
    elif action == 'reject':
        db.session.delete(review)
        db.session.commit()
        flash('❌ Review rejected and deleted.', 'success')
    
    return redirect(url_for('admin_reviews'))

# Manage Orders
@app.route('/admin/orders')
@login_required
def admin_orders():
    status = request.args.get('status', 'all')
    
    query = Order.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, status=status)

# Update Order Status
@app.route('/admin/order/<int:id>/update', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    order.status = request.form['status']
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'✅ Order #{id} status updated to {order.status}', 'success')
    return redirect(url_for('admin_orders'))

# Bulk Actions
@app.route('/admin/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form['action']
    selected_ids = request.form.getlist('selected_ids')
    
    if not selected_ids:
        flash('❌ No items selected', 'danger')
        return redirect(request.referrer)
    
    if action == 'delete_products':
        Product.query.filter(Product.id.in_(selected_ids)).delete(synchronize_session=False)
        flash(f'✅ {len(selected_ids)} products deleted', 'success')
    elif action == 'feature_products':
        Product.query.filter(Product.id.in_(selected_ids)).update({'featured': True}, synchronize_session=False)
        flash(f'✅ {len(selected_ids)} products featured', 'success')
    elif action == 'unfeature_products':
        Product.query.filter(Product.id.in_(selected_ids)).update({'featured': False}, synchronize_session=False)
        flash(f'✅ {len(selected_ids)} products unfeatured', 'success')
    elif action == 'approve_reviews':
        Review.query.filter(Review.id.in_(selected_ids)).update({'approved': True}, synchronize_session=False)
        flash(f'✅ {len(selected_ids)} reviews approved', 'success')
    
    db.session.commit()
    return redirect(request.referrer)

# Admin Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 Logged out successfully!', 'info')
    return redirect(url_for('index'))

# ===== SETUP ROUTES =====

# Create Admin Account with password: nora123
@app.route('/setup-admin')
def setup_admin():
    # Delete existing admin if any
    Admin.query.delete()
    
    # Create admin with password: nora123
    hashed_password = generate_password_hash('nora123', method='pbkdf2:sha256')
    new_admin = Admin(
        username='admin',
        password=hashed_password,
        email='admin@norahairline.com',
        full_name='Nora HairLine Admin'
    )
    
    db.session.add(new_admin)
    db.session.commit()
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Admin Setup Complete</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .card { background: white; color: #333; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); max-width: 500px; }
            .success { color: #10b981; font-size: 48px; margin-bottom: 20px; }
            .credentials { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea; }
            .btn { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 10px; font-weight: bold; transition: transform 0.3s; }
            .btn:hover { transform: translateY(-3px); }
            .warning { color: #f59e0b; background: #fffbeb; padding: 15px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="success">✅</div>
            <h1>Admin Setup Complete!</h1>
            <p>Your admin account has been created successfully.</p>
            
            <div class="credentials">
                <h3>Login Credentials:</h3>
                <p><strong>Username:</strong> <code style="background: #e5e7eb; padding: 5px 10px; border-radius: 4px;">admin</code></p>
                <p><strong>Password:</strong> <code style="background: #e5e7eb; padding: 5px 10px; border-radius: 4px;">nora123</code></p>
            </div>
            
            <div class="warning">
                <strong>⚠️ IMPORTANT:</strong> Change your password after first login!
            </div>
            
            <div style="margin-top: 30px;">
                <a class="btn" href="/login">Go to Login Page</a>
                <a class="btn" href="/" style="background: #4b5563;">Go to Homepage</a>
            </div>
        </div>
    </body>
    </html>
    '''

# Quick Setup - Add Sample Data
@app.route('/quick-setup')
def quick_setup():
    # Add sample products if none exist
    if not Product.query.first():
        sample_products = [
            {
                'name': 'Premium Bone Straight Hair',
                'description': '100% Virgin Brazilian Hair, 24 inches, Can be dyed and styled',
                'price': 129.99,
                'category': 'hair',
                'image_url': '/static/samples/hair1.jpg',
                'featured': True,
                'stock': 50,
                'rating': 4.8
            },
            {
                'name': 'Curly Hair Extensions',
                'description': 'Natural Water Wave, 22 inches, Malaysian Hair',
                'price': 109.99,
                'category': 'hair',
                'image_url': '/static/samples/hair2.jpg',
                'featured': True,
                'stock': 35,
                'rating': 4.9
            },
            {
                'name': 'Lace Front Wig - Blonde',
                'description': 'HD Lace Front Wig, Pre-plucked Hairline',
                'price': 199.99,
                'category': 'wigs',
                'image_url': '/static/samples/wig1.jpg',
                'video_url': '/static/samples/wig-video.mp4',
                'featured': True,
                'stock': 20,
                'rating': 4.7
            },
            {
                'name': 'Hair Growth Shampoo',
                'description': 'Organic Hair Growth Shampoo, 500ml',
                'price': 24.99,
                'category': 'care',
                'image_url': '/static/samples/shampoo.jpg',
                'featured': True,
                'stock': 100,
                'rating': 4.6
            }
        ]
        
        for data in sample_products:
            product = Product(**data)
            db.session.add(product)
        
        # Add sample reviews
        sample_reviews = [
            {
                'product_id': 1,
                'customer_name': 'Sarah Johnson',
                'customer_email': 'sarah@email.com',
                'rating': 5,
                'comment': 'Amazing quality! The hair looks so natural.',
                'approved': True
            },
            {
                'product_id': 2,
                'customer_name': 'Mike Smith',
                'customer_email': 'mike@email.com',
                'rating': 4,
                'comment': 'Good product, arrived on time.',
                'approved': True
            }
        ]
        
        for data in sample_reviews:
            review = Review(**data)
            db.session.add(review)
        
        db.session.commit()
        
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>✅ Setup Complete</title></head>
        <body style="padding: 40px; text-align: center;">
            <h1>✅ Sample Data Added!</h1>
            <p>4 sample products and 2 reviews have been added.</p>
            <p><a href="/">View Homepage</a> | <a href="/admin/dashboard">Go to Admin</a></p>
        </body>
        </html>
        '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>⚠️ Already Setup</title></head>
    <body style="padding: 40px; text-align: center;">
        <h1>⚠️ Already Setup</h1>
        <p>Sample data already exists.</p>
        <p><a href="/">Go to Homepage</a></p>
    </body>
    </html>
    '''

# ===== API ROUTES =====

# Get product data for AJAX
@app.route('/api/products')
def api_products():
    products = Product.query.all()
    data = []
    for p in products:
        data.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'image': p.image_url,
            'category': p.category,
            'rating': p.rating,
            'stock': p.stock
        })
    return jsonify(data)

# Get stats for dashboard
@app.route('/api/stats')
@login_required
def api_stats():
    stats = {
        'products': Product.query.count(),
        'orders': Order.query.count(),
        'reviews': Review.query.count(),
        'pending_orders': Order.query.filter_by(status='Pending').count(),
        'pending_reviews': Review.query.filter_by(approved=False).count(),
        'revenue': sum(o.total_price for o in Order.query.filter_by(status='Delivered').all()) or 0
    }
    return jsonify(stats)

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
