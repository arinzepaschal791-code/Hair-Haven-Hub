# main.py - FIXED VERSION WITH PROPER DATABASE INITIALIZATION
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates',
           static_url_path='/static')

# Configuration - USE SQLITE FOR SIMPLICITY
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'  # Fixed path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# ========== DATABASE MODELS ==========
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'product'  # EXPLICIT TABLE NAME
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Login Manager
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Website Configuration
WEBSITE_CONFIG = {
    'brand_name': 'NORA HAIR LINE',
    'tagline': 'Premium 100% Human Hair',
    'slogan': 'Luxury for less...',
    'description': 'Premium 100% human hair extensions, wigs, and hair products at wholesale prices.',
    'address': 'No 5 Veet Gold Plaza, opposite Abia gate @ Tradefair Shopping Center, Badagry Express Way, Lagos State.',
    'phone': '08038707795',
    'whatsapp': 'https://wa.me/2348038707795',
    'instagram': 'norahairline',
    'email': 'info@norahairline.com',
    'currency': 'NGN',
    'currency_symbol': '₦',
    'year': datetime.now().year,
}

# Initialize Database Function
def init_database():
    """Initialize database with all tables and sample data"""
    logger.info("Initializing database...")
    
    # Drop all tables first (for development)
    try:
        db.drop_all()
        logger.info("Dropped all tables")
    except Exception as e:
        logger.warning(f"Could not drop tables: {e}")
    
    # Create all tables
    try:
        db.create_all()
        logger.info("✅ Created all database tables")
        
        # Create admin user
        if not User.query.filter_by(email='admin@norahairline.com').first():
            admin = User(
                username='admin',
                email='admin@norahairline.com',
                phone='08038707795',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            logger.info("✅ Created admin user: admin@norahairline.com / admin123")
        
        # Create sample categories
        categories = [
            {'name': 'Hair Extensions', 'slug': 'hair-extensions'},
            {'name': 'Wigs', 'slug': 'wigs'},
            {'name': 'Closures', 'slug': 'closures'},
            {'name': 'Frontals', 'slug': 'frontals'},
            {'name': 'Hair Care', 'slug': 'hair-care'},
        ]
        
        for cat_data in categories:
            if not Category.query.filter_by(slug=cat_data['slug']).first():
                category = Category(**cat_data)
                db.session.add(category)
        
        # Create sample products
        products = [
            Product(
                name="Brazilian Straight Hair 24''",
                slug="brazilian-straight-hair-24",
                description="Premium 100% Brazilian Virgin Hair, Straight Texture, 24 inches",
                price=25000.00,
                old_price=30000.00,
                category="Hair Extensions",
                image="hair1.jpg",
                stock=50,
                featured=True
            ),
            Product(
                name="Peruvian Curly Hair 22''",
                slug="peruvian-curly-hair-22",
                description="100% Peruvian Human Hair, Natural Curly Pattern, 22 inches",
                price=28000.00,
                old_price=35000.00,
                category="Hair Extensions",
                image="hair2.jpg",
                stock=30,
                featured=True
            ),
            Product(
                name="13x4 Lace Frontal Wig",
                slug="13x4-lace-frontal-wig",
                description="HD Lace Frontal Wig, Pre-plucked, Natural Hairline",
                price=45000.00,
                old_price=55000.00,
                category="Wigs",
                image="wig1.jpg",
                stock=20,
                featured=True
            ),
            Product(
                name="4x4 Lace Closure",
                slug="4x4-lace-closure",
                description="4x4 HD Lace Closure, Swiss Lace, Bleached Knots",
                price=18000.00,
                old_price=22000.00,
                category="Closures",
                image="closure1.jpg",
                stock=40,
                featured=True
            ),
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        logger.info(f"✅ Created {len(products)} sample products")
        logger.info(f"✅ Database initialization complete!")
        
        # Print debug info
        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print(f"📊 Total Products: {Product.query.count()}")
        print(f"📁 Total Categories: {Category.query.count()}")
        print(f"👑 Admin User: admin@norahairline.com / admin123")
        print("="*60)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Database initialization failed: {e}")
        raise

# Helper Functions
def format_price(price):
    """Format price as Nigerian Naira"""
    try:
        return f"₦{float(price):,.2f}"
    except:
        return "₦0.00"

# Initialize database on startup
with app.app_context():
    try:
        # Check if database exists
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Try to create tables only
        try:
            db.create_all()
            logger.info("Created tables only (no sample data)")
        except Exception as e2:
            logger.error(f"Failed to create tables: {e2}")

# Context Processor
@app.context_processor
def inject_globals():
    cart_count = 0
    if 'cart' in session:
        cart_count = len(session['cart'])
    
    return {
        **WEBSITE_CONFIG,
        'cart_count': cart_count,
        'current_year': datetime.now().year,
        'now': datetime.now()
    }

# ========== ROUTES ==========

@app.route('/')
def home():
    """Homepage"""
    try:
        featured_products = Product.query.filter_by(featured=True).limit(6).all()
        categories = Category.query.limit(5).all()
        
        # Format prices
        for product in featured_products:
            product.formatted_price = format_price(product.price)
            if product.old_price:
                product.formatted_old_price = format_price(product.old_price)
        
        return render_template('index.html',
                             featured_products=featured_products,
                             categories=categories)
    except Exception as e:
        logger.error(f"Home error: {e}")
        # Return empty data if database error
        return render_template('index.html',
                             featured_products=[],
                             categories=[])

@app.route('/shop')
def shop():
    """Shop page"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        products = query.order_by(Product.created_at.desc()).all()
        categories = Category.query.all()
        
        # Format prices
        for product in products:
            product.formatted_price = format_price(product.price)
            if product.old_price:
                product.formatted_old_price = format_price(product.old_price)
        
        return render_template('shop.html',
                             products=products,
                             categories=categories,
                             category=category,
                             search=search)
    except Exception as e:
        logger.error(f"Shop error: {e}")
        flash('Error loading products. Please try again.', 'error')
        return render_template('shop.html',
                             products=[],
                             categories=[],
                             category='',
                             search='')

@app.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    try:
        product = Product.query.filter_by(slug=slug).first_or_404()
        product.formatted_price = format_price(product.price)
        if product.old_price:
            product.formatted_old_price = format_price(product.old_price)
        
        # Get related products
        related_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product.id
        ).limit(4).all()
        
        for p in related_products:
            p.formatted_price = format_price(p.price)
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products)
    except Exception as e:
        logger.error(f"Product detail error: {e}")
        flash('Product not found.', 'error')
        return redirect(url_for('shop'))

@app.route('/category/<slug>')
def category_page(slug):
    """Category page"""
    try:
        category = Category.query.filter_by(slug=slug).first_or_404()
        products = Product.query.filter_by(category=category.name).all()
        
        for product in products:
            product.formatted_price = format_price(product.price)
        
        return render_template('category.html',
                             category=category,
                             products=products)
    except Exception as e:
        logger.error(f"Category page error: {e}")
        flash('Category not found.', 'error')
        return redirect(url_for('shop'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# Login/Register Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, is_admin=False)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('home'))
    
    try:
        stats = {
            'products': Product.query.count(),
            'orders': Order.query.count(),
            'users': User.query.count(),
            'revenue': db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
        }
        
        recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_products=recent_products,
                             recent_orders=recent_orders)
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return render_template('admin/dashboard.html',
                             stats={'products': 0, 'orders': 0, 'users': 0, 'revenue': 0},
                             recent_products=[],
                             recent_orders=[])

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('home'))
    
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('admin/products.html', products=products)
    except Exception as e:
        logger.error(f"Admin products error: {e}")
        return render_template('admin/products.html', products=[])

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"500 Error: {error}")
    return render_template('500.html'), 500

# ========== START APPLICATION ==========

if __name__ == '__main__':
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('templates/admin', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n{'='*60}")
    print(f"🚀 NORA HAIR LINE E-COMMERCE")
    print(f"{'='*60}")
    print(f"🌐 Homepage: http://localhost:{port}")
    print(f"👑 Admin: admin@norahairline.com / admin123")
    print(f"🛒 Shop: http://localhost:{port}/shop")
    print(f"{'='*60}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
