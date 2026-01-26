# main.py - COMPLETE FIXED VERSION WITH ALL FEATURES
import os
import sys
import traceback
from datetime import datetime, timedelta
import random
import string
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ========== CREATE APP ==========
app = Flask(__name__)

# ========== CONFIGURATION ==========
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026-change-in-production')

# Database configuration for Render
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SITE_LOGO'] = 'logo.png'

# ========== INITIALIZE EXTENSIONS ==========
db = SQLAlchemy(app)

# ========== DATABASE MODELS ==========
class User(db.Model):
    __tablename__ = 'admin_user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500), default='default-category.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    compare_price = db.Column(db.Float)
    sku = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    image_url = db.Column(db.String(500), default='default-product.jpg')
    length = db.Column(db.String(50))
    texture = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('Category', backref='products')
    
    @property
    def display_price(self):
        return float(self.price)
    
    @property
    def formatted_price(self):
        return f"₦{self.display_price:,.2f}"
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Customer(db.Model):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Customer {self.email}>'

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50), default='bank_transfer')
    payment_status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')

class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    location = db.Column(db.String(100))
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    
    def __repr__(self):
        return f'<Review {self.id}>'

# ========== BUSINESS CONFIGURATION ==========
BUSINESS_CONFIG = {
    'brand_name': 'NORA HAIR LINE',
    'tagline': 'Premium 100% Human Hair',
    'slogan': 'Luxury for less...',
    'description': 'Premium 100% human hair extensions, wigs, and hair products at wholesale prices.',
    'address': 'No 5 Veet Gold Plaza, opposite Abia gate @ Tradefair Shopping Center, Badagry Express Way, Lagos State.',
    'phone': '08038707795',
    'whatsapp': 'https://wa.me/2348038707795',
    'instagram': 'norahairline',
    'instagram_url': 'https://instagram.com/norahairline',
    'email': 'info@norahairline.com',
    'support_email': 'support@norahairline.com',
    'currency': 'NGN',
    'currency_symbol': '₦',
    'payment_account': '2059311531',
    'payment_bank': 'UBA',
    'payment_name': 'CHUKWUNEKE CHIAMAKA',
    'year': datetime.now().year,
    'site_logo': 'logo.png'
}

# ========== DELIVERY CALCULATOR ==========
class DeliveryCalculator:
    FREE_DELIVERY_THRESHOLD = 150000.00
    LAGOS_DELIVERY = 3000.00
    OUTSIDE_LAGOS_DELIVERY = 5000.00
    
    LAGOS_AREAS = [
        'Ikeja', 'Victoria Island', 'Lekki', 'Ikoyi', 'Surulere', 
        'Yaba', 'Lagos Island', 'Ajah', 'Apapa', 'Festac',
        'Gbagada', 'Maryland', 'Magodo', 'Anthony', 'Ojota',
        'Lagos', 'VI', 'IK', 'Aj'
    ]
    
    @staticmethod
    def calculate_delivery_fee(cart_total, delivery_city=""):
        if cart_total >= DeliveryCalculator.FREE_DELIVERY_THRESHOLD:
            return 0.0
        
        if not delivery_city:
            return DeliveryCalculator.LAGOS_DELIVERY
        
        delivery_city = delivery_city.lower()
        is_lagos = any(area.lower() in delivery_city for area in DeliveryCalculator.LAGOS_AREAS)
        
        return DeliveryCalculator.LAGOS_DELIVERY if is_lagos else DeliveryCalculator.OUTSIDE_LAGOS_DELIVERY
    
    @staticmethod
    def get_delivery_message(cart_total, delivery_city=""):
        fee = DeliveryCalculator.calculate_delivery_fee(cart_total, delivery_city)
        
        if fee == 0:
            return "🎉 FREE DELIVERY!"
        
        remaining = DeliveryCalculator.FREE_DELIVERY_THRESHOLD - cart_total
        if remaining > 0:
            return f"Delivery: ₦{fee:,.2f} | Add ₦{remaining:,.2f} more for FREE delivery!"
        
        return f"Delivery Fee: ₦{fee:,.2f}"

# ========== DATABASE INITIALIZATION ==========
def init_db():
    """Initialize database with tables and sample data"""
    print("🔄 Initializing database...", file=sys.stderr)
    
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created", file=sys.stderr)
            
            # Create admin user if not exists
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    email='admin@norahairline.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                print("✅ Admin user created: admin/admin123", file=sys.stderr)
            
            # Create default categories if none exist
            if Category.query.count() == 0:
                categories = [
                    ('Lace Wigs', 'lace-wigs', 'Natural looking lace front wigs with HD lace'),
                    ('Hair Bundles', 'hair-bundles', 'Premium 100% human hair bundles in various textures'),
                    ('Closures', 'closures', 'Hair closures for protective styling'),
                    ('Frontals', 'frontals', '13x4 and 13x6 lace frontals'),
                    ('360 Wigs', '360-wigs', '360 lace wigs for full perimeter styling'),
                    ('Hair Care', 'hair-care', 'Products for hair maintenance and growth'),
                ]
                
                for name, slug, desc in categories:
                    category = Category(name=name, slug=slug, description=desc)
                    db.session.add(category)
                
                print("✅ Sample categories added", file=sys.stderr)
            
            # Create sample products if none exist
            if Product.query.count() == 0:
                categories = Category.query.all()
                
                sample_products = [
                    ('Brazilian Body Wave 24"', 12999.99, 15999.99, 50, 'hair-bundles', 
                     'Premium Brazilian body wave hair, 24 inches, 100% human hair', 'brazilian-wave.jpg', 'body wave'),
                    ('Peruvian Straight 22"', 14999.99, 17999.99, 30, 'hair-bundles',
                     'Silky straight Peruvian hair, 22 inches, natural black', 'peruvian-straight.jpg', 'straight'),
                    ('13x4 Lace Frontal Wig', 19999.99, 23999.99, 20, 'lace-wigs',
                     'HD lace frontal wig with natural hairline', 'lace-wig.jpg', 'straight'),
                    ('4x4 Lace Closure', 8999.99, 11999.99, 40, 'closures',
                     '4x4 HD lace closure with bleached knots', 'closure.jpg', 'straight'),
                    ('13x6 Lace Frontal', 15999.99, 19999.99, 25, 'frontals',
                     '13x6 lace frontal for natural look', 'frontal.jpg', 'curly'),
                    ('Hair Growth Oil', 2999.99, 3999.99, 100, 'hair-care',
                     'Essential oils for hair growth and thickness', 'hair-oil.jpg', None),
                    ('360 Lace Frontal Wig', 22999.99, 27999.99, 10, '360-wigs',
                     '360 lace wig for full perimeter styling', '360-wig.jpg', 'wavy'),
                    ('Malaysian Straight 26"', 16999.99, 20999.99, 15, 'hair-bundles',
                     'Premium Malaysian straight hair, 26 inches', 'malaysian-straight.jpg', 'straight'),
                ]
                
                for i, (name, price, compare_price, quantity, category_slug, desc, image, texture) in enumerate(sample_products):
                    category = Category.query.filter_by(slug=category_slug).first()
                    if category:
                        product = Product(
                            name=name,
                            slug=name.lower().replace(' ', '-').replace('"', ''),
                            description=desc,
                            price=price,
                            compare_price=compare_price,
                            quantity=quantity,
                            sku=f'HAIR-{i+1:03d}',
                            category_id=category.id,
                            featured=(i < 6),
                            texture=texture,
                            image_url=image
                        )
                        db.session.add(product)
                
                print("✅ Sample products added", file=sys.stderr)
            
            # Create sample reviews if none exist
            if Review.query.count() == 0:
                reviews = [
                    (1, 'Chiamaka Okeke', 5, 'The Brazilian hair I purchased is absolutely stunning! It\'s been 6 months and still looks brand new. Best quality I\'ve ever had!', 'Lagos'),
                    (2, 'Bisi Adeyemi', 5, 'The lace frontal wig is so natural looking! I\'ve received countless compliments. The customer service was excellent too!', 'Abuja'),
                    (3, 'Fatima Bello', 4, 'Fast delivery and premium quality hair. I\'ll definitely be ordering again. The Peruvian straight is my new favorite!', 'Port Harcourt'),
                    (4, 'Amaka Nwosu', 5, 'The closure is perfect! So natural and easy to install. Will definitely buy from Nora Hair Line again.', 'Enugu'),
                    (5, 'Jennifer Musa', 5, 'Hair growth oil works wonders! My edges are growing back after just 2 months of use.', 'Kano'),
                ]
                
                for product_id, name, rating, comment, location in reviews:
                    review = Review(
                        product_id=product_id,
                        customer_name=name,
                        rating=rating,
                        comment=comment,
                        location=location,
                        approved=True
                    )
                    db.session.add(review)
                
                print("✅ Sample reviews added", file=sys.stderr)
            
            db.session.commit()
            print("✅ Database initialization complete", file=sys.stderr)
            return True
    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

# ========== INITIALIZE DATABASE ==========
init_db()

# ========== HELPER FUNCTIONS ==========
def format_price(value):
    """Safely format price value"""
    try:
        if value is None:
            return "₦0.00"
        if isinstance(value, str):
            value = float(value)
        return f"₦{value:,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"

def generate_order_number():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'NORA-{timestamp}-{random_str}'

def calculate_cart_total():
    total = 0
    if 'cart' in session:
        for item in session['cart']:
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            total += float(price) * quantity
    return total

# ========== AUTHENTICATION DECORATORS ==========
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'customer_id' not in session:
            flash('Please login to access this page', 'warning')
            session['pending_checkout'] = True
            return redirect(url_for('customer_login'))
        return f(*args, **kwargs)
    return decorated_function

# ========== CONTEXT PROCESSOR ==========
@app.context_processor
def inject_global_vars():
    """Make variables available to all templates"""
    categories = []
    cart_count = 0
    cart_total = 0
    
    try:
        categories = Category.query.all()
    except Exception as e:
        print(f"❌ Context processor error (categories): {str(e)}", file=sys.stderr)
        categories = []
    
    if 'cart' in session:
        cart_count = sum(item.get('quantity', 1) for item in session['cart'])
        cart_total = calculate_cart_total()
    
    return dict(
        now=datetime.now(),
        categories=categories,
        cart_count=cart_count,
        cart_total=cart_total,
        current_year=datetime.now().year,
        config=BUSINESS_CONFIG,
        format_price=format_price
    )

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"❌ 500 Error: {error}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    return render_template('500.html'), 500

# ========== PUBLIC ROUTES ==========

@app.route('/')
def index():
    """Homepage"""
    try:
        featured_products = Product.query.filter_by(featured=True, active=True).limit(8).all()
        categories = Category.query.limit(6).all()
        reviews = Review.query.filter_by(approved=True).limit(5).all()
        
        return render_template('index.html',
                             featured_products=featured_products,
                             categories=categories,
                             reviews=reviews)
    except Exception as e:
        print(f"❌ Homepage error: {str(e)}", file=sys.stderr)
        return render_template('index.html',
                             featured_products=[],
                             categories=[],
                             reviews=[])

@app.route('/shop')
def shop():
    """Shop page - FIXED PAGINATION"""
    try:
        category_id = request.args.get('category', type=int)
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        query = Product.query.filter_by(active=True)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        # FIXED: Proper pagination handling
        products_pagination = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = Category.query.all()
        
        return render_template('shop.html',
                             products=products_pagination,
                             categories=categories,
                             category_id=category_id,
                             search_query=search)
    except Exception as e:
        print(f"❌ Shop error: {str(e)}", file=sys.stderr)
        flash('Error loading products.', 'danger')
        return render_template('shop.html',
                             products=[],
                             categories=[],
                             category_id=None,
                             search_query='')

@app.route('/product/<int:id>')
def product_detail(id):
    """Product detail page"""
    try:
        product = Product.query.get_or_404(id)
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.active == True
        ).limit(4).all()
        
        reviews = Review.query.filter_by(product_id=id, approved=True).all()
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products,
                             reviews=reviews)
    except Exception as e:
        print(f"❌ Product detail error: {str(e)}", file=sys.stderr)
        flash('Product not found.', 'danger')
        return redirect(url_for('shop'))

@app.route('/cart')
def cart():
    """Shopping cart page - FIXED 404"""
    cart_items = session.get('cart', [])
    subtotal = calculate_cart_total()
    delivery_fee = DeliveryCalculator.calculate_delivery_fee(subtotal)
    total = subtotal + delivery_fee
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_fee=delivery_fee,
                         total=total,
                         free_delivery_threshold=DeliveryCalculator.FREE_DELIVERY_THRESHOLD)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    try:
        product = Product.query.get_or_404(product_id)
        
        if not product.active or product.quantity <= 0:
            flash('Product is not available.', 'warning')
            return redirect(request.referrer or url_for('shop'))
        
        quantity = int(request.form.get('quantity', 1))
        
        if quantity > product.quantity:
            flash(f'Only {product.quantity} items available in stock.', 'warning')
            return redirect(request.referrer or url_for('product_detail', id=product.id))
        
        if 'cart' not in session:
            session['cart'] = []
        
        cart = session['cart']
        
        # Check if product already in cart
        for item in cart:
            if item['id'] == product_id:
                new_quantity = item['quantity'] + quantity
                if new_quantity > product.quantity:
                    flash(f'Cannot add more. Only {product.quantity - item["quantity"]} more available.', 'warning')
                    return redirect(request.referrer or url_for('cart'))
                
                item['quantity'] = new_quantity
                session.modified = True
                flash(f'Added {quantity} more of {product.name} to cart.', 'success')
                return redirect(request.referrer or url_for('cart'))
        
        # Add new item to cart
        cart.append({
            'id': product_id,
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image_url': product.image_url,
            'stock': product.quantity,
            'slug': product.slug
        })
        session.modified = True
        
        flash(f'{product.name} added to cart!', 'success')
        return redirect(request.referrer or url_for('cart'))
        
    except Exception as e:
        print(f"❌ Add to cart error: {str(e)}", file=sys.stderr)
        flash('Error adding to cart. Please try again.', 'danger')
        return redirect(request.referrer or url_for('shop'))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update cart item quantity"""
    try:
        if 'cart' not in session:
            return redirect(url_for('cart'))
        
        cart = session['cart']
        quantity = int(request.form.get('quantity', 1))
        
        for item in cart:
            if item['id'] == product_id:
                if quantity <= 0:
                    cart.remove(item)
                else:
                    product = Product.query.get(product_id)
                    if product and quantity > product.quantity:
                        flash(f'Only {product.quantity} items available in stock.', 'warning')
                        return redirect(url_for('cart'))
                    item['quantity'] = quantity
                break
        
        session.modified = True
        flash('Cart updated successfully!', 'success')
        return redirect(url_for('cart'))
        
    except Exception as e:
        flash('Error updating cart.', 'danger')
        return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    try:
        if 'cart' in session:
            cart = session['cart']
            session['cart'] = [item for item in cart if item['id'] != product_id]
            session.modified = True
            flash('Item removed from cart.', 'info')
        
        return redirect(url_for('cart'))
    except Exception as e:
        flash('Error removing item from cart.', 'danger')
        return redirect(url_for('cart'))

# ========== CUSTOMER AUTHENTICATION ROUTES ==========

@app.route('/register', methods=['GET', 'POST'])
def customer_register():
    """Customer registration"""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            
            # Check if customer exists
            existing_customer = Customer.query.filter_by(email=email).first()
            if existing_customer:
                flash('Email already registered. Please login.', 'danger')
                return redirect(url_for('customer_login'))
            
            # Create new customer
            customer = Customer(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            customer.set_password(password)
            
            db.session.add(customer)
            db.session.commit()
            
            # Auto login after registration
            session['customer_id'] = customer.id
            session['customer_name'] = f"{customer.first_name} {customer.last_name}"
            session.pop('pending_checkout', None)
            
            flash('Registration successful! Welcome!', 'success')
            return redirect(url_for('account'))
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ Registration error: {str(e)}", file=sys.stderr)
            flash('Error during registration. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def customer_login():
    """Customer login"""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            
            customer = Customer.query.filter_by(email=email).first()
            
            if customer and customer.check_password(password):
                session['customer_id'] = customer.id
                session['customer_name'] = f"{customer.first_name} {customer.last_name}"
                session.pop('pending_checkout', None)
                
                flash('Login successful!', 'success')
                
                # Redirect to checkout if there's a pending order
                if 'pending_checkout' in session:
                    return redirect(url_for('checkout'))
                return redirect(url_for('account'))
            else:
                flash('Invalid email or password', 'danger')
        
        except Exception as e:
            print(f"❌ Login error: {str(e)}", file=sys.stderr)
            flash('Login error. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def customer_logout():
    """Customer logout"""
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    session.pop('pending_checkout', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/account')
@customer_required
def account():
    """Customer account page"""
    customer = Customer.query.get(session['customer_id'])
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()
    
    return render_template('account.html', customer=customer, orders=orders)

# ========== CHECKOUT ROUTES ==========

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page with delivery calculator"""
    if 'customer_id' not in session:
        session['pending_checkout'] = True
        flash('Please login to complete your order', 'warning')
        return redirect(url_for('customer_login'))
    
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('shop'))
    
    # Calculate totals
    subtotal = calculate_cart_total()
    delivery_city = request.form.get('city', '')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            city = request.form.get('city')
            state = request.form.get('state')
            payment_method = request.form.get('payment_method', 'bank_transfer')
            notes = request.form.get('notes', '')
            
            # Validate required fields
            if not all([name, email, phone, address, city, state]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('checkout'))
            
            # Calculate delivery fee
            delivery_fee = DeliveryCalculator.calculate_delivery_fee(subtotal, city)
            total = subtotal + delivery_fee
            
            # Create order
            order = Order(
                order_number=generate_order_number(),
                customer_id=session['customer_id'],
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                shipping_address=address,
                shipping_city=city,
                shipping_state=state,
                total_amount=subtotal,
                shipping_amount=delivery_fee,
                final_amount=total,
                payment_method=payment_method,
                notes=notes
            )
            
            db.session.add(order)
            db.session.flush()
            
            # Add order items
            for item in cart_items:
                product = Product.query.get(item['id'])
                if product:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        quantity=item['quantity'],
                        unit_price=item['price'],
                        total_price=item['price'] * item['quantity']
                    )
                    db.session.add(order_item)
            
            db.session.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            flash(f'Order #{order.order_number} created successfully! We will contact you shortly.', 'success')
            return render_template('order.html',
                                 order=order,
                                 bank_details=BUSINESS_CONFIG)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Checkout error: {str(e)}", file=sys.stderr)
            flash('Error processing order. Please try again.', 'danger')
            return redirect(url_for('checkout'))
    
    # GET request - show checkout form
    delivery_fee = DeliveryCalculator.calculate_delivery_fee(subtotal, delivery_city)
    total = subtotal + delivery_fee
    
    customer = None
    if 'customer_id' in session:
        customer = Customer.query.get(session['customer_id'])
    
    return render_template('checkout.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_fee=delivery_fee,
                         total=total,
                         free_delivery_threshold=DeliveryCalculator.FREE_DELIVERY_THRESHOLD,
                         customer=customer)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            if not all([name, email, subject, message]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('contact'))
            
            # Here you would save to database or send email
            flash('Your message has been sent successfully! We will contact you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html')

# ========== ADMIN ROUTES ==========

@app.route('/admin')
@app.route('/admin/login')
def admin_login():
    """Admin login - FIXED NETWORK ERROR"""
    if 'admin_id' in session and session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Query admin user
            admin = User.query.filter_by(username=username, is_admin=True).first()
            
            if admin and admin.check_password(password):
                session['admin_id'] = admin.id
                session['admin_name'] = admin.username
                session['is_admin'] = True
                
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials', 'danger')
                
        except Exception as e:
            print(f"❌ Admin login error: {str(e)}", file=sys.stderr)
            flash('Login error. Please try again.', 'danger')
    
    return render_template('admin/admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('is_admin', None)
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        total_orders = Order.query.count()
        total_products = Product.query.count()
        total_customers = Customer.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        return render_template('admin/admin_dashboard.html',
                             total_orders=total_orders,
                             total_products=total_products,
                             total_customers=total_customers,
                             pending_orders=pending_orders,
                             recent_orders=recent_orders)
    except Exception as e:
        print(f"❌ Admin dashboard error: {str(e)}", file=sys.stderr)
        flash('Error loading dashboard.', 'danger')
        return render_template('admin/admin_dashboard.html',
                             total_orders=0,
                             total_products=0,
                             total_customers=0,
                             pending_orders=0,
                             recent_orders=[])

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products list"""
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
        categories = Category.query.all()
        
        return render_template('admin/products.html',
                             products=products,
                             categories=categories)
    except Exception as e:
        print(f"❌ Admin products error: {str(e)}", file=sys.stderr)
        flash('Error loading products.', 'danger')
        return render_template('admin/products.html',
                             products=[],
                             categories=[])

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Add product"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price', 0))
            compare_price = request.form.get('compare_price')
            quantity = int(request.form.get('quantity', 0))
            category_id = int(request.form.get('category_id'))
            featured = 'featured' in request.form
            active = 'active' in request.form
            
            # Generate slug and SKU
            slug = name.lower().replace(' ', '-').replace('"', '').replace("'", '')
            sku = f"HAIR-{random.randint(1000, 9999)}"
            
            product = Product(
                name=name,
                slug=slug,
                description=description,
                price=price,
                compare_price=float(compare_price) if compare_price else None,
                quantity=quantity,
                sku=sku,
                category_id=category_id,
                featured=featured,
                active=active
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Add product error: {str(e)}", file=sys.stderr)
            flash('Error adding product. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders"""
    try:
        status = request.args.get('status', 'all')
        
        query = Order.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        return render_template('admin/order.html',
                             orders=orders,
                             status=status)
    except Exception as e:
        print(f"❌ Admin orders error: {str(e)}", file=sys.stderr)
        flash('Error loading orders.', 'danger')
        return render_template('admin/order.html',
                             orders=[],
                             status='all')

@app.route('/admin/orders/<int:id>')
@admin_required
def admin_order_detail(id):
    """Order detail"""
    try:
        order = Order.query.get_or_404(id)
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        
        return render_template('admin/order_detail.html',
                             order=order,
                             order_items=order_items)
    except Exception as e:
        print(f"❌ Admin order detail error: {str(e)}", file=sys.stderr)
        flash('Error loading order details.', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    """Admin reviews"""
    try:
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        return render_template('admin/reviews.html', reviews=reviews)
    except Exception as e:
        print(f"❌ Admin reviews error: {str(e)}", file=sys.stderr)
        flash('Error loading reviews.', 'danger')
        return render_template('admin/reviews.html', reviews=[])

# ========== HEALTH CHECK ==========
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
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

# ========== APPLICATION FACTORY ==========
def create_app():
    """Application factory for Gunicorn"""
    return app

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Create required directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🚀 NORA HAIR LINE E-COMMERCE", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"🌐 Homepage: http://localhost:{port}", file=sys.stderr)
    print(f"🛍️  Shop: http://localhost:{port}/shop", file=sys.stderr)
    print(f"👑 Admin: http://localhost:{port}/admin", file=sys.stderr)
    print(f"👤 Customer Login: http://localhost:{port}/login", file=sys.stderr)
    print(f"📧 Admin Login: admin/admin123", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    app.run(host='0.0.0.0', port=port, debug=True)
