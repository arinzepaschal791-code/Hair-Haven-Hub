from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Admin, Product, Order, Review
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
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ===== HELPER FUNCTIONS =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='images'):
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, unique_filename)
        file.save(filepath)
        return f"/static/uploads/{folder}/{unique_filename}"
    return None

# ===== CREATE DATABASE TABLES =====
with app.app_context():
    db.create_all()

# ===== PUBLIC ROUTES =====

@app.route('/')
def index():
    products = Product.query.filter_by(featured=True).limit(8).all()
    if not products:
        products = Product.query.limit(8).all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = Product.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.description.ilike(f'%{search}%'))
    
    products_list = query.order_by(Product.created_at.desc()).all()
    return render_template('products.html', products=products_list, category=category, search=search)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def order(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        order = Order(
            customer_name=request.form['name'],
            customer_email=request.form['email'],
            customer_phone=request.form['phone'],
            product_id=product_id,
            quantity=int(request.form['quantity']),
            total_price=product.price * int(request.form['quantity'])
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash(f'Order placed successfully! Order ID: {order.id}', 'success')
        return redirect(url_for('index'))
    
    return render_template('order.html', product=product)

# ===== ADMIN ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('admin/admin_login.html')
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('✅ Login successful! Welcome to Admin Dashboard', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid username or password', 'danger')
    
    return render_template('admin/admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Get statistics
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count() if hasattr(Review, 'query') else 0
    pending_orders = Order.query.filter_by(status='Pending').count()
    
    # Get recent data
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(5).all() if hasattr(Review, 'query') else []
    
    # Get low stock products
    low_stock = Product.query.filter(Product.stock < 10).limit(5).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_reviews=total_reviews,
                         pending_orders=pending_orders,
                         recent_products=recent_products,
                         recent_orders=recent_orders,
                         recent_reviews=recent_reviews,
                         low_stock=low_stock)

@app.route('/admin/products')
@login_required
def admin_products():
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.description.ilike(f'%{search}%'))
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    products_list = query.order_by(Product.created_at.desc()).all()
    
    return render_template('admin/admin_dashboard.html', 
                         products=products_list, 
                         search=search, 
                         category=category)

@app.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            category = request.form['category']
            stock = int(request.form.get('stock', 100))
            featured = 'featured' in request.form
            video_url = request.form.get('video_url', '')
            
            # Handle main image upload
            image_url = ''
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    image_url = save_uploaded_file(file, 'images')
            
            # Handle additional images
            gallery_images = []
            if 'gallery_images' in request.files:
                files = request.files.getlist('gallery_images')
                for file in files:
                    if file.filename:
                        gallery_url = save_uploaded_file(file, 'gallery')
                        gallery_images.append(gallery_url)
            
            # If no file uploaded, use URL from form
            if not image_url:
                image_url = request.form.get('image_url', '')
            
            # Create product
            product = Product(
                name=name,
                description=description,
                price=price,
                category=category,
                image_url=image_url,
                video_url=video_url,
                featured=featured,
                stock=stock,
                gallery_images=','.join(gallery_images) if gallery_images else ''
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'✅ Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            flash(f'❌ Error adding product: {str(e)}', 'danger')
    
    return render_template('admin/add_product.html')

@app.route('/admin/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = float(request.form['price'])
            product.category = request.form['category']
            product.stock = int(request.form.get('stock', 100))
            product.featured = 'featured' in request.form
            product.video_url = request.form.get('video_url', '')
            
            # Handle main image upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    product.image_url = save_uploaded_file(file, 'images')
            elif request.form.get('image_url'):
                product.image_url = request.form.get('image_url')
            
            # Handle gallery images
            if 'gallery_images' in request.files:
                files = request.files.getlist('gallery_images')
                gallery_images = []
                for file in files:
                    if file.filename:
                        gallery_url = save_uploaded_file(file, 'gallery')
                        gallery_images.append(gallery_url)
                
                if gallery_images:
                    # Keep existing images and add new ones
                    existing_images = product.gallery_images.split(',') if product.gallery_images else []
                    existing_images = [img for img in existing_images if img]
                    product.gallery_images = ','.join(existing_images + gallery_images)
            
            product.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash(f'✅ Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            flash(f'❌ Error updating product: {str(e)}', 'danger')
    
    # Parse gallery images
    gallery_images = []
    if product.gallery_images:
        gallery_images = [img.strip() for img in product.gallery_images.split(',') if img.strip()]
    
    return render_template('admin/edit_product.html', 
                         product=product, 
                         gallery_images=gallery_images)

@app.route('/admin/delete-product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'✅ Product "{name}" deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/toggle-featured/<int:id>')
@login_required
def toggle_featured(id):
    product = Product.query.get_or_404(id)
    product.featured = not product.featured
    db.session.commit()
    
    status = "featured" if product.featured else "unfeatured"
    flash(f'✅ Product "{product.name}" {status}!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/delete-image/<int:id>/<int:image_index>')
@login_required
def delete_image(id, image_index):
    product = Product.query.get_or_404(id)
    
    if product.gallery_images:
        images = product.gallery_images.split(',')
        if 0 <= image_index < len(images):
            # Remove the image
            images.pop(image_index)
            product.gallery_images = ','.join(images)
            db.session.commit()
            flash('✅ Image deleted successfully!', 'success')
    
    return redirect(url_for('edit_product', id=id))

@app.route('/admin/orders')
@login_required
def admin_orders():
    status = request.args.get('status', 'all')
    
    query = Order.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders, status=status)

@app.route('/admin/update-order/<int:id>', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    order.status = request.form['status']
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'✅ Order #{id} status updated to {order.status}', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    status = request.args.get('status', 'pending')
    
    query = Review.query
    
    if status == 'approved':
        query = query.filter_by(approved=True)
    elif status == 'pending':
        query = query.filter_by(approved=False)
    
    reviews = query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews, status=status)

@app.route('/admin/approve-review/<int:id>')
@login_required
def approve_review(id):
    review = Review.query.get_or_404(id)
    review.approved = True
    db.session.commit()
    
    # Update product rating
    product_reviews = Review.query.filter_by(product_id=review.product_id, approved=True).all()
    if product_reviews:
        avg_rating = sum(r.rating for r in product_reviews) / len(product_reviews)
        product = Product.query.get(review.product_id)
        if product:
            product.rating = round(avg_rating, 1)
            db.session.commit()
    
    flash('✅ Review approved!', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/delete-review/<int:id>')
@login_required
def delete_review(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('✅ Review deleted!', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('👋 Logged out successfully!', 'info')
    return redirect(url_for('index'))

# ===== SETUP ROUTES =====

@app.route('/setup-admin')
def setup_admin():
    # Check if admin already exists
    existing_admin = Admin.query.filter_by(username='admin').first()
    
    if existing_admin:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Exists</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                .card { max-width: 500px; margin: 0 auto; padding: 30px; background: #f8f9fa; border-radius: 10px; }
                h1 { color: #333; }
                .credentials { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .btn { display: inline-block; background: #6a11cb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>⚠️ Admin Already Exists</h1>
                <p>Admin account is already created.</p>
                <div class="credentials">
                    <p><strong>Username:</strong> admin</p>
                    <p><strong>Password:</strong> nora123</p>
                </div>
                <a class="btn" href="/admin/login">Go to Login Page</a>
                <a class="btn" href="/">Go to Homepage</a>
            </div>
        </body>
        </html>
        '''
    
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
        <title>✅ Admin Created</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .card { background: white; color: #333; padding: 40px; border-radius: 15px; max-width: 500px; margin: 0 auto; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
            h1 { color: #10b981; }
            .credentials { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .btn { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 10px; font-weight: bold; }
            .warning { color: #f59e0b; background: #fffbeb; padding: 15px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>✅ Admin Setup Complete!</h1>
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
                <a class="btn" href="/admin/login">Go to Login Page</a>
                <a class="btn" href="/" style="background: #4b5563;">Go to Homepage</a>
            </div>
        </div>
    </body>
    </html>
    '''

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
                'stock': 50,
                'featured': True,
                'rating': 4.8
            },
            {
                'name': 'Curly Hair Extension',
                'description': 'Natural Water Wave, 22 inches, Malaysian Hair, Tangle Free',
                'price': 109.99,
                'category': 'hair',
                'stock': 35,
                'featured': True,
                'rating': 4.9
            },
            {
                'name': 'Lace Front Wig - Blonde',
                'description': 'HD Lace Front Wig, 180% Density, Pre-plucked Hairline',
                'price': 199.99,
                'category': 'wigs',
                'stock': 20,
                'featured': True,
                'rating': 4.7
            },
            {
                'name': 'Hair Growth Shampoo',
                'description': 'Organic Hair Growth Shampoo, Sulfate Free, 500ml',
                'price': 24.99,
                'category': 'care',
                'stock': 100,
                'featured': True,
                'rating': 4.6
            }
        ]
        
        for data in sample_products:
            product = Product(**data)
            db.session.add(product)
        
        db.session.commit()
        
        return '''
        <html>
        <head>
            <title>✅ Setup Complete</title>
            <style>
                body { padding: 40px; text-align: center; font-family: Arial, sans-serif; }
                .success { color: #10b981; font-size: 48px; margin: 20px; }
                .btn { display: inline-block; background: #6a11cb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="success">✅</div>
            <h1>Sample Data Added!</h1>
            <p>4 sample products have been added to your database.</p>
            <div>
                <a class="btn" href="/">View Homepage</a>
                <a class="btn" href="/admin/dashboard">Go to Admin Dashboard</a>
            </div>
        </body>
        </html>
        '''
    
    return '''
    <html>
    <body style="padding: 40px; text-align: center;">
        <h1>⚠️ Already Setup</h1>
        <p>Sample data already exists.</p>
        <p><a href="/">Go to Homepage</a></p>
    </body>
    </html>
    '''

# ===== API ROUTES =====

@app.route('/api/stats')
@login_required
def api_stats():
    stats = {
        'products': Product.query.count(),
        'orders': Order.query.count(),
        'reviews': Review.query.count() if hasattr(Review, 'query') else 0,
        'pending_orders': Order.query.filter_by(status='Pending').count(),
        'revenue': sum(o.total_price for o in Order.query.filter_by(status='Delivered').all()) or 0
    }
    return jsonify(stats)

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
