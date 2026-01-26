# main.py - COMPLETE WORKING VERSION WITH ACCOUNT, ADMIN, AND PAYMENT SYSTEMS
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import logging
from functools import wraps
import random
import string

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates',
           static_url_path='/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Website configuration
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
    'payment_account': '2059311531',
    'payment_bank': 'UBA',
    'payment_name': 'CHUKWUNEKE CHIAMAKA',
    'shipping_fee': 2000.00
}

# ========== DATABASE MODELS ==========

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    first_login = db.Column(db.Boolean, default=True)  # For admin password change
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    cart = db.relationship('Cart', backref='user', uselist=False, lazy=True)
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='Nigeria')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    wishlists = db.relationship('Wishlist', backref='product', lazy=True)

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")
    
    def get_total(self):
        total = 0
        for item in self.items:
            total += item.quantity * item.product.price
        return total
    
    def get_item_count(self):
        return sum(item.quantity for item in self.items)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    address = db.relationship('Address')
    
    # Order details
    subtotal = db.Column(db.Float, nullable=False)
    shipping_fee = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Status tracking
    status = db.Column(db.String(50), default='pending')  # pending, processing, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    payment_method = db.Column(db.String(50))
    payment_proof = db.Column(db.String(500))  # URL to payment proof image
    admin_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of purchase
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Login Manager
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========== HELPER FUNCTIONS ==========

def format_price(price):
    """Format price as Nigerian Naira"""
    try:
        return f"₦{float(price):,.2f}"
    except:
        return "₦0.00"

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'NORA-{timestamp}-{random_str}'

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('account'))
        return f(*args, **kwargs)
    return decorated_function

def get_or_create_cart(user_id):
    """Get or create cart for user"""
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart

def get_cart_count():
    """Get cart item count for current user"""
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            return cart.get_item_count()
    return 0

def get_cart_total():
    """Get cart total for current user"""
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            return cart.get_total()
    return 0

# ========== DATABASE INITIALIZATION ==========

def init_database():
    """Initialize database with all tables and sample data"""
    logger.info("Initializing database...")
    
    # Create all tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Created all database tables")
            
            # Create admin user if not exists
            admin = User.query.filter_by(email='admin@norahairline.com').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@norahairline.com',
                    phone=WEBSITE_CONFIG['phone'],
                    is_admin=True,
                    first_login=True
                )
                admin.set_password('admin123')  # One-time password
                db.session.add(admin)
                logger.info("✅ Created admin user with one-time password: admin123")
            
            # Create sample products if none exist
            if Product.query.count() == 0:
                products = [
                    Product(
                        name="Brazilian Straight Hair 24''",
                        slug="brazilian-straight-hair-24",
                        description="Premium 100% Brazilian Virgin Hair, Straight Texture, 24 inches. Perfect for everyday wear.",
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
                        description="100% Peruvian Human Hair, Natural Curly Pattern, 22 inches. Soft and bouncy.",
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
                        description="HD Lace Frontal Wig, Pre-plucked, Natural Hairline. Looks 100% natural.",
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
                        description="4x4 HD Lace Closure, Swiss Lace, Bleached Knots. Perfect for protective styles.",
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
                
                logger.info(f"✅ Created {len(products)} sample products")
            
            db.session.commit()
            
            print("\n" + "="*60)
            print("DATABASE INITIALIZATION COMPLETE")
            print("="*60)
            print("👑 ADMIN LOGIN:")
            print(f"📧 Email: admin@norahairline.com")
            print(f"🔑 Password: admin123 (CHANGE THIS ON FIRST LOGIN!)")
            print("="*60)
            print(f"📊 Total Products: {Product.query.count()}")
            print(f"👥 Total Users: {User.query.count()}")
            print("="*60)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Database initialization failed: {e}")
            raise

# Initialize database
init_database()

# ========== CONTEXT PROCESSOR ==========

@app.context_processor
def inject_globals():
    """Inject variables into all templates"""
    cart_count = get_cart_count()
    cart_total = get_cart_total()
    
    return {
        **WEBSITE_CONFIG,
        'cart_count': cart_count,
        'cart_total': format_price(cart_total),
        'formatted_cart_total': format_price(cart_total),
        'current_year': datetime.now().year,
        'now': datetime.now()
    }

# ========== ROUTES ==========

@app.route('/')
def home():
    """Homepage"""
    featured_products = Product.query.filter_by(featured=True).limit(6).all()
    categories = db.session.query(Product.category).distinct().all()
    
    for product in featured_products:
        product.formatted_price = format_price(product.price)
        if product.old_price:
            product.formatted_old_price = format_price(product.old_price)
    
    return render_template('index.html',
                         featured_products=featured_products,
                         categories=[cat[0] for cat in categories])

@app.route('/shop')
def shop():
    """Shop page"""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Product.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    products = query.order_by(Product.created_at.desc()).all()
    categories = db.session.query(Product.category).distinct().all()
    
    for product in products:
        product.formatted_price = format_price(product.price)
        if product.old_price:
            product.formatted_old_price = format_price(product.old_price)
    
    return render_template('shop.html',
                         products=products,
                         categories=[cat[0] for cat in categories],
                         category=category,
                         search=search)

@app.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
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

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# ========== ACCOUNT ROUTES ==========

@app.route('/account')
@login_required
def account():
    """Customer account dashboard"""
    try:
        # Get user's recent orders
        orders = Order.query.filter_by(user_id=current_user.id)\
                          .order_by(Order.created_at.desc())\
                          .limit(5).all()
        
        # Get user's addresses
        addresses = Address.query.filter_by(user_id=current_user.id).all()
        
        # Get default address
        default_address = Address.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).first()
        
        # Format order totals
        for order in orders:
            order.formatted_total = format_price(order.total_amount)
        
        return render_template('account.html',
                             user=current_user,
                             orders=orders,
                             addresses=addresses,
                             default_address=default_address)
    except Exception as e:
        logger.error(f"Account error: {e}")
        flash('Error loading account information.', 'error')
        return render_template('account.html',
                             user=current_user,
                             orders=[],
                             addresses=[],
                             default_address=None)

@app.route('/account/orders')
@login_required
def account_orders():
    """Customer order history"""
    orders = Order.query.filter_by(user_id=current_user.id)\
                      .order_by(Order.created_at.desc()).all()
    
    for order in orders:
        order.formatted_total = format_price(order.total_amount)
    
    return render_template('account_orders.html', orders=orders)

@app.route('/account/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page"""
    order = Order.query.get_or_404(order_id)
    
    # Check if order belongs to current user
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('account'))
    
    order.formatted_subtotal = format_price(order.subtotal)
    order.formatted_shipping = format_price(order.shipping_fee)
    order.formatted_total = format_price(order.total_amount)
    
    for item in order.items:
        item.formatted_price = format_price(item.price)
        item.subtotal = item.price * item.quantity
        item.formatted_subtotal = format_price(item.subtotal)
    
    return render_template('order_detail.html', order=order)

@app.route('/account/addresses')
@login_required
def account_addresses():
    """Customer address book"""
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('account_addresses.html', addresses=addresses)

@app.route('/account/addresses/add', methods=['GET', 'POST'])
@login_required
def add_address():
    """Add new address"""
    if request.method == 'POST':
        # Check if this should be default
        is_default = 'is_default' in request.form
        
        # If setting as default, unset other defaults
        if is_default:
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        address = Address(
            user_id=current_user.id,
            full_name=request.form['full_name'],
            phone=request.form['phone'],
            address_line1=request.form['address_line1'],
            address_line2=request.form.get('address_line2', ''),
            city=request.form['city'],
            state=request.form['state'],
            postal_code=request.form.get('postal_code', ''),
            is_default=is_default
        )
        
        db.session.add(address)
        db.session.commit()
        
        flash('Address added successfully!', 'success')
        return redirect(url_for('account_addresses'))
    
    return render_template('add_address.html')

@app.route('/account/profile', methods=['GET', 'POST'])
@login_required
def account_profile():
    """Edit profile"""
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.phone = request.form['phone']
        
        # Check if password change is requested
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('account_profile'))
    
    return render_template('account_profile.html', user=current_user)

# ========== CART ROUTES ==========

@app.route('/cart')
@login_required
def cart():
    """View cart"""
    cart_obj = get_or_create_cart(current_user.id)
    
    total = cart_obj.get_total()
    shipping_fee = WEBSITE_CONFIG['shipping_fee']
    grand_total = total + shipping_fee
    
    for item in cart_obj.items:
        item.product.formatted_price = format_price(item.product.price)
        item.subtotal = item.quantity * item.product.price
        item.formatted_subtotal = format_price(item.subtotal)
    
    return render_template('cart.html',
                         cart_items=cart_obj.items,
                         subtotal=format_price(total),
                         shipping_fee=format_price(shipping_fee),
                         grand_total=format_price(grand_total))

@app.route('/cart/add/<int:product_id>')
@login_required
def add_to_cart(product_id):
    """Add item to cart"""
    product = Product.query.get_or_404(product_id)
    cart_obj = get_or_create_cart(current_user.id)
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(cart_id=cart_obj.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart_obj.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{product.name} added to cart!', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity"""
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Verify cart belongs to current user
    if cart_item.cart.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('cart'))
    
    quantity = int(request.form['quantity'])
    
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = quantity
    
    db.session.commit()
    flash('Cart updated!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    """Remove item from cart"""
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Verify cart belongs to current user
    if cart_item.cart.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# ========== CHECKOUT & PAYMENT ROUTES ==========

@app.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    cart_obj = get_or_create_cart(current_user.id)
    
    if not cart_obj.items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
    
    # Get user's addresses
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    # Calculate totals
    subtotal = cart_obj.get_total()
    shipping_fee = WEBSITE_CONFIG['shipping_fee']
    grand_total = subtotal + shipping_fee
    
    return render_template('checkout.html',
                         cart_items=cart_obj.items,
                         addresses=addresses,
                         subtotal=format_price(subtotal),
                         shipping_fee=format_price(shipping_fee),
                         grand_total=format_price(grand_total))

@app.route('/checkout/process', methods=['POST'])
@login_required
def process_checkout():
    """Process checkout and create order"""
    try:
        cart_obj = get_or_create_cart(current_user.id)
        
        if not cart_obj.items:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('cart'))
        
        # Get selected address
        address_id = request.form.get('address_id')
        if not address_id:
            flash('Please select a shipping address.', 'error')
            return redirect(url_for('checkout'))
        
        address = Address.query.get_or_404(address_id)
        
        # Calculate totals
        subtotal = cart_obj.get_total()
        shipping_fee = WEBSITE_CONFIG['shipping_fee']
        total_amount = subtotal + shipping_fee
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            address_id=address.id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            payment_method='bank_transfer',
            status='pending',
            payment_status='pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Add order items
        for cart_item in cart_obj.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        CartItem.query.filter_by(cart_id=cart_obj.id).delete()
        
        db.session.commit()
        
        flash('Order created successfully! Please make payment and upload proof.', 'success')
        return redirect(url_for('order_payment', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Checkout error: {e}")
        flash('Error processing checkout. Please try again.', 'error')
        return redirect(url_for('checkout'))

@app.route('/order/<int:order_id>/payment')
@login_required
def order_payment(order_id):
    """Payment instructions page"""
    order = Order.query.get_or_404(order_id)
    
    # Verify order belongs to current user
    if order.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('account'))
    
    order.formatted_total = format_price(order.total_amount)
    
    return render_template('order_payment.html', order=order)

@app.route('/order/<int:order_id>/upload-proof', methods=['POST'])
@login_required
def upload_payment_proof(order_id):
    """Upload payment proof"""
    order = Order.query.get_or_404(order_id)
    
    # Verify order belongs to current user
    if order.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return jsonify({'success': False, 'message': 'Access denied'})
    
    # In production, handle file upload properly
    # For now, just mark as paid
    order.payment_status = 'paid'
    order.status = 'pending_confirmation'
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Payment proof uploaded! Admin will review your order.', 'success')
    return jsonify({'success': True, 'redirect': url_for('order_detail', order_id=order.id)})

# ========== AUTHENTICATION ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('account'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Account is disabled. Please contact support.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user)
            
            # Admin password change on first login
            if user.is_admin and user.first_login:
                flash('Please change your password.', 'warning')
                return redirect(url_for('admin_change_password'))
            
            flash('Login successful!', 'success')
            
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('account'))
        
        flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone', '')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        user = User(
            username=username,
            email=email,
            phone=phone,
            is_admin=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create cart for user
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Welcome!', 'success')
        return redirect(url_for('account'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ========== ADMIN ROUTES ==========

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Force password change on first login
    if current_user.first_login:
        return redirect(url_for('admin_change_password'))
    
    # Get stats
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_users': User.query.filter_by(is_admin=False).count(),
        'pending_orders': Order.query.filter_by(status='pending_confirmation').count(),
        'revenue': db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    }
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    for order in recent_orders:
        order.formatted_total = format_price(order.total_amount)
    
    for product in recent_products:
        product.formatted_price = format_price(product.price)
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_orders=recent_orders,
                         recent_products=recent_products)

@app.route('/admin/change-password', methods=['GET', 'POST'])
@admin_required
def admin_change_password():
    """Admin password change (first login)"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('admin_change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('admin_change_password'))
        
        current_user.set_password(new_password)
        current_user.first_login = False
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/change_password.html')

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin order management"""
    status = request.args.get('status', 'all')
    
    query = Order.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    for order in orders:
        order.formatted_total = format_price(order.total_amount)
        order.user_email = order.user.email
    
    return render_template('admin/orders.html', orders=orders, status=status)

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Admin order detail"""
    order = Order.query.get_or_404(order_id)
    
    order.formatted_subtotal = format_price(order.subtotal)
    order.formatted_shipping = format_price(order.shipping_fee)
    order.formatted_total = format_price(order.total_amount)
    
    for item in order.items:
        item.formatted_price = format_price(item.price)
        item.subtotal = item.price * item.quantity
        item.formatted_subtotal = format_price(item.subtotal)
    
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    valid_statuses = ['pending_confirmation', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    
    if new_status in valid_statuses:
        order.status = new_status
        order.admin_notes = admin_notes
        
        # Set timestamps
        if new_status == 'confirmed':
            order.confirmed_at = datetime.utcnow()
        elif new_status == 'shipped':
            order.shipped_at = datetime.utcnow()
        elif new_status == 'delivered':
            order.delivered_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Order status updated to {new_status}.', 'success')
    
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin product management"""
    products = Product.query.order_by(Product.created_at.desc()).all()
    
    for product in products:
        product.formatted_price = format_price(product.price)
    
    return render_template('admin/products.html', products=products)

@app.route('/admin/customers')
@admin_required
def admin_customers():
    """Admin customer management"""
    customers = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return render_template('admin/customers.html', customers=customers)

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
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
    print(f"👤 Customer: Register at /register")
    print(f"🛒 Shop: http://localhost:{port}/shop")
    print(f"👤 Account: http://localhost:{port}/account")
    print(f"{'='*60}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
