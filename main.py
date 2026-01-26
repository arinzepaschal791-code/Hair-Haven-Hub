# main.py - Updated Version
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import json
import uuid
import secrets
from functools import wraps

# Import models
try:
    from models import db, Admin, Product, Order, Review, User, Cart, CartItem, Payment, OrderItem
    print("✓ All models imported successfully")
    HAS_REVIEW = True
    HAS_USER = True
    HAS_CART = True
    HAS_PAYMENT = True
    HAS_ORDER_ITEM = True
except ImportError as e:
    print(f"Import warning: {e}")
    try:
        from models import db, Admin, Product, Order
        Review = None
        User = None
        Cart = None
        CartItem = None
        Payment = None
        OrderItem = None
        HAS_REVIEW = False
        HAS_USER = False
        HAS_CART = False
        HAS_PAYMENT = False
        HAS_ORDER_ITEM = False
        print("✓ Imported basic models only")
    except ImportError as e2:
        print(f"Critical import error: {e2}")
        raise

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# ============ CONFIGURATION ============
class Config:
    # Database
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
        print(f"✓ Using PostgreSQL database")
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///norahairline.db'
        print("✓ Using SQLite database")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

app.config.from_object(Config)

# ============ PAYMENT CONFIGURATION ============
PAYMENT_CONFIG = {
    'account_number': '2059311531',
    'bank_name': 'UBA',
    'account_name': 'CHUKWUNEKE CHIAMAKA',
    'currency': 'NGN',
    'currency_symbol': '₦',
    'shipping_fee': 2000.00,  # NGN 2000 flat rate
    'minimum_order': 0.00
}

# ============ FILE UPLOAD SETUP ============
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

IMAGE_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
VIDEO_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')

# ============ HELPER FUNCTIONS ============
def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def format_price(price):
    """Format price as Nigerian Naira"""
    try:
        return f"₦{float(price):,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"

def create_directories():
    """Create all required directories"""
    directories = [
        'static',
        'static/images',
        'static/css',
        'static/js',
        'templates',
        'templates/admin',
        'templates/email',
        app.config['UPLOAD_FOLDER'],
        IMAGE_FOLDER,
        VIDEO_FOLDER
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_cart_count():
    """Get cart item count for current user"""
    if HAS_CART and session.get('user_id'):
        try:
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if cart:
                return CartItem.query.filter_by(cart_id=cart.id).count()
        except Exception as e:
            print(f"Error getting cart count: {e}")
    return 0

def calculate_cart_totals():
    """Calculate cart totals for current user"""
    if not session.get('user_id') or not HAS_CART:
        return {'subtotal': 0, 'shipping': 0, 'total': 0, 'items': 0}
    
    try:
        cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
        if not cart:
            return {'subtotal': 0, 'shipping': 0, 'total': 0, 'items': 0}
        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return {'subtotal': 0, 'shipping': 0, 'total': 0, 'items': 0}
        
        subtotal = 0
        for item in cart_items:
            if item and item.product:
                subtotal += item.quantity * item.product.price
        
        shipping = PAYMENT_CONFIG['shipping_fee'] if subtotal > 0 else 0
        total = subtotal + shipping
        
        return {
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'items': len(cart_items),
            'formatted_subtotal': format_price(subtotal),
            'formatted_shipping': format_price(shipping),
            'formatted_total': format_price(total)
        }
    except Exception as e:
        print(f"Error calculating cart totals: {e}")
        return {'subtotal': 0, 'shipping': 0, 'total': 0, 'items': 0}

# Initialize database
db.init_app(app)

# ============ WEBSITE CONFIGURATION ============
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

# ============ APPLICATION INITIALIZATION ============
with app.app_context():
    try:
        # Create directories
        create_directories()
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Create default admin if none exists
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@norahairline.com',
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            print("👑 Created default admin: username='admin', password='admin123'")
        
        # Create sample products if none exist
        if not Product.query.first():
            sample_products = [
                Product(
                    name="Premium Bone Straight Hair 24\"",
                    description="24-inch premium quality 100% human hair, bone straight texture. Perfect for everyday wear. Easy to install and maintain.",
                    price=134985.0,
                    category="hair",
                    image_url="/static/images/hair1.jpg",
                    image_urls=json.dumps(["/static/images/hair1.jpg"]),
                    stock=50,
                    featured=True,
                    sku=f"HAIR-{uuid.uuid4().hex[:8].upper()}",
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
                    sku=f"HAIR-{uuid.uuid4().hex[:8].upper()}",
                    created_at=datetime.utcnow()
                )
            ]
            
            for product in sample_products:
                db.session.add(product)
            print(f"🛍️ Created {len(sample_products)} sample products")
        
        db.session.commit()
        print("✅ Database initialization completed")
        
    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()

# ============ CONTEXT PROCESSORS ============
@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    cart_info = calculate_cart_totals()
    return {
        **WEBSITE_CONFIG,
        'cart_count': cart_info['items'],
        'cart_totals': cart_info,
        'current_path': request.path,
        'now': datetime.now()
    }

# ============ WEBSITE PAGES ============
@app.route('/')
def index():
    """Main store homepage"""
    try:
        featured_products = Product.query.filter_by(featured=True).order_by(
            Product.created_at.desc()
        ).limit(8).all()
        
        # Get latest products
        new_products = Product.query.order_by(
            Product.created_at.desc()
        ).limit(6).all()
        
        # Get reviews if available
        reviews = []
        if HAS_REVIEW:
            reviews = Review.query.filter_by(approved=True).order_by(
                Review.created_at.desc()
            ).limit(4).all()
        
        # Get categories with counts
        categories = {
            'hair': Product.query.filter_by(category='hair').count(),
            'wigs': Product.query.filter_by(category='wigs').count(),
            'care': Product.query.filter_by(category='care').count()
        }
        
        return render_template('index.html',
                             featured_products=featured_products,
                             new_products=new_products,
                             reviews=reviews,
                             categories=categories,
                             total_products=Product.query.count())
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html',
                             featured_products=[],
                             new_products=[],
                             reviews=[],
                             categories={'hair': 0, 'wigs': 0, 'care': 0},
                             total_products=0)

@app.route('/shop')
@app.route('/products')
def products_page():
    """Products shopping page"""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    
    try:
        query = Product.query
        
        # Apply filters
        if category and category != 'all':
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%'),
                    Product.category.ilike(f'%{search}%')
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
        
        products = query.all()
        
        # Get distinct categories for filter
        categories = db.session.query(
            Product.category
        ).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('products.html',
                             products=products,
                             category=category,
                             search=search,
                             sort=sort,
                             categories=categories)
    except Exception as e:
        print(f"Error in products_page: {e}")
        return render_template('products.html',
                             products=[],
                             category=category,
                             search=search,
                             sort=sort,
                             categories=[])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Get related products
        related_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product.id
        ).limit(4).all()
        
        # Get reviews
        reviews = []
        if HAS_REVIEW:
            reviews = Review.query.filter_by(
                product_id=product_id,
                approved=True
            ).order_by(Review.created_at.desc()).all()
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products,
                             reviews=reviews)
    except Exception as e:
        print(f"Error in product_detail: {e}")
        flash('Product not found.', 'error')
        return redirect(url_for('products_page'))

# ============ USER AUTHENTICATION ============
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('login.html')
        
        if HAS_USER:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_email'] = user.email
                session['user_name'] = user.name
                session.permanent = True
                
                flash('Login successful!', 'success')
                
                # Redirect to next page or home
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
        
        flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if not name:
            errors.append('Name is required')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if not phone:
            errors.append('Phone number is required')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if HAS_USER:
            # Check if user exists
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
        
        # Create new user
        if HAS_USER:
            user = User(
                name=name,
                email=email,
                phone=phone,
                password=generate_password_hash(password),
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Log user in
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session.permanent = True
            
            flash('Registration successful! Welcome to Nora Hair Line.', 'success')
            return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ============ CART FUNCTIONALITY ============
@app.route('/cart')
@login_required
def cart():
    """Shopping cart page"""
    try:
        if not HAS_CART:
            flash('Cart functionality is not available.', 'error')
            return redirect(url_for('index'))
        
        cart_obj = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart_obj:
            return render_template('cart.html', cart_items=[])
        
        cart_items = CartItem.query.filter_by(cart_id=cart_obj.id).all()
        
        # Calculate totals
        totals = calculate_cart_totals()
        
        return render_template('cart.html',
                             cart_items=cart_items,
                             **totals)
    except Exception as e:
        print(f"Error in cart: {e}")
        flash('Error loading cart.', 'error')
        return render_template('cart.html', cart_items=[])

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    try:
        if not HAS_CART:
            return jsonify({'success': False, 'message': 'Cart functionality not available'}), 400
        
        quantity = int(request.form.get('quantity', 1))
        
        if quantity < 1:
            return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
        
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check stock
        if product.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Only {product.stock} items available in stock'
            }), 400
        
        # Get or create cart
        cart_obj = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart_obj:
            cart_obj = Cart(
                user_id=session['user_id'],
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(cart_obj)
            db.session.flush()  # Get cart ID
        
        # Check if item already in cart
        cart_item = CartItem.query.filter_by(
            cart_id=cart_obj.id,
            product_id=product_id
        ).first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                return jsonify({
                    'success': False,
                    'message': f'Cannot add {quantity} more. Only {product.stock - cart_item.quantity} available.'
                }), 400
            cart_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                cart_id=cart_obj.id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        # Get updated cart count
        cart_count = CartItem.query.filter_by(cart_id=cart_obj.id).count()
        
        return jsonify({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': cart_count,
            'product_name': product.name
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding to cart: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update-cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity"""
    try:
        if not HAS_CART:
            return jsonify({'success': False, 'message': 'Cart functionality not available'}), 400
        
        quantity = int(request.form.get('quantity', 1))
        
        if quantity < 1:
            # Remove item if quantity is 0 or negative
            return remove_from_cart(item_id)
        
        cart_item = CartItem.query.get_or_404(item_id)
        
        # Verify cart belongs to user
        cart_obj = Cart.query.get(cart_item.cart_id)
        if cart_obj.user_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        product = Product.query.get(cart_item.product_id)
        
        # Check stock
        if product.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Only {product.stock} items available in stock'
            }), 400
        
        # Update quantity
        cart_item.quantity = quantity
        db.session.commit()
        
        # Calculate new totals
        item_total = cart_item.quantity * product.price
        totals = calculate_cart_totals()
        
        return jsonify({
            'success': True,
            'message': 'Cart updated',
            'item_total': float(item_total),
            'formatted_item_total': format_price(item_total),
            **totals
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart"""
    try:
        if not HAS_CART:
            return jsonify({'success': False, 'message': 'Cart functionality not available'}), 400
        
        cart_item = CartItem.query.get_or_404(item_id)
        
        # Verify cart belongs to user
        cart_obj = Cart.query.get(cart_item.cart_id)
        if cart_obj.user_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        db.session.delete(cart_item)
        db.session.commit()
        
        totals = calculate_cart_totals()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            **totals
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ CHECKOUT & PAYMENT ============
@app.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    try:
        if not HAS_CART:
            flash('Checkout functionality not available.', 'error')
            return redirect(url_for('cart'))
        
        cart_obj = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart_obj:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('cart'))
        
        cart_items = CartItem.query.filter_by(cart_id=cart_obj.id).all()
        if not cart_items:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('cart'))
        
        totals = calculate_cart_totals()
        
        return render_template('checkout.html', **totals)
        
    except Exception as e:
        print(f"Error in checkout: {e}")
        flash('Error loading checkout.', 'error')
        return redirect(url_for('cart'))

@app.route('/place-order', methods=['POST'])
@login_required
def place_order():
    """Place order and create payment"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400
        
        # Get cart
        cart_obj = Cart.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not cart_obj:
            return jsonify({'success': False, 'message': 'Cart not found'}), 400
        
        cart_items = CartItem.query.filter_by(cart_id=cart_obj.id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Calculate total
        subtotal = sum(item.quantity * item.product.price for item in cart_items if item.product)
        shipping = PAYMENT_CONFIG['shipping_fee']
        total = subtotal + shipping
        
        # Create order
        order = Order(
            user_id=session['user_id'],
            customer_name=data.get('name', session.get('user_name', '')),
            customer_email=data.get('email', session.get('user_email', '')),
            customer_phone=data.get('phone', ''),
            customer_address=data.get('address', ''),
            customer_city=data.get('city', ''),
            customer_state=data.get('state', ''),
            total_price=total,
            subtotal=subtotal,
            shipping_fee=shipping,
            status='pending',
            payment_status='pending',
            notes=data.get('notes', ''),
            created_at=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        if HAS_ORDER_ITEM:
            for cart_item in cart_items:
                if cart_item.product:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=cart_item.product_id,
                        product_name=cart_item.product.name,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.product.price,
                        total_price=cart_item.quantity * cart_item.product.price
                    )
                    db.session.add(order_item)
        
        # Create payment record
        if HAS_PAYMENT:
            reference = f"NHL{datetime.now().strftime('%Y%m%d%H%M%S')}{order.id:04d}"
            payment = Payment(
                order_id=order.id,
                amount=total,
                payment_method='bank_transfer',
                status='pending',
                reference=reference,
                created_at=datetime.utcnow()
            )
            db.session.add(payment)
        
        # Update cart status
        cart_obj.status = 'completed'
        cart_obj.updated_at = datetime.utcnow()
        
        # Update product stock
        for cart_item in cart_items:
            if cart_item.product:
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'order_id': order.id,
            'reference': reference if HAS_PAYMENT else f"ORDER{order.id}",
            'total': float(total),
            'formatted_total': format_price(total)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error placing order: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/payment/<int:order_id>')
@login_required
def payment_page(order_id):
    """Payment page"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verify order belongs to user
        if order.user_id != session['user_id']:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('index'))
        
        # Get payment info if exists
        payment = None
        if HAS_PAYMENT:
            payment = Payment.query.filter_by(order_id=order_id).first()
        
        return render_template('payment.html',
                             order=order,
                             payment=payment)
        
    except Exception as e:
        print(f"Error in payment_page: {e}")
        flash('Order not found.', 'error')
        return redirect(url_for('user_orders'))

# ============ ORDER MANAGEMENT ============
@app.route('/orders')
@login_required
def user_orders():
    """User order history"""
    try:
        orders = Order.query.filter_by(
            user_id=session['user_id']
        ).order_by(Order.created_at.desc()).all()
        
        return render_template('orders.html', orders=orders)
        
    except Exception as e:
        print(f"Error in user_orders: {e}")
        return render_template('orders.html', orders=[])

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verify order belongs to user
        if order.user_id != session['user_id']:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('index'))
        
        # Get order items if available
        order_items = []
        if HAS_ORDER_ITEM:
            order_items = OrderItem.query.filter_by(order_id=order_id).all()
        
        # Get payment info
        payment = None
        if HAS_PAYMENT:
            payment = Payment.query.filter_by(order_id=order_id).first()
        
        return render_template('order_detail.html',
                             order=order,
                             order_items=order_items,
                             payment=payment)
        
    except Exception as e:
        print(f"Error in order_detail: {e}")
        flash('Order not found.', 'error')
        return redirect(url_for('user_orders'))

# ============ ACCOUNT MANAGEMENT ============
@app.route('/account')
@login_required
def account():
    """User account page"""
    try:
        if not HAS_USER:
            flash('Account functionality not available.', 'error')
            return redirect(url_for('index'))
        
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            flash('User not found.', 'error')
            return redirect(url_for('login'))
        
        # Get order count
        order_count = Order.query.filter_by(user_id=session['user_id']).count()
        
        return render_template('account.html',
                             user=user,
                             order_count=order_count)
        
    except Exception as e:
        print(f"Error in account: {e}")
        flash('Error loading account.', 'error')
        return redirect(url_for('index'))

# ============ ADMIN AUTHENTICATION ============
@app.route('/admin')
@app.route('/admin/login')
def admin_login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

# ============ ADMIN DASHBOARD ============
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard page"""
    try:
        # Get stats
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_users = User.query.count() if HAS_USER else 0
        
        # Calculate total sales
        total_sales_result = db.session.query(
            db.func.sum(Order.total_price)
        ).filter(Order.payment_status == 'completed').first()
        total_sales = total_sales_result[0] or 0
        
        # Recent orders
        recent_orders = Order.query.order_by(
            Order.created_at.desc()
        ).limit(10).all()
        
        # Low stock products
        low_stock = Product.query.filter(
            Product.stock < 10
        ).order_by(Product.stock.asc()).limit(5).all()
        
        # Pending payments
        pending_payments = []
        if HAS_PAYMENT:
            pending_payments = Payment.query.filter_by(
                status='pending'
            ).order_by(Payment.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_users=total_users,
                             total_sales=total_sales,
                             recent_orders=recent_orders,
                             low_stock=low_stock,
                             pending_payments=pending_payments)
        
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        flash('Error loading dashboard.', 'error')
        return render_template('admin/dashboard.html',
                             total_products=0,
                             total_orders=0,
                             total_users=0,
                             total_sales=0,
                             recent_orders=[],
                             low_stock=[],
                             pending_payments=[])

# ============ API ENDPOINTS ============
@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Admin login API"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {'username': username}
            })
        
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products API"""
    try:
        category = request.args.get('category')
        featured = request.args.get('featured', '').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
        query = Product.query
        
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
            'video_url': p.video_url or '',
            'image_urls': json.loads(p.image_urls) if p.image_urls else [],
            'stock': p.stock,
            'featured': p.featured,
            'sku': p.sku,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None
        } for p in products])
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

# ============ STATIC FILE SERVING ============
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory('uploads', filename)

# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Custom 500 page"""
    print(f"Internal error: {e}")
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    """Custom 403 page"""
    return render_template('403.html'), 403

# ============ APPLICATION START ============
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print(f"\n{'='*60}")
    print(f"🚀 NORA HAIR LINE - E-COMMERCE PLATFORM")
    print(f"{'='*60}")
    print(f"🌐 Homepage:          http://localhost:{port}")
    print(f"🛍️  Shop:              http://localhost:{port}/shop")
    print(f"👤 User Login:        http://localhost:{port}/login")
    print(f"👑 Admin Login:       http://localhost:{port}/admin")
    print(f"💰 Payment Account:   {PAYMENT_CONFIG['account_number']}")
    print(f"🏦 Bank:              {PAYMENT_CONFIG['bank_name']}")
    print(f"👤 Account Name:      {PAYMENT_CONFIG['account_name']}")
    print(f"📍 Address:           {WEBSITE_CONFIG['address']}")
    print(f"📞 Contact:           {WEBSITE_CONFIG['phone']}")
    print(f"{'='*60}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') != 'production'
    )
