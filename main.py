# main.py - Optimized Production Version
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for, flash, abort
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import json
import uuid
import secrets
import logging
from functools import wraps
import time
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import models with fallback
MODELS_AVAILABLE = True
try:
    from models import db, Admin, Product, Order, Review, User, Cart, CartItem, Payment, OrderItem
    logger.info("✓ All models imported successfully")
except ImportError as e:
    logger.warning(f"Models import warning: {e}")
    MODELS_AVAILABLE = False
    # Create dummy classes to prevent crashes
    class DummyModel:
        query = None
        def __init__(self, **kwargs):
            pass
    
    db = DummyModel()
    Admin = Product = Order = Review = User = Cart = CartItem = Payment = OrderItem = DummyModel

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app, supports_credentials=True)

# ============ CONFIGURATION ============
class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///norahairline.db')
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
    
    # Performance
    JSONIFY_PRETTYPRINT_REGULAR = False
    TEMPLATES_AUTO_RELOAD = os.environ.get('FLASK_ENV') == 'development'

app.config.from_object(Config)

# Initialize database if available
if MODELS_AVAILABLE:
    db.init_app(app)

# ============ BUSINESS CONFIGURATION ============
PAYMENT_CONFIG = {
    'account_number': '2059311531',
    'bank_name': 'UBA',
    'account_name': 'CHUKWUNEKE CHIAMAKA',
    'currency': 'NGN',
    'currency_symbol': '₦',
    'shipping_fee': Decimal('2000.00'),
    'free_shipping_threshold': Decimal('50000.00'),
    'tax_rate': Decimal('0.075'),  # 7.5% VAT
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
    'payment_config': PAYMENT_CONFIG,
    'social': {
        'facebook': '#',
        'twitter': '#',
        'instagram': 'https://instagram.com/norahairline',
        'pinterest': '#',
    }
}

# ============ HELPER FUNCTIONS ============
def ensure_directories():
    """Create all required directories"""
    directories = [
        'static/images/products',
        'static/images/logo',
        'static/css',
        'static/js',
        'static/uploads',
        'templates/admin',
        'templates/email',
        'templates/partials',
        app.config['UPLOAD_FOLDER'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'images'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'videos'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'proofs'),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def format_price(price):
    """Format price as Nigerian Naira"""
    try:
        if isinstance(price, (int, float, Decimal)):
            return f"₦{price:,.2f}"
        return f"₦{float(price):,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"

def calculate_totals(subtotal):
    """Calculate shipping, tax, and total"""
    shipping = Decimal('0.00')
    if subtotal > 0:
        if subtotal >= PAYMENT_CONFIG['free_shipping_threshold']:
            shipping = Decimal('0.00')
        else:
            shipping = PAYMENT_CONFIG['shipping_fee']
    
    tax = subtotal * PAYMENT_CONFIG['tax_rate']
    total = subtotal + shipping + tax
    
    return {
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
        'formatted_subtotal': format_price(subtotal),
        'formatted_shipping': format_price(shipping),
        'formatted_tax': format_price(tax),
        'formatted_total': format_price(total)
    }

# ============ DECORATORS ============
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============ DATABASE INITIALIZATION ============
def init_database():
    """Initialize database with default data"""
    if not MODELS_AVAILABLE:
        logger.warning("Models not available - skipping database initialization")
        return
    
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            logger.info("✅ Database tables created")
            
            # Create default admin
            if not Admin.query.first():
                admin = Admin(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    email='admin@norahairline.com',
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(admin)
                logger.info("👑 Created default admin")
            
            # Create sample products if none exist
            if not Product.query.first():
                sample_products = [
                    {
                        'name': "Premium Bone Straight Hair 24\"",
                        'description': "24-inch premium quality 100% human hair, bone straight texture.",
                        'price': Decimal('134985.00'),
                        'category': 'hair',
                        'stock': 50,
                        'featured': True,
                        'image_url': '/static/images/products/hair1.jpg'
                    },
                    {
                        'name': "Curly Brazilian Hair 22\"",
                        'description': "22-inch natural Brazilian curly hair, soft and bouncy.",
                        'price': Decimal('149985.00'),
                        'category': 'hair',
                        'stock': 30,
                        'featured': True,
                        'image_url': '/static/images/products/hair2.jpg'
                    }
                ]
                
                for prod_data in sample_products:
                    product = Product(
                        **prod_data,
                        sku=f"PROD-{uuid.uuid4().hex[:8].upper()}",
                        image_urls=json.dumps([prod_data['image_url']]),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(product)
                
                logger.info(f"🛍️ Created {len(sample_products)} sample products")
            
            db.session.commit()
            logger.info("✅ Database initialization completed")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Database initialization error: {e}")
            raise

# ============ CONTEXT PROCESSORS ============
@app.context_processor
def inject_template_vars():
    """Inject variables into all templates"""
    cart_info = {
        'items': 0,
        'subtotal': Decimal('0.00'),
        'formatted_subtotal': format_price(0)
    }
    
    if MODELS_AVAILABLE and session.get('user_id'):
        try:
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if cart:
                cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
                cart_info['items'] = len(cart_items)
                subtotal = sum(
                    item.quantity * item.product.price 
                    for item in cart_items 
                    if item and item.product
                )
                cart_info['subtotal'] = subtotal
                cart_info['formatted_subtotal'] = format_price(subtotal)
        except Exception as e:
            logger.error(f"Error loading cart: {e}")
    
    return {
        **WEBSITE_CONFIG,
        'cart': cart_info,
        'user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email')
        },
        'admin': session.get('admin_logged_in'),
        'current_year': datetime.now().year,
        'current_path': request.path
    }

# ============ WEBSITE ROUTES ============
@app.route('/')
def index():
    """Homepage"""
    try:
        featured_products = []
        new_products = []
        
        if MODELS_AVAILABLE:
            featured_products = Product.query.filter_by(
                featured=True, 
                stock__gt=0
            ).order_by(
                Product.created_at.desc()
            ).limit(8).all()
            
            new_products = Product.query.filter(
                Product.stock > 0
            ).order_by(
                Product.created_at.desc()
            ).limit(6).all()
        
        return render_template('index.html',
                             featured_products=featured_products,
                             new_products=new_products)
    except Exception as e:
        logger.error(f"Error loading homepage: {e}")
        return render_template('index.html',
                             featured_products=[],
                             new_products=[])

@app.route('/shop')
@app.route('/products')
def products_page():
    """Products listing"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'newest')
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        query = Product.query.filter(Product.stock > 0)
        
        # Apply filters
        if category and category != 'all':
            query = query.filter_by(category=category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.category.ilike(search_term)
                )
            )
        
        # Apply sorting
        if sort == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort == 'name':
            query = query.order_by(Product.name.asc())
        else:  # newest
            query = query.order_by(Product.created_at.desc())
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        products = pagination.items
        
        # Get categories for filter
        categories = []
        if MODELS_AVAILABLE:
            categories = db.session.query(
                Product.category
            ).distinct().all()
            categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('products.html',
                             products=products,
                             pagination=pagination,
                             category=category,
                             search=search,
                             sort=sort,
                             categories=categories)
    except Exception as e:
        logger.error(f"Error loading products: {e}")
        return render_template('products.html',
                             products=[],
                             category='',
                             search='',
                             sort='newest',
                             categories=[])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
        if not MODELS_AVAILABLE:
            abort(404)
        
        product = Product.query.get_or_404(product_id)
        
        # Get related products
        related_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product_id,
            Product.stock > 0
        ).limit(4).all()
        
        # Get reviews
        reviews = []
        if hasattr(Review, 'query'):
            reviews = Review.query.filter_by(
                product_id=product_id,
                approved=True
            ).order_by(Review.created_at.desc()).all()
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products,
                             reviews=reviews)
    except Exception as e:
        logger.error(f"Error loading product {product_id}: {e}")
        flash('Product not found.', 'error')
        return redirect(url_for('products_page'))

# ============ AUTHENTICATION ROUTES ============
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not email or not password:
            flash('Please enter email and password.', 'error')
            return render_template('login.html')
        
        if not MODELS_AVAILABLE:
            flash('System temporarily unavailable.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash('Account is deactivated.', 'error')
                return render_template('login.html')
            
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session.permanent = remember
            
            flash('Login successful!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next') or url_for('index')
            return redirect(next_page)
        
        flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if not phone or len(phone) < 10:
            errors.append('Valid phone number is required')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if MODELS_AVAILABLE:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html',
                                 name=name,
                                 email=email,
                                 phone=phone)
        
        # Create user
        if MODELS_AVAILABLE:
            try:
                user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    password=generate_password_hash(password),
                    created_at=datetime.utcnow(),
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                
                # Create cart for user
                cart = Cart(
                    user_id=user.id,
                    status='active',
                    created_at=datetime.utcnow()
                )
                db.session.add(cart)
                db.session.commit()
                
                # Auto login
                session['user_id'] = user.id
                session['user_email'] = user.email
                session['user_name'] = user.name
                
                flash('Registration successful! Welcome to Nora Hair Line.', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {e}")
                flash('Registration failed. Please try again.', 'error')
        
        else:
            flash('Registration temporarily unavailable.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ============ CART ROUTES ============
@app.route('/cart')
@login_required
def cart_page():
    """Shopping cart"""
    try:
        if not MODELS_AVAILABLE:
            flash('Cart functionality temporarily unavailable.', 'error')
            return render_template('cart.html', cart_items=[])
        
        cart = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart:
            return render_template('cart.html', cart_items=[])
        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        
        # Calculate totals
        subtotal = Decimal('0.00')
        for item in cart_items:
            if item and item.product:
                item.item_total = item.quantity * item.product.price
                subtotal += item.item_total
                item.formatted_item_total = format_price(item.item_total)
                item.product.formatted_price = format_price(item.product.price)
        
        totals = calculate_totals(subtotal)
        
        return render_template('cart.html',
                             cart_items=cart_items,
                             **totals)
    except Exception as e:
        logger.error(f"Error loading cart: {e}")
        flash('Error loading cart.', 'error')
        return render_template('cart.html', cart_items=[])

@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def api_add_to_cart(product_id):
    """Add item to cart (API)"""
    try:
        if not MODELS_AVAILABLE:
            return jsonify({'success': False, 'message': 'System unavailable'}), 503
        
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        if quantity < 1:
            return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
        
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check stock
        if product.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Only {product.stock} items in stock'
            }), 400
        
        # Get or create cart
        cart = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart:
            cart = Cart(
                user_id=session['user_id'],
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(cart)
            db.session.flush()
        
        # Check if item exists in cart
        cart_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=product_id
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                created_at=datetime.utcnow()
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        # Get updated cart count
        cart_count = CartItem.query.filter_by(cart_id=cart.id).count()
        
        return jsonify({
            'success': True,
            'message': 'Added to cart',
            'cart_count': cart_count,
            'product': {
                'name': product.name,
                'price': float(product.price),
                'image': product.image_url
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding to cart: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ CHECKOUT ROUTES ============
@app.route('/checkout')
@login_required
def checkout_page():
    """Checkout page"""
    try:
        if not MODELS_AVAILABLE:
            flash('Checkout unavailable.', 'error')
            return redirect(url_for('cart_page'))
        
        cart = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('cart_page'))
        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('cart_page'))
        
        # Calculate subtotal
        subtotal = Decimal('0.00')
        for item in cart_items:
            if item and item.product:
                subtotal += item.quantity * item.product.price
        
        totals = calculate_totals(subtotal)
        
        return render_template('checkout.html',
                             cart_items=cart_items,
                             **totals)
    except Exception as e:
        logger.error(f"Error loading checkout: {e}")
        flash('Error loading checkout.', 'error')
        return redirect(url_for('cart_page'))

@app.route('/api/order/create', methods=['POST'])
@login_required
def api_create_order():
    """Create order API"""
    try:
        if not MODELS_AVAILABLE:
            return jsonify({'success': False, 'message': 'System unavailable'}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid data'}), 400
        
        # Get cart
        cart = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart:
            return jsonify({'success': False, 'message': 'Cart not found'}), 404
        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Calculate totals
        subtotal = Decimal('0.00')
        for item in cart_items:
            if item and item.product:
                subtotal += item.quantity * item.product.price
        
        totals = calculate_totals(subtotal)
        
        # Create order
        order = Order(
            user_id=session['user_id'],
            order_number=f"NHL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
            customer_name=data.get('name', session.get('user_name', '')),
            customer_email=data.get('email', session.get('user_email', '')),
            customer_phone=data.get('phone', ''),
            customer_address=data.get('address', ''),
            customer_city=data.get('city', ''),
            customer_state=data.get('state', ''),
            subtotal=subtotal,
            shipping_fee=totals['shipping'],
            tax_amount=totals['tax'],
            total_amount=totals['total'],
            status='pending',
            payment_status='pending',
            notes=data.get('notes', ''),
            created_at=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            if cart_item and cart_item.product:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price,
                    total_price=cart_item.quantity * cart_item.product.price
                )
                db.session.add(order_item)
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.updated_at = datetime.utcnow()
        
        # Create payment
        payment = Payment(
            order_id=order.id,
            amount=totals['total'],
            payment_method='bank_transfer',
            status='pending',
            reference=f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{order.id}",
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        
        # Update cart status
        cart.status = 'completed'
        cart.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order.id,
            'order_number': order.order_number,
            'payment_reference': payment.reference,
            'total': float(totals['total']),
            'formatted_total': totals['formatted_total']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating order: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ ORDER ROUTES ============
@app.route('/orders')
@login_required
def orders_page():
    """User orders"""
    try:
        if not MODELS_AVAILABLE:
            return render_template('orders.html', orders=[])
        
        orders = Order.query.filter_by(
            user_id=session['user_id']
        ).order_by(
            Order.created_at.desc()
        ).all()
        
        return render_template('orders.html', orders=orders)
    except Exception as e:
        logger.error(f"Error loading orders: {e}")
        return render_template('orders.html', orders=[])

@app.route('/order/<int:order_id>')
@login_required
def order_detail_page(order_id):
    """Order details"""
    try:
        if not MODELS_AVAILABLE:
            abort(404)
        
        order = Order.query.get_or_404(order_id)
        
        # Check ownership
        if order.user_id != session['user_id']:
            flash('Access denied.', 'error')
            return redirect(url_for('orders_page'))
        
        # Get order items
        order_items = []
        if hasattr(OrderItem, 'query'):
            order_items = OrderItem.query.filter_by(order_id=order_id).all()
        
        # Get payment info
        payment = None
        if hasattr(Payment, 'query'):
            payment = Payment.query.filter_by(order_id=order_id).first()
        
        return render_template('order_detail.html',
                             order=order,
                             order_items=order_items,
                             payment=payment)
    except Exception as e:
        logger.error(f"Error loading order {order_id}: {e}")
        flash('Order not found.', 'error')
        return redirect(url_for('orders_page'))

# ============ ADMIN ROUTES ============
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter username and password.', 'error')
            return render_template('admin/login.html')
        
        if not MODELS_AVAILABLE:
            flash('System unavailable.', 'error')
            return render_template('admin/login.html')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            if not admin.is_active:
                flash('Account is deactivated.', 'error')
                return render_template('admin/login.html')
            
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session.permanent = True
            
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid credentials.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        if not MODELS_AVAILABLE:
            return render_template('admin/dashboard.html', stats={})
        
        # Statistics
        stats = {
            'total_products': Product.query.count(),
            'total_orders': Order.query.count(),
            'total_users': User.query.count() if hasattr(User, 'query') else 0,
            'total_sales': db.session.query(
                db.func.sum(Order.total_amount)
            ).filter(Order.payment_status == 'completed').scalar() or Decimal('0.00'),
            'pending_orders': Order.query.filter_by(status='pending').count(),
            'low_stock': Product.query.filter(Product.stock < 10).count()
        }
        
        # Recent orders
        recent_orders = Order.query.order_by(
            Order.created_at.desc()
        ).limit(10).all()
        
        # Recent payments
        recent_payments = []
        if hasattr(Payment, 'query'):
            recent_payments = Payment.query.order_by(
                Payment.created_at.desc()
            ).limit(10).all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_orders=recent_orders,
                             recent_payments=recent_payments)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return render_template('admin/dashboard.html',
                             stats={},
                             recent_orders=[],
                             recent_payments=[])

# ============ STATIC FILES ============
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory('static', filename)
    except:
        abort(404)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    try:
        return send_from_directory('uploads', filename)
    except:
        abort(404)

# ============ API ENDPOINTS ============
@app.route('/api/products', methods=['GET'])
def api_products():
    """Products API"""
    try:
        if not MODELS_AVAILABLE:
            return jsonify([])
        
        category = request.args.get('category')
        featured = request.args.get('featured', '').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
        query = Product.query.filter(Product.stock > 0)
        
        if category:
            query = query.filter_by(category=category)
        
        if featured:
            query = query.filter_by(featured=True)
        
        query = query.order_by(Product.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'formatted_price': format_price(p.price),
            'category': p.category,
            'image_url': p.image_url or '/static/images/default-product.jpg',
            'stock': p.stock,
            'featured': p.featured,
            'sku': p.sku
        } for p in products])
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify([]), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': MODELS_AVAILABLE
    })

# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def not_found_error(error):
    """404 Error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 Error handler"""
    logger.error(f"Server error: {error}")
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """403 Error handler"""
    return render_template('403.html'), 403

# ============ APPLICATION START ============
if __name__ == '__main__':
    # Create directories
    ensure_directories()
    
    # Initialize database
    init_database()
    
    # Print startup information
    print("\n" + "="*60)
    print("🚀 NORA HAIR LINE E-COMMERCE PLATFORM")
    print("="*60)
    print(f"🌐 URL:              http://localhost:{os.environ.get('PORT', 10000)}")
    print(f"📁 Static Files:     {app.static_folder}")
    print(f"📁 Templates:        {app.template_folder}")
    print(f"💾 Database:         {app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]}")
    print(f"🔐 Admin Login:      /admin/login")
    print(f"💰 Payment Account:  {PAYMENT_CONFIG['account_number']}")
    print("="*60)
    
    # Run application
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
