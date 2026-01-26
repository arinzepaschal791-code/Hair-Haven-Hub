import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random
import string

# ========== CREATE APP FIRST ==========
app = Flask(__name__)

# ========== CONFIGURATION ==========
# Configure database for Render compatibility
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ========== INITIALIZE EXTENSIONS ==========
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# ========== DATABASE MODELS ==========
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float, nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.String(300), default='default-product.jpg')
    images = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0)
    shipping_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    billing_address = db.Column(db.Text, nullable=True)
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    __tablename__ = 'contact_message'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== DATABASE INITIALIZATION (MUST BE DONE BEFORE ROUTES) ==========
def init_database():
    """Initialize database with default data - MUST be called before any routes"""
    print("🔄 Initializing database...", file=sys.stderr)
    
    try:
        # Create all tables
        with app.app_context():
            db.create_all()
            print("✅ Database tables created", file=sys.stderr)
            
            # Create admin user if not exists
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    username='admin',
                    email=admin_email,
                    password=generate_password_hash(admin_password),
                    is_admin=True
                )
                db.session.add(admin)
                print(f"✅ Admin user created: {admin_email}", file=sys.stderr)
            
            # Create default categories if none exist
            if Category.query.count() == 0:
                categories = [
                    ('Hair Extensions', 'hair-extensions', 'Premium quality hair extensions'),
                    ('Wigs', 'wigs', 'Natural looking wigs'),
                    ('Hair Care', 'hair-care', 'Products for hair maintenance'),
                    ('Accessories', 'accessories', 'Hair accessories'),
                    ('Tools', 'tools', 'Hair styling tools')
                ]
                
                for name, slug, desc in categories:
                    category = Category(name=name, slug=slug, description=desc)
                    db.session.add(category)
                
                print("✅ Default categories created", file=sys.stderr)
            
            # Create sample products if none exist
            if Product.query.count() == 0:
                categories = Category.query.all()
                
                sample_products = [
                    ('Brazilian Body Wave', 129.99, 99.99, 50, 'Premium Brazilian body wave hair extensions'),
                    ('Peruvian Straight', 149.99, 119.99, 30, 'Silky straight Peruvian hair'),
                    ('Lace Front Wig', 199.99, None, 20, 'Natural looking lace front wig'),
                    ('Hair Vitamins', 29.99, 24.99, 100, 'Essential vitamins for hair growth'),
                    ('Hair Dryer', 89.99, 79.99, 25, 'Professional hair dryer')
                ]
                
                for i, (name, price, sale_price, stock, desc) in enumerate(sample_products):
                    category = categories[i % len(categories)]
                    product = Product(
                        name=name,
                        slug=name.lower().replace(' ', '-'),
                        sku=f'PROD-{i+1:03d}',
                        description=desc,
                        short_description=f'Premium quality {name.lower()}',
                        price=price,
                        sale_price=sale_price,
                        stock=stock,
                        category_id=category.id,
                        image='default-product.jpg',
                        featured=(i < 3),
                        active=True
                    )
                    db.session.add(product)
                
                print("✅ Sample products created", file=sys.stderr)
            
            try:
                db.session.commit()
                print("✅ Database initialized successfully", file=sys.stderr)
                return True
            except Exception as e:
                db.session.rollback()
                print(f"❌ Database commit error: {e}", file=sys.stderr)
                return False
                
    except Exception as e:
        print(f"❌ Database initialization error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

# ========== INITIALIZE DATABASE NOW (BEFORE ANYTHING ELSE) ==========
init_database()

# ========== FLASK-LOGIN SETUP ==========
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# ========== CONTEXT PROCESSORS ==========
@app.context_processor
def inject_global_vars():
    """Make variables available to all templates"""
    try:
        categories = Category.query.all()
    except:
        categories = []
    
    cart_count = 0
    if 'cart' in session:
        cart_count = len(session['cart'])
    
    return dict(
        current_user=current_user,
        now=datetime.now(),
        categories=categories,
        cart_count=cart_count,
        current_year=datetime.now().year,
        app_name="Nora Hair Line"
    )

# ========== HELPER FUNCTIONS ==========
def generate_order_number():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'ORD-{timestamp}-{random_str}'

def generate_sku(name):
    prefix = ''.join([word[:3].upper() for word in name.split()[:2]])
    random_num = ''.join(random.choices(string.digits, k=6))
    return f'{prefix}-{random_num}'

def calculate_cart_total():
    total = 0
    if 'cart' in session:
        for item in session['cart']:
            total += item.get('price', 0) * item.get('quantity', 1)
    return total

# ========== DECORATORS ==========
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin area.', 'warning')
            return redirect(url_for('admin_login'))
        
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"❌ 500 Error: {error}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    
    # Simple error page without database queries
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>500 - Internal Server Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #d9534f; }
            .container { max-width: 600px; margin: 0 auto; }
            .btn { display: inline-block; padding: 10px 20px; margin: 10px; 
                   background: #007bff; color: white; text-decoration: none; 
                   border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>500 - Internal Server Error</h1>
            <p>We're experiencing technical difficulties. Please try again later.</p>
            <p><strong>Nora Hair Line</strong></p>
            <a href="/" class="btn">Go Home</a>
            <a href="javascript:history.back()" class="btn">Go Back</a>
        </div>
    </body>
    </html>
    ''', 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

# ========== PUBLIC ROUTES ==========
@app.route('/')
def home():
    """Homepage with featured products"""
    try:
        # Get featured products
        featured_products = Product.query.filter_by(featured=True, active=True).limit(8).all()
        
        # Get new arrivals (latest products)
        new_products = Product.query.filter_by(active=True).order_by(Product.created_at.desc()).limit(8).all()
        
        # Get categories for homepage
        categories = Category.query.all()
        
        # Get featured reviews
        featured_reviews = Review.query.filter_by(is_featured=True, is_approved=True).limit(3).all()
        
        return render_template('index.html',
                             featured_products=featured_products,
                             new_products=new_products,
                             categories=categories,
                             featured_reviews=featured_reviews)
    except Exception as e:
        print(f"❌ Homepage error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # Fallback homepage if database query fails
        return render_template('index.html',
                             featured_products=[],
                             new_products=[],
                             categories=[],
                             featured_reviews=[])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            db.session.add(contact_msg)
            db.session.commit()
            
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html')

@app.route('/products')
def products():
    try:
        category_id = request.args.get('category', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 12
        search_query = request.args.get('q', '')
        
        query = Product.query.filter_by(active=True)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search_query:
            query = query.filter(
                Product.name.ilike(f'%{search_query}%') |
                Product.description.ilike(f'%{search_query}%')
            )
        
        products_paginated = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = Category.query.all()
        selected_category = Category.query.get(category_id) if category_id else None
        
        return render_template('products.html',
                             products=products_paginated,
                             categories=categories,
                             selected_category=selected_category,
                             search_query=search_query)
    except Exception as e:
        print(f"❌ Products page error: {e}", file=sys.stderr)
        return render_template('products.html',
                             products=[],
                             categories=[],
                             selected_category=None,
                             search_query='')

@app.route('/product/<slug>')
def product_detail(slug):
    try:
        product = Product.query.filter_by(slug=slug, active=True).first_or_404()
        
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.active == True
        ).limit(4).all()
        
        reviews = Review.query.filter_by(
            product_id=product.id,
            is_approved=True
        ).order_by(Review.created_at.desc()).all()
        
        avg_rating = 0
        if reviews:
            avg_rating = sum([r.rating for r in reviews]) / len(reviews)
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products,
                             reviews=reviews,
                             avg_rating=round(avg_rating, 1))
    except Exception as e:
        print(f"❌ Product detail error: {e}", file=sys.stderr)
        abort(404)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    subtotal = calculate_cart_total()
    tax = subtotal * 0.08
    shipping = 0 if subtotal == 0 else 5.99
    total = subtotal + tax + shipping
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         tax=tax,
                         shipping=shipping,
                         total=total)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        if not product.active or product.stock <= 0:
            flash('Product is not available.', 'warning')
            return redirect(request.referrer or url_for('products'))
        
        quantity = int(request.form.get('quantity', 1))
        
        if 'cart' not in session:
            session['cart'] = []
        
        cart = session['cart']
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] += quantity
                session.modified = True
                flash(f'Added {quantity} more of {product.name} to cart.', 'success')
                return redirect(request.referrer or url_for('cart'))
        
        cart.append({
            'id': product_id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.sale_price if product.sale_price else product.price),
            'quantity': quantity,
            'image': product.image,
            'stock': product.stock
        })
        session.modified = True
        
        flash(f'{product.name} added to cart!', 'success')
        return redirect(request.referrer or url_for('cart'))
    except Exception as e:
        flash('Error adding to cart.', 'danger')
        return redirect(request.referrer or url_for('products'))

# ========== SIMPLIFIED ADMIN ROUTES ==========
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password) and user.is_admin:
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login - Nora Hair Line</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f5f5f5; }
            .login-box { max-width: 400px; margin: 100px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .logo { text-align: center; font-size: 24px; font-weight: bold; color: #333; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="logo">Nora Hair Line</div>
            <h2>Admin Login</h2>
            <form method="POST">
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_users = User.query.count()
        
        completed_orders = Order.query.filter_by(payment_status='paid').all()
        total_revenue = sum(order.final_amount for order in completed_orders)
        
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        low_stock = Product.query.filter(Product.stock < 10, Product.active == True).count()
        
        return render_template('admin/dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_users=total_users,
                             total_revenue=total_revenue,
                             recent_orders=recent_orders,
                             low_stock=low_stock)
    except Exception as e:
        print(f"❌ Dashboard error: {e}", file=sys.stderr)
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('admin_login'))

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
        categories = Category.query.all()
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Products - Admin</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
                th { background: #f5f5f5; }
                .btn { padding: 5px 10px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; }
                .btn-primary { background: #007bff; color: white; }
                .btn-success { background: #28a745; color: white; }
                .btn-danger { background: #dc3545; color: white; }
            </style>
        </head>
        <body>
            <h1>Product Management</h1>
            <a href="/admin/dashboard" style="margin-bottom: 20px; display: inline-block;">← Back to Dashboard</a>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        ''' + ''.join([f'''
                    <tr>
                        <td>{p.id}</td>
                        <td>{p.name}</td>
                        <td>${p.price}</td>
                        <td>{p.stock}</td>
                        <td>{'Active' if p.active else 'Inactive'}</td>
                        <td>
                            <button class="btn btn-primary">Edit</button>
                            <button class="btn btn-danger">Delete</button>
                        </td>
                    </tr>
        ''' for p in products]) + '''
                </tbody>
            </table>
            <div style="margin-top: 20px;">
                <button class="btn btn-success">+ Add New Product</button>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f'Error loading products: {str(e)}', 500

# ========== API ENDPOINTS ==========
@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/stats')
@login_required
@admin_required
def api_stats():
    try:
        stats = {
            'total_products': Product.query.count(),
            'total_orders': Order.query.count(),
            'total_revenue': sum(o.final_amount for o in Order.query.filter_by(payment_status='paid').all()),
            'pending_orders': Order.query.filter_by(status='pending').count(),
        }
        return jsonify(stats)
    except:
        return jsonify({'error': 'Failed to fetch stats'}), 500

# ========== SIMPLE TEMPLATE RENDERING ==========
@app.route('/test')
def test():
    """Simple test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test - Nora Hair Line</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .success { color: green; font-size: 24px; }
        </style>
    </head>
    <body>
        <h1>Nora Hair Line</h1>
        <div class="success">✅ Website is working!</div>
        <p>Database: Connected</p>
        <p>Admin: Ready</p>
        <p><a href="/">Go to Homepage</a></p>
        <p><a href="/admin/login">Admin Login</a></p>
    </body>
    </html>
    '''

# ========== APPLICATION FACTORY ==========
def create_app():
    """Application factory for Gunicorn"""
    return app

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Nora Hair Line starting on port {port}", file=sys.stderr)
    print(f"🔗 http://localhost:{port}", file=sys.stderr)
    print(f"🔗 http://localhost:{port}/admin/login", file=sys.stderr)
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
