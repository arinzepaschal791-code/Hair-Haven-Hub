# main.py - COMPLETE FIXED VERSION
import os
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import uuid
import secrets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models
try:
    from models import db, Admin, Product, Order, Review, User, Cart, CartItem, Payment, OrderItem
    MODELS_AVAILABLE = True
    logger.info("✓ All models imported successfully")
except ImportError as e:
    logger.error(f"Models import error: {e}")
    MODELS_AVAILABLE = False

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# Configure for Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///norahairline.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Initialize database
if MODELS_AVAILABLE:
    db.init_app(app)

# Business configuration
PAYMENT_CONFIG = {
    'account_number': '2059311531',
    'bank_name': 'UBA',
    'account_name': 'CHUKWUNEKE CHIAMAKA',
    'currency': 'NGN',
    'currency_symbol': '₦',
    'shipping_fee': 2000.00,
}

WEBSITE_CONFIG = {
    'brand_name': 'NORA HAIR LINE',
    'tagline': 'Luxury for less...',
    'wholesale': 'STRICTLY WHOLESALE DEAL IN: Closure | Frontals | 360 illusion frontal | Wigs | Bundles',
    'address': 'No 5 Veet gold plaza, directly opposite Abia gate @ Tradefair Shopping Center Badagry Express Way, Lagos State.',
    'phone': '08038707795',
    'whatsapp': 'https://wa.me/2348038707795',
    'instagram': '@norahairline',
    'instagram_url': 'https://instagram.com/norahairline',
    'currency': 'NGN',
    'currency_symbol': '₦',
    'contact_email': 'info@norahairline.com',
    'support_email': 'support@norahairline.com',
    'logo_url': '/static/images/logo.png',
    'favicon_url': '/static/images/favicon.ico',
    'year': datetime.now().year,
    'payment_config': PAYMENT_CONFIG
}

# Helper functions
def format_price(price):
    """Format price as Nigerian Naira"""
    try:
        return f"₦{float(price):,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"

def create_directories():
    """Create required directories"""
    directories = [
        'static',
        'static/images',
        'static/css',
        'static/js',
        'templates',
        'templates/admin',
        'uploads',
        'uploads/images',
        'uploads/videos'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")

def get_cart_count():
    """Get cart item count for current user"""
    try:
        if MODELS_AVAILABLE and session.get('user_id'):
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if cart:
                return CartItem.query.filter_by(cart_id=cart.id).count()
    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
    return 0

# Database initialization
def init_database():
    """Initialize database with sample data"""
    if not MODELS_AVAILABLE:
        return
    
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created successfully")
            
            # Create default admin
            if not Admin.query.first():
                admin = Admin(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    email='admin@norahairline.com',
                    created_at=datetime.utcnow()
                )
                db.session.add(admin)
                logger.info("👑 Created default admin: username='admin', password='admin123'")
            
            # Create sample products if none exist
            if not Product.query.first():
                products = [
                    Product(
                        name="Premium Bone Straight Hair 24\"",
                        description="24-inch premium quality 100% human hair, bone straight texture. Perfect for everyday wear. Easy to install and maintain.",
                        price=134985.0,
                        category="hair",
                        image_url="/static/images/hair1.jpg",
                        image_urls=json.dumps(["/static/images/hair1.jpg"]),
                        stock=50,
                        featured=True,
                        product_code=f"HAIR-{uuid.uuid4().hex[:8].upper()}",
                        created_at=datetime.utcnow()
                    ),
                    Product(
                        name="Curly Brazilian Hair 22\"",
                        description="22-inch natural Brazilian curly hair, soft and bouncy. Perfect for Afro-centric styles.",
                        price=149985.0,
                        category="hair",
                        image_url="/static/images/hair2.jpg",
                        image_urls=json.dumps(["/static/images/hair2.jpg"]),
                        stock=30,
                        featured=True,
                        product_code=f"HAIR-{uuid.uuid4().hex[:8].upper()}",
                        created_at=datetime.utcnow()
                    ),
                    Product(
                        name="Lace Front Wig - Natural Black",
                        description="13x4 lace front wig, natural black color, pre-plucked hairline. Looks 100% natural.",
                        price=194985.0,
                        category="wigs",
                        image_url="/static/images/wig1.jpg",
                        image_urls=json.dumps(["/static/images/wig1.jpg"]),
                        stock=20,
                        featured=True,
                        product_code=f"WIG-{uuid.uuid4().hex[:8].upper()}",
                        created_at=datetime.utcnow()
                    ),
                    Product(
                        name="Hair Growth Oil 8oz",
                        description="Organic hair growth oil with rosemary and castor oil. Promotes hair growth and thickness.",
                        price=37485.0,
                        category="care",
                        image_url="/static/images/oil1.jpg",
                        image_urls=json.dumps(["/static/images/oil1.jpg"]),
                        stock=100,
                        featured=False,
                        product_code=f"CARE-{uuid.uuid4().hex[:8].upper()}",
                        created_at=datetime.utcnow()
                    )
                ]
                
                for product in products:
                    db.session.add(product)
                
                logger.info(f"🛍️ Created {len(products)} sample products")
            
            db.session.commit()
            logger.info("✅ Database initialization completed")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Database initialization error: {str(e)}")

# Context processor
@app.context_processor
def inject_globals():
    """Inject variables into all templates"""
    cart_count = get_cart_count()
    
    return {
        **WEBSITE_CONFIG,
        'cart_count': cart_count,
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name'),
        'user_email': session.get('user_email'),
        'admin_logged_in': session.get('admin_logged_in'),
        'current_year': datetime.now().year,
        'now': datetime.now()
    }

# ============ ROUTES ============

@app.route('/')
def index():
    """Homepage"""
    try:
        featured_products = []
        if MODELS_AVAILABLE:
            featured_products = Product.query.filter_by(featured=True).order_by(
                Product.created_at.desc()
            ).limit(8).all()
            
            # Format prices
            for product in featured_products:
                product.formatted_price = format_price(product.price)
        
        return render_template('index.html', featured_products=featured_products)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('index.html', featured_products=[])

@app.route('/shop')
@app.route('/products')
def products_page():
    """Products page"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        products = []
        if MODELS_AVAILABLE:
            query = Product.query
            
            if category:
                query = query.filter_by(category=category)
            
            if search:
                query = query.filter(Product.name.ilike(f'%{search}%'))
            
            products = query.order_by(Product.created_at.desc()).all()
            
            # Format prices
            for product in products:
                product.formatted_price = format_price(product.price)
        
        return render_template('products.html',
                             products=products,
                             category=category,
                             search=search)
    except Exception as e:
        logger.error(f"Error in products_page: {e}")
        return render_template('products.html',
                             products=[],
                             category=category,
                             search=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
        if not MODELS_AVAILABLE:
            flash('Product not found.', 'error')
            return redirect(url_for('products_page'))
        
        product = Product.query.get_or_404(product_id)
        product.formatted_price = format_price(product.price)
        
        # Get related products
        related_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product_id
        ).limit(4).all()
        
        for p in related_products:
            p.formatted_price = format_price(p.price)
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products)
    except Exception as e:
        logger.error(f"Error in product_detail: {e}")
        flash('Product not found.', 'error')
        return redirect(url_for('products_page'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter email and password.', 'error')
            return render_template('login.html')
        
        # Demo login for testing
        if email == 'customer@example.com' and password == 'password':
            session['user_id'] = 1
            session['user_name'] = 'Demo Customer'
            session['user_email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        
        # Admin login
        if email == 'admin@norahairline.com' and password == 'admin123':
            session['admin_logged_in'] = True
            session['user_id'] = 999
            session['user_name'] = 'Admin'
            session['user_email'] = email
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # Check database
        if MODELS_AVAILABLE:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        
        flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if not name or not email or not password:
            flash('All fields are required.', 'error')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        else:
            try:
                if MODELS_AVAILABLE:
                    # Check if user exists
                    existing = User.query.filter_by(email=email).first()
                    if existing:
                        flash('Email already registered.', 'error')
                    else:
                        # Create user
                        user = User(
                            name=name,
                            email=email,
                            phone=phone,
                            password=generate_password_hash(password)
                        )
                        db.session.add(user)
                        db.session.commit()
                        
                        # Auto login
                        session['user_id'] = user.id
                        session['user_name'] = user.name
                        session['user_email'] = user.email
                        
                        flash('Registration successful!', 'success')
                        return redirect(url_for('index'))
                else:
                    flash('Registration temporarily unavailable.', 'error')
                    
            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {e}")
                flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    """Cart page"""
    return render_template('cart.html', cart_items=[])

@app.route('/checkout')
def checkout():
    """Checkout page"""
    return render_template('checkout.html')

@app.route('/orders')
def orders():
    """Orders page"""
    return render_template('orders.html', orders=[])

# ============ ADMIN ROUTES ============

@app.route('/admin')
def admin_login_page():
    """Admin login page"""
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('admin_logged_in'):
        flash('Please login as admin.', 'warning')
        return redirect(url_for('admin_login_page'))
    
    try:
        stats = {}
        recent_products = []
        
        if MODELS_AVAILABLE:
            stats = {
                'products': Product.query.count(),
                'orders': Order.query.count(),
                'users': User.query.count()
            }
            
            recent_products = Product.query.order_by(
                Product.created_at.desc()
            ).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_products=recent_products)
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return render_template('admin/dashboard.html',
                             stats={'products': 0, 'orders': 0, 'users': 0},
                             recent_products=[])

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    if not session.get('admin_logged_in'):
        flash('Please login as admin.', 'warning')
        return redirect(url_for('admin_login_page'))
    
    try:
        products = []
        if MODELS_AVAILABLE:
            products = Product.query.order_by(Product.created_at.desc()).all()
            for product in products:
                product.formatted_price = format_price(product.price)
        
        return render_template('admin/products.html', products=products)
    except Exception as e:
        logger.error(f"Admin products error: {e}")
        return render_template('admin/products.html', products=[])

# ============ API ROUTES ============

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': MODELS_AVAILABLE,
        'time': datetime.now().isoformat()
    })

@app.route('/api/products')
def api_products():
    """Products API"""
    try:
        if not MODELS_AVAILABLE:
            return jsonify([])
        
        products = Product.query.limit(20).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'formatted_price': format_price(p.price),
            'category': p.category,
            'image_url': p.image_url or '/static/images/default-product.jpg',
            'stock': p.stock,
            'featured': p.featured
        } for p in products])
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify([]), 500

# ============ STATIC FILES ============

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    return send_from_directory('uploads', filename)

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500

# ============ APPLICATION START ============

if __name__ == '__main__':
    # Create directories
    create_directories()
    
    # Initialize database
    init_database()
    
    # Start application
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n{'='*60}")
    print(f"🚀 NORA HAIR LINE")
    print(f"{'='*60}")
    print(f"🌐 Homepage: http://localhost:{port}")
    print(f"👤 Customer login: customer@example.com / password")
    print(f"👑 Admin login: admin@norahairline.com / admin123")
    print(f"{'='*60}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
