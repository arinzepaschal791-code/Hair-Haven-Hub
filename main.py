import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# Configure for Railway
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')

db = SQLAlchemy(app)

# Simple Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Business config
WEBSITE_CONFIG = {
    'brand_name': 'NORA HAIR LINE',
    'tagline': 'Luxury for less...',
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
    'payment_config': {
        'account_number': '2059311531',
        'bank_name': 'UBA',
        'account_name': 'CHUKWUNEKE CHIAMAKA',
        'currency': 'NGN',
        'currency_symbol': '₦'
    }
}

def format_price(price):
    try:
        return f"₦{float(price):,.2f}"
    except:
        return "₦0.00"

def get_cart_count():
    """Safely get cart count"""
    try:
        if session.get('user_id'):
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if cart:
                return CartItem.query.filter_by(cart_id=cart.id).count()
    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
    return 0

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("✅ Database tables created")
        
        # Create default admin
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@norahairline.com'
            )
            db.session.add(admin)
            logger.info("👑 Created default admin: admin/admin123")
        
        # Create sample products
        if not Product.query.first():
            products = [
                Product(
                    name="Premium Bone Straight Hair 24\"",
                    description="24-inch premium quality 100% human hair, bone straight texture.",
                    price=134985.0,
                    category="hair",
                    image_url="/static/images/hair1.jpg",
                    stock=50,
                    featured=True
                ),
                Product(
                    name="Curly Brazilian Hair 22\"",
                    description="22-inch natural Brazilian curly hair, soft and bouncy.",
                    price=149985.0,
                    category="hair",
                    image_url="/static/images/hair2.jpg",
                    stock=30,
                    featured=True
                ),
                Product(
                    name="Lace Front Wig - Natural Black",
                    description="13x4 lace front wig, natural black color.",
                    price=194985.0,
                    category="wigs",
                    image_url="/static/images/wig1.jpg",
                    stock=20,
                    featured=True
                ),
                Product(
                    name="Hair Growth Oil 8oz",
                    description="Organic hair growth oil with rosemary and castor oil.",
                    price=37485.0,
                    category="care",
                    image_url="/static/images/oil1.jpg",
                    stock=100,
                    featured=False
                )
            ]
            for product in products:
                db.session.add(product)
            logger.info(f"🛍️ Created {len(products)} sample products")
        
        db.session.commit()
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        db.session.rollback()

# FIXED CONTEXT PROCESSOR - This injects variables into ALL templates
@app.context_processor
def inject_globals():
    """Inject variables into all templates"""
    try:
        cart_count = get_cart_count()
    except:
        cart_count = 0
    
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
        featured_products = Product.query.filter_by(featured=True).limit(8).all()
        new_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
        
        # Format prices
        for product in featured_products + new_products:
            product.formatted_price = format_price(product.price)
        
        return render_template('index.html',
                             featured_products=featured_products,
                             new_products=new_products)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        # Return empty lists if error
        return render_template('index.html',
                             featured_products=[],
                             new_products=[])

@app.route('/shop')
@app.route('/products')
def products_page():
    """Products page"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
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
                             category='',
                             search='')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
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
        
        # Demo login - replace with database check
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
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid credentials.', 'error')
    
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
                
            except Exception as e:
                db.session.rollback()
                if 'unique' in str(e).lower():
                    flash('Email already registered.', 'error')
                else:
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
    cart_items = []  # Empty for now
    return render_template('cart.html', cart_items=cart_items)

@app.route('/checkout')
def checkout():
    """Checkout page"""
    return render_template('checkout.html')

@app.route('/admin')
def admin_login_page():
    """Admin login page"""
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))
    
    try:
        stats = {
            'products': Product.query.count(),
            'users': User.query.count()
        }
        
        recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_products=recent_products)
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return render_template('admin/dashboard.html',
                             stats={'products': 0, 'users': 0},
                             recent_products=[])

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))
    
    products = Product.query.order_by(Product.created_at.desc()).all()
    for product in products:
        product.formatted_price = format_price(product.price)
    
    return render_template('admin/products.html', products=products)

# Static file serving
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

# API endpoints
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'database': DATABASE_URL is not None,
        'time': datetime.now().isoformat()
    })

@app.route('/api/products')
def api_products():
    try:
        products = Product.query.limit(20).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'category': p.category,
            'image_url': p.image_url,
            'stock': p.stock
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n{'='*60}")
    print(f"🚀 NORA HAIR LINE")
    print(f"{'='*60}")
    print(f"🌐 URL: http://localhost:{port}")
    print(f"👤 Customer login: customer@example.com / password")
    print(f"👑 Admin login: admin@norahairline.com / admin123")
    print(f"{'='*60}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
