from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json
import uuid
from werkzeug.utils import secure_filename

# Import models
try:
    from models import db, Admin, Product, Order, Review, User, Cart, CartItem, Payment
    print("✓ All models imported successfully")
    HAS_REVIEW = True
    HAS_USER = True
    HAS_CART = True
    HAS_PAYMENT = True
except ImportError as e:
    print(f"Import error: {e}")
    from models import db, Admin, Product, Order
    Review = None
    User = None
    Cart = None
    CartItem = None
    Payment = None
    HAS_REVIEW = False
    HAS_USER = False
    HAS_CART = False
    HAS_PAYMENT = False
    print("✓ Imported basic models only")

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# ============ DATABASE CONFIGURATION ============
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✓ Using PostgreSQL database")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'
    print("✓ Using SQLite database")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
app.config['SESSION_TYPE'] = 'filesystem'

# ============ PAYMENT CONFIGURATION ============
PAYMENT_CONFIG = {
    'account_number': '2059311531',
    'bank_name': 'UBA',
    'account_name': 'CHUKWUNEKE CHIAMAKA',
    'currency': 'NGN',
    'currency_symbol': '₦'
}

# ============ FILE UPLOAD CONFIGURATION ============
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')

# Create upload directories if they don't exist
for folder in [UPLOAD_FOLDER, IMAGE_FOLDER, VIDEO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

# Initialize database
db.init_app(app)

# ============ CREATE DEFAULT DIRECTORIES ============
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'static',
        'static/images',
        'static/css',
        'static/js',
        'static/uploads',
        'templates',
        'templates/admin',
        'uploads',
        'uploads/images',
        'uploads/videos'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}/")

# ============ DATABASE SETUP ============
with app.app_context():
    try:
        # Ensure all directories exist
        ensure_directories()
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # ===== CREATE DEFAULT ADMIN =====
        admin_count = Admin.query.count()
        if admin_count == 0:
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@norahairline.com',
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            print(f"👑 Created default admin: username='admin', password='admin123'")
        else:
            print(f"👑 Admin already exists: {admin_count} admin(s) found")
        
        # ===== CREATE SAMPLE PRODUCTS =====
        product_count = Product.query.count()
        if product_count == 0:
            # Prices in Naira
            products = [
                Product(
                    name="Premium Bone Straight Hair 24\"",
                    description="24-inch premium quality 100% human hair, bone straight texture. Perfect for everyday wear. Easy to install and maintain.",
                    price=134985.0,  # Naira
                    category="hair",
                    image_url="/static/images/hair1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/hair1.jpg"]),
                    stock=50,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Curly Brazilian Hair 22\"",
                    description="22-inch natural Brazilian curly hair, soft and bouncy. Perfect for Afro-centric styles.",
                    price=149985.0,  # Naira
                    category="hair",
                    image_url="/static/images/hair2.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/hair2.jpg"]),
                    stock=30,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Lace Front Wig - Natural Black",
                    description="13x4 lace front wig, natural black color, pre-plucked hairline. Looks 100% natural.",
                    price=194985.0,  # Naira
                    category="wigs",
                    image_url="/static/images/wig1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/wig1.jpg"]),
                    stock=20,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Hair Growth Oil 8oz",
                    description="Organic hair growth oil with rosemary and castor oil. Promotes hair growth and thickness.",
                    price=37485.0,  # Naira
                    category="care",
                    image_url="/static/images/oil1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/oil1.jpg"]),
                    stock=100,
                    featured=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Moisturizing Shampoo 16oz",
                    description="Sulfate-free moisturizing shampoo for all hair types. Gentle on hair and scalp.",
                    price=28485.0,  # Naira
                    category="care",
                    image_url="/static/images/shampoo1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/shampoo1.jpg"]),
                    stock=80,
                    featured=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Silk Press Hair 26\"",
                    description="26-inch silk press hair, ultra smooth and shiny. Professional quality for salons.",
                    price=179985.0,  # Naira
                    category="hair",
                    image_url="/static/images/hair3.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/hair3.jpg"]),
                    stock=15,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="360 Lace Frontal Wig",
                    description="360 lace frontal wig with baby hairs. Full coverage for versatile styling.",
                    price=249985.0,  # Naira
                    category="wigs",
                    image_url="/static/images/wig2.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/wig2.jpg"]),
                    stock=25,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Deep Conditioner 12oz",
                    description="Deep conditioning treatment for dry and damaged hair. Restores moisture and shine.",
                    price=22485.0,  # Naira
                    category="care",
                    image_url="/static/images/conditioner1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/conditioner1.jpg"]),
                    stock=60,
                    featured=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            # Add products to session
            for product in products:
                db.session.add(product)
            
            print(f"🛍️  Created {len(products)} sample products")
        
        else:
            print(f"🛍️  Products already exist: {product_count} product(s) found")
        
        # ===== CREATE SAMPLE REVIEWS =====
        if HAS_REVIEW and Review:
            review_count = Review.query.count()
            if review_count == 0:
                sample_reviews = [
                    Review(
                        product_id=1,
                        customer_name="Chinwe Okafor",
                        customer_email="chinwe@example.com",
                        rating=5,
                        comment="Excellent quality hair! Looks and feels natural. Will definitely order again.",
                        approved=True,
                        created_at=datetime.utcnow()
                    ),
                    Review(
                        product_id=2,
                        customer_name="Amina Bello",
                        customer_email="amina@example.com",
                        rating=4,
                        comment="Love the curls! So soft and easy to maintain. Perfect for Nigerian weather.",
                        approved=True,
                        created_at=datetime.utcnow()
                    ),
                    Review(
                        product_id=3,
                        customer_name="Ngozi Eze",
                        customer_email="ngozi@example.com",
                        rating=5,
                        comment="Best lace front wig I've ever owned! The hairline is so natural.",
                        approved=True,
                        created_at=datetime.utcnow()
                    )
                ]
                
                for review in sample_reviews:
                    db.session.add(review)
                
                print(f"🌟 Created {len(sample_reviews)} sample reviews")
            else:
                print(f"🌟 Reviews already exist: {review_count} review(s) found")
        
        # Commit all changes
        db.session.commit()
        print("✅ Database setup completed successfully")
        
    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")
        # Rollback in case of error
        db.session.rollback()
        import traceback
        traceback.print_exc()

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
    'year': datetime.now().year,
    'payment_config': PAYMENT_CONFIG
}

# ============ HELPER FUNCTIONS ============
def format_price(price):
    """Format price as Nigerian Naira"""
    return f"₦{float(price):,.2f}"

def get_cart_count():
    """Get cart item count for current user"""
    if HAS_CART and Cart and CartItem:
        if session.get('user_id'):
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if cart:
                return CartItem.query.filter_by(cart_id=cart.id).count()
    return 0

# ============ WEBSITE PAGES ============

@app.route('/')
def index():
    """Main store homepage with modern design"""
    try:
        # Get featured products
        featured_products = Product.query.filter_by(featured=True).order_by(Product.created_at.desc()).limit(8).all()
        
        # Format product prices
        for product in featured_products:
            product.formatted_price = format_price(product.price)
        
        # Get approved reviews
        if HAS_REVIEW and Review:
            approved_reviews = Review.query.filter_by(approved=True).order_by(Review.created_at.desc()).limit(6).all()
        else:
            approved_reviews = []
        
        # Get product categories count
        categories = {
            'hair': Product.query.filter_by(category='hair').count(),
            'wigs': Product.query.filter_by(category='wigs').count(),
            'care': Product.query.filter_by(category='care').count()
        }
        
        # Calculate total products
        total_products = Product.query.count()
        
        # Get cart count
        cart_count = get_cart_count()
        
        return render_template('index.html', 
                             featured_products=featured_products,
                             reviews=approved_reviews,
                             categories=categories,
                             total_products=total_products,
                             cart_count=cart_count,
                             **WEBSITE_CONFIG)
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html', 
                             featured_products=[],
                             reviews=[],
                             categories={'hair': 0, 'wigs': 0, 'care': 0},
                             total_products=0,
                             cart_count=0,
                             **WEBSITE_CONFIG)

@app.route('/shop')
@app.route('/products')
def products_page():
    """Products shopping page"""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    try:
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        products = query.order_by(Product.created_at.desc()).all()
        
        # Format prices
        for product in products:
            product.formatted_price = format_price(product.price)
        
        cart_count = get_cart_count()
        
        return render_template('products.html', 
                             products=products,
                             category=category,
                             search=search,
                             cart_count=cart_count,
                             **WEBSITE_CONFIG)
    except Exception as e:
        print(f"Error in products_page: {e}")
        return render_template('products.html', 
                             products=[],
                             category=category,
                             search=search,
                             cart_count=0,
                             **WEBSITE_CONFIG)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
        product = Product.query.get_or_404(product_id)
        product.formatted_price = format_price(product.price)
        
        # Get related products
        related_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product.id
        ).limit(4).all()
        
        for p in related_products:
            p.formatted_price = format_price(p.price)
        
        # Get product reviews
        if HAS_REVIEW and Review:
            reviews = Review.query.filter_by(product_id=product_id, approved=True).all()
        else:
            reviews = []
        
        cart_count = get_cart_count()
        
        return render_template('product_detail.html', 
                             product=product,
                             related_products=related_products,
                             reviews=reviews,
                             cart_count=cart_count,
                             **WEBSITE_CONFIG)
    except Exception as e:
        print(f"Error in product_detail: {e}")
        return redirect(url_for('products_page'))

# ============ USER AUTHENTICATION ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if HAS_USER and User:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_email'] = user.email
                session['user_name'] = user.name
                return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid credentials', **WEBSITE_CONFIG)
    
    cart_count = get_cart_count()
    return render_template('login.html', cart_count=cart_count, **WEBSITE_CONFIG)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match', **WEBSITE_CONFIG)
        
        if HAS_USER and User:
            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('register.html', error='Email already registered', **WEBSITE_CONFIG)
            
            # Create new user
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
            
            return redirect(url_for('index'))
    
    cart_count = get_cart_count()
    return render_template('register.html', cart_count=cart_count, **WEBSITE_CONFIG)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

# ============ CART FUNCTIONALITY ============

@app.route('/cart')
def cart():
    """Shopping cart page"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        if HAS_CART and Cart and CartItem:
            # Get or create cart
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if not cart:
                cart = Cart(user_id=session['user_id'], status='active')
                db.session.add(cart)
                db.session.commit()
            
            # Get cart items
            cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
            
            # Calculate totals
            subtotal = 0
            for item in cart_items:
                if item.product:
                    item.total = item.quantity * item.product.price
                    subtotal += item.total
                    item.formatted_total = format_price(item.total)
                    item.product.formatted_price = format_price(item.product.price)
            
            shipping = 2000 if subtotal > 0 else 0  # NGN 2000 shipping
            total = subtotal + shipping
            
            cart_count = len(cart_items)
            
            return render_template('cart.html',
                                 cart_items=cart_items,
                                 subtotal=subtotal,
                                 shipping=shipping,
                                 total=total,
                                 formatted_subtotal=format_price(subtotal),
                                 formatted_shipping=format_price(shipping),
                                 formatted_total=format_price(total),
                                 cart_count=cart_count,
                                 **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in cart: {e}")
    
    return render_template('cart.html', cart_items=[], cart_count=0, **WEBSITE_CONFIG)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        quantity = int(request.form.get('quantity', 1))
        
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check stock
        if product.stock < quantity:
            return jsonify({'success': False, 'message': f'Only {product.stock} items in stock'}), 400
        
        if HAS_CART and Cart and CartItem:
            # Get or create cart
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if not cart:
                cart = Cart(user_id=session['user_id'], status='active')
                db.session.add(cart)
                db.session.commit()
            
            # Check if item already in cart
            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
            
            # Update product stock
            product.stock -= quantity
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Product added to cart',
                'cart_count': CartItem.query.filter_by(cart_id=cart.id).count()
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Cart functionality not available'}), 500

@app.route('/update-cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    """Update cart item quantity"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        quantity = int(request.form.get('quantity', 1))
        
        if HAS_CART and CartItem:
            cart_item = CartItem.query.get_or_404(item_id)
            
            # Verify cart belongs to user
            cart = Cart.query.get(cart_item.cart_id)
            if cart.user_id != session['user_id']:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Get product
            product = Product.query.get(cart_item.product_id)
            
            # Calculate stock difference
            stock_diff = quantity - cart_item.quantity
            
            if product.stock < stock_diff:
                return jsonify({'success': False, 'message': f'Only {product.stock + cart_item.quantity} items in stock'}), 400
            
            # Update quantities
            cart_item.quantity = quantity
            product.stock -= stock_diff
            
            db.session.commit()
            
            # Calculate new totals
            item_total = cart_item.quantity * product.price
            
            return jsonify({
                'success': True,
                'message': 'Cart updated',
                'item_total': float(item_total),
                'formatted_item_total': format_price(item_total)
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Cart functionality not available'}), 500

@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    """Remove item from cart"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        if HAS_CART and CartItem:
            cart_item = CartItem.query.get_or_404(item_id)
            
            # Verify cart belongs to user
            cart = Cart.query.get(cart_item.cart_id)
            if cart.user_id != session['user_id']:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Restore product stock
            product = Product.query.get(cart_item.product_id)
            product.stock += cart_item.quantity
            
            # Remove item
            db.session.delete(cart_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Item removed from cart'
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Cart functionality not available'}), 500

# ============ CHECKOUT & PAYMENT ============

@app.route('/checkout')
def checkout():
    """Checkout page"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        if HAS_CART and Cart and CartItem:
            # Get cart
            cart = Cart.query.filter_by(user_id=session['user_id'], status='active').first()
            if not cart:
                return redirect(url_for('cart'))
            
            # Get cart items
            cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
            if not cart_items:
                return redirect(url_for('cart'))
            
            # Calculate totals
            subtotal = sum(item.quantity * item.product.price for item in cart_items if item.product)
            shipping = 2000 if subtotal > 0 else 0
            total = subtotal + shipping
            
            cart_count = len(cart_items)
            
            return render_template('checkout.html',
                                 subtotal=subtotal,
                                 shipping=shipping,
                                 total=total,
                                 formatted_subtotal=format_price(subtotal),
                                 formatted_shipping=format_price(shipping),
                                 formatted_total=format_price(total),
                                 cart_count=cart_count,
                                 **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in checkout: {e}")
    
    return redirect(url_for('cart'))

@app.route('/place-order', methods=['POST'])
def place_order():
    """Place order and create payment"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        
        # Get user info
        user_id = session['user_id']
        
        # Get cart
        cart = Cart.query.filter_by(user_id=user_id, status='active').first()
        if not cart:
            return jsonify({'success': False, 'message': 'Cart not found'}), 400
        
        # Get cart items
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Calculate total
        total = sum(item.quantity * item.product.price for item in cart_items if item.product)
        shipping = 2000
        total_with_shipping = total + shipping
        
        # Create order
        order = Order(
            user_id=user_id,
            customer_name=data.get('name', session.get('user_name', '')),
            customer_email=data.get('email', session.get('user_email', '')),
            customer_phone=data.get('phone', ''),
            customer_address=data.get('address', ''),
            customer_city=data.get('city', ''),
            customer_state=data.get('state', ''),
            total_price=total_with_shipping,
            shipping_fee=shipping,
            status='pending',
            payment_status='pending',
            notes=data.get('notes', ''),
            created_at=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            if cart_item.product:
                # Create order item record (you would need an OrderItem model)
                # For now, we'll store product info in order notes
                pass
        
        # Create payment record
        if HAS_PAYMENT and Payment:
            payment = Payment(
                order_id=order.id,
                amount=total_with_shipping,
                payment_method='bank_transfer',
                status='pending',
                reference=f"NHL{datetime.now().strftime('%Y%m%d')}{order.id:04d}",
                created_at=datetime.utcnow()
            )
            db.session.add(payment)
        
        # Update cart status
        cart.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'order_id': order.id,
            'reference': payment.reference if HAS_PAYMENT and Payment else f"ORDER{order.id}",
            'total': float(total_with_shipping),
            'formatted_total': format_price(total_with_shipping)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/payment/<int:order_id>')
def payment_page(order_id):
    """Payment page"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verify order belongs to user
        if order.user_id != session['user_id']:
            return redirect(url_for('index'))
        
        # Get payment info if exists
        payment = None
        if HAS_PAYMENT and Payment:
            payment = Payment.query.filter_by(order_id=order_id).first()
        
        order.formatted_total = format_price(order.total_price)
        
        cart_count = get_cart_count()
        
        return render_template('payment.html',
                             order=order,
                             payment=payment,
                             cart_count=cart_count,
                             **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in payment_page: {e}")
        return redirect(url_for('index'))

@app.route('/confirm-payment/<int:order_id>', methods=['POST'])
def confirm_payment(order_id):
    """User confirms they've made payment"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        
        order = Order.query.get_or_404(order_id)
        
        # Verify order belongs to user
        if order.user_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Update payment status
        if HAS_PAYMENT and Payment:
            payment = Payment.query.filter_by(order_id=order_id).first()
            if payment:
                payment.status = 'processing'
                payment.payment_proof = data.get('proof_details', '')
                payment.updated_at = datetime.utcnow()
        
        order.payment_status = 'processing'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment confirmation received. Admin will verify your payment.',
            'order_id': order.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ ORDER TRACKING ============

@app.route('/orders')
def user_orders():
    """User order history"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
        
        for order in orders:
            order.formatted_total = format_price(order.total_price)
            if order.created_at:
                order.formatted_date = order.created_at.strftime('%b %d, %Y')
        
        cart_count = get_cart_count()
        
        return render_template('orders.html',
                             orders=orders,
                             cart_count=cart_count,
                             **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in user_orders: {e}")
        return render_template('orders.html', orders=[], cart_count=0, **WEBSITE_CONFIG)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    """Order detail page"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verify order belongs to user
        if order.user_id != session['user_id']:
            return redirect(url_for('index'))
        
        order.formatted_total = format_price(order.total_price)
        order.formatted_date = order.created_at.strftime('%B %d, %Y %I:%M %p') if order.created_at else ''
        
        # Get payment info
        payment = None
        if HAS_PAYMENT and Payment:
            payment = Payment.query.filter_by(order_id=order_id).first()
        
        cart_count = get_cart_count()
        
        return render_template('order_detail.html',
                             order=order,
                             payment=payment,
                             cart_count=cart_count,
                             **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in order_detail: {e}")
        return redirect(url_for('user_orders'))

# ============ ACCOUNT MANAGEMENT ============

@app.route('/account')
def account():
    """User account page"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        if HAS_USER and User:
            user = User.query.get(session['user_id'])
            
            # Get order count
            order_count = Order.query.filter_by(user_id=session['user_id']).count()
            
            cart_count = get_cart_count()
            
            return render_template('account.html',
                                 user=user,
                                 order_count=order_count,
                                 cart_count=cart_count,
                                 **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in account: {e}")
    
    return render_template('account.html', cart_count=0, **WEBSITE_CONFIG)

# ============ ADMIN PAGES ============

@app.route('/admin')
def admin():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/admin_login.html', **WEBSITE_CONFIG)

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    try:
        # Get stats
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_users = User.query.count() if HAS_USER and User else 0
        
        total_sales = db.session.query(db.func.sum(Order.total_price)).scalar() or 0
        
        # Recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        for order in recent_orders:
            order.formatted_total = format_price(order.total_price)
            order.formatted_date = order.created_at.strftime('%b %d') if order.created_at else ''
        
        # Low stock products
        low_stock = Product.query.filter(Product.stock < 10).limit(5).all()
        
        # Pending payments
        pending_payments = []
        if HAS_PAYMENT and Payment:
            pending_payments = Payment.query.filter_by(status='processing').limit(5).all()
        
        return render_template('admin/admin_dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_users=total_users,
                             total_sales=total_sales,
                             formatted_total_sales=format_price(total_sales),
                             recent_orders=recent_orders,
                             low_stock=low_stock,
                             pending_payments=pending_payments,
                             **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        return render_template('admin/admin_dashboard.html', **WEBSITE_CONFIG)

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    try:
        # Get category filter
        category = request.args.get('category', '')
        
        # Build query
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        # Get products
        products = query.order_by(Product.created_at.desc()).all()
        
        # Get categories for filter dropdown
        categories = db.session.query(Product.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        # Format prices in Naira
        for product in products:
            product.formatted_price = format_price(product.price)
        
        # Pass data to template
        return render_template('admin/products.html', 
                             products=products,
                             categories=categories,
                             selected_category=category,
                             **WEBSITE_CONFIG)
    except Exception as e:
        print(f"Error in admin_products: {e}")
        # Return empty page if error
        return render_template('admin/products.html', 
                             products=[],
                             categories=[],
                             selected_category='',
                             **WEBSITE_CONFIG)

@app.route('/admin/orders')
def admin_orders():
    """Admin orders management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    try:
        # Get status filter
        status = request.args.get('status', '')
        
        # Build query
        query = Order.query
        
        if status:
            query = query.filter_by(status=status)
        
        # Get orders
        orders = query.order_by(Order.created_at.desc()).all()
        
        # Format total prices in Naira
        for order in orders:
            order.formatted_total_price = format_price(order.total_price)
            order.formatted_date = order.created_at.strftime('%b %d, %Y') if order.created_at else ''
            
        return render_template('admin/order.html', 
                             orders=orders,
                             selected_status=status,
                             **WEBSITE_CONFIG)
    except Exception as e:
        print(f"Error in admin_orders: {e}")
        return render_template('admin/order.html', 
                             orders=[],
                             selected_status='',
                             **WEBSITE_CONFIG)

@app.route('/admin/payments')
def admin_payments():
    """Admin payments management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    try:
        if HAS_PAYMENT and Payment:
            # Get status filter
            status = request.args.get('status', '')
            
            # Build query
            query = Payment.query.join(Order).add_entity(Order)
            
            if status:
                query = query.filter(Payment.status == status)
            
            # Get payments with orders
            payments_data = query.order_by(Payment.created_at.desc()).all()
            
            payments = []
            for payment, order in payments_data:
                payment.order = order
                payment.formatted_amount = format_price(payment.amount)
                payment.formatted_date = payment.created_at.strftime('%b %d, %Y') if payment.created_at else ''
                payments.append(payment)
            
            return render_template('admin/payments.html',
                                 payments=payments,
                                 selected_status=status,
                                 **WEBSITE_CONFIG)
        
        return render_template('admin/payments.html',
                             payments=[],
                             selected_status='',
                             **WEBSITE_CONFIG)
    
    except Exception as e:
        print(f"Error in admin_payments: {e}")
        return render_template('admin/payments.html',
                             payments=[],
                             selected_status='',
                             **WEBSITE_CONFIG)

@app.route('/admin/confirm-payment/<int:payment_id>', methods=['POST'])
def admin_confirm_payment(payment_id):
    """Admin confirms payment"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if HAS_PAYMENT and Payment:
            payment = Payment.query.get_or_404(payment_id)
            order = Order.query.get(payment.order_id)
            
            # Update payment status
            payment.status = 'completed'
            payment.updated_at = datetime.utcnow()
            
            # Update order status
            order.payment_status = 'completed'
            order.status = 'processing'  # Move to processing/shipping
            order.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment confirmed successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Payment functionality not available'}), 500

@app.route('/admin/update-order-status/<int:order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    """Admin updates order status"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required', 'success': False}), 400
        
        order = Order.query.get_or_404(order_id)
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'order_id': order.id,
            'status': new_status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

# ============ STATIC FILE SERVING ============

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory('static', filename)
    except:
        return "File not found", 404

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    try:
        return send_from_directory('uploads', filename)
    except:
        return "File not found", 404

# ============ API ENDPOINTS ============

@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products with optional category filter"""
    try:
        category = request.args.get('category')
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        featured_only = request.args.get('featured', '').lower() == 'true'
        if featured_only:
            query = query.filter_by(featured=True)
            
        # Sort by newest first
        query = query.order_by(Product.created_at.desc())
        
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
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None
        } for p in products])
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

# ============ ADMIN API ============

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Admin login"""
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
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {'username': username}
            })
        
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': 'Logged out'})

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    cart_count = get_cart_count()
    return render_template('404.html', cart_count=cart_count, **WEBSITE_CONFIG), 404

@app.errorhandler(500)
def internal_error(e):
    """Custom 500 page"""
    cart_count = get_cart_count()
    return render_template('500.html', cart_count=cart_count, **WEBSITE_CONFIG), 500

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Ensure directories exist
    ensure_directories()
    
    print(f"\n{'='*60}")
    print(f"🚀 NORA HAIR LINE - COMPLETE E-COMMERCE")
    print(f"{'='*60}")
    print(f"🌐 Homepage:          http://localhost:{port}")
    print(f"🛍️  Shop:              http://localhost:{port}/shop")
    print(f"💰 Payment Account:   {PAYMENT_CONFIG['account_number']}")
    print(f"🏦 Bank:              {PAYMENT_CONFIG['bank_name']}")
    print(f"👤 Account Name:      {PAYMENT_CONFIG['account_name']}")
    print(f"👑 Admin Login:       http://localhost:{port}/admin")
    print(f"📊 Admin Dashboard:   http://localhost:{port}/admin/dashboard")
    print(f"💰 Currency:          {PAYMENT_CONFIG['currency']} ({PAYMENT_CONFIG['currency_symbol']})")
    print(f"📍 Address:           {WEBSITE_CONFIG['address']}")
    print(f"📞 Contact:           {WEBSITE_CONFIG['phone']}")
    print(f"{'='*60}")
    
    app.run(host='0.0.0.0', port=port, debug=True)
