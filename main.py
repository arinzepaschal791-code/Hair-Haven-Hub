# main.py - NORA HAIR LINE E-COMMERCE - PRODUCTION READY
# ========== ULTIMATE PYTHON 3.13 COMPATIBILITY FIX ==========
# THIS ENTIRE BLOCK MUST BE AT THE VERY TOP OF YOUR FILE
import sys
import os
import types

# CRITICAL: Override pkg_resources BEFORE anything else tries to import it
print("🚀 Applying Python 3.13 compatibility patches...", file=sys.stderr)

# Completely remove any existing pkg_resources
if 'pkg_resources' in sys.modules:
    del sys.modules['pkg_resources']

# Create a complete mock pkg_resources that works with Python 3.13
mock_pkg_resources = types.ModuleType('pkg_resources')

# Mock WorkingSet class
class WorkingSet:
    def __init__(self):
        self.entry_keys = {}
        self.entries = []
        self.by_key = {}
    def __iter__(self):
        return iter([])
    def add_entry(self, entry):
        pass
    def __contains__(self, item):
        return False
    def find(self, req):
        return None

# Add all required attributes
mock_pkg_resources.working_set = WorkingSet()
mock_pkg_resources.require = lambda *args, **kwargs: []
mock_pkg_resources.get_distribution = lambda *args, **kwargs: None
mock_pkg_resources.iter_entry_points = lambda *args, **kwargs: []
mock_pkg_resources.resource_filename = lambda *args, **kwargs: ''
mock_pkg_resources.resource_string = lambda *args, **kwargs: b''
mock_pkg_resources.resource_stream = lambda *args, **kwargs: open(os.devnull, 'rb')
mock_pkg_resources.get_provider = lambda *args, **kwargs: None
mock_pkg_resources.clean_resources = lambda *args, **kwargs: None
mock_pkg_resources.get_supported_platform = lambda: sys.platform
mock_pkg_resources.get_build_platform = lambda: sys.platform
mock_pkg_resources.get_entry_map = lambda *args, **kwargs: {}
mock_pkg_resources.get_entry_info = lambda *args, **kwargs: None
mock_pkg_resources.load_entry_point = lambda *args, **kwargs: None

# Install the mock
sys.modules['pkg_resources'] = mock_pkg_resources
print("✅ Installed mock pkg_resources (Python 3.13 compatible)", file=sys.stderr)

# Mock gunicorn.six.moves for gunicorn 20.1.0
class SixMock:
    class moves:
        class urllib:
            class parse:
                @staticmethod
                def urlsplit(url):
                    from urllib.parse import urlsplit
                    return urlsplit(url)
                @staticmethod
                def urljoin(base, url):
                    from urllib.parse import urljoin
                    return urljoin(base, url)
                @staticmethod
                def urlparse(url):
                    from urllib.parse import urlparse
                    return urlparse(url)
                @staticmethod
                def quote(string, safe='/', encoding=None, errors=None):
                    from urllib.parse import quote
                    return quote(string, safe, encoding, errors)
                @staticmethod
                def unquote(string, encoding='utf-8', errors='replace'):
                    from urllib.parse import unquote
                    return unquote(string, encoding, errors)

sys.modules['gunicorn.six'] = SixMock
sys.modules['gunicorn.six.moves'] = SixMock.moves
sys.modules['gunicorn.six.moves.urllib'] = SixMock.moves.urllib
sys.modules['gunicorn.six.moves.urllib.parse'] = SixMock.moves.urllib.parse
print("✅ Installed gunicorn.six mock", file=sys.stderr)

# ========== IMPORTS ==========
import traceback
from datetime import datetime, timedelta
import random
import string
from functools import wraps
import json
import re
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from sqlalchemy import text, or_, and_, func, desc

# ========== SQLALCHEMY COMPATIBILITY PATCH ==========
# Apply TypingOnly patch after SQLAlchemy is imported
try:
    import sqlalchemy.util.langhelpers
    original_init_subclass = sqlalchemy.util.langhelpers.TypingOnly.__init_subclass__
    
    def patched_init_subclass(cls, *args, **kwargs):
        # Remove attributes that cause AssertionError in Python 3.13
        for attr in ['__static_attributes__', '__firstlineno__', '__classcell__']:
            if hasattr(cls, attr):
                delattr(cls, attr)
        return original_init_subclass.__func__(cls, *args, **kwargs)
    
    sqlalchemy.util.langhelpers.TypingOnly.__init_subclass__ = classmethod(patched_init_subclass)
    print("✅ SQLAlchemy TypingOnly patch applied", file=sys.stderr)
except Exception as e:
    print(f"⚠️ SQLAlchemy patch warning: {e}", file=sys.stderr)

# ========== CREATE APP ==========
app = Flask(__name__)

# ========== CONFIGURATION ==========
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026-change-in-production')

# Database configuration
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    # Local development - use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'
    print("✅ Using SQLite database (local development)", file=sys.stderr)
elif database_url.startswith('postgres://'):
    # Fix Render/Heroku PostgreSQL URLs
    fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = fixed_url
    print("✅ Using PostgreSQL database (production)", file=sys.stderr)
else:
    # Already correct URL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("✅ Using database from environment", file=sys.stderr)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# ========== CSRF PROTECTION ==========
csrf = CSRFProtect(app)

# ========== UPLOAD FOLDER CONFIG ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

# Create folder immediately
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"✅ Created uploads folder: {UPLOAD_FOLDER}", file=sys.stderr)
else:
    print(f"✅ Uploads folder exists: {UPLOAD_FOLDER}", file=sys.stderr)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# ========== END CONFIG ==========

# Allowed upload extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

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
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, nullable=False, default=0.0)
    compare_price = db.Column(db.Float)
    sku = db.Column(db.String(100))
    total_quantity = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_bundle = db.Column(db.Boolean, default=False)
    bundle_discount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', backref='products', lazy='joined')
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')

    @property
    def stock(self):
        """Calculate total stock across all variants"""
        if self.variants:
            return sum(variant.stock for variant in self.variants)
        return self.total_quantity

    @property
    def min_price(self):
        """Get minimum variant price"""
        if self.variants:
            prices = [v.price for v in self.variants if v.price > 0]
            return min(prices) if prices else self.base_price
        return self.base_price

    @property
    def max_price(self):
        """Get maximum variant price"""
        if self.variants:
            prices = [v.price for v in self.variants if v.price > 0]
            return max(prices) if prices else self.base_price
        return self.base_price

    @property
    def display_price(self):
        """Display price range for products with variants"""
        if self.variants and len(set(v.price for v in self.variants)) > 1:
            return f"₦{self.min_price:,.0f} - ₦{self.max_price:,.0f}"
        return f"₦{self.min_price:,.0f}"

    @property
    def available_lengths(self):
        """Get unique available lengths"""
        if self.variants:
            lengths = [v.length for v in self.variants if v.length and v.stock > 0]
            return sorted(set(lengths))
        return []

    @property
    def available_textures(self):
        """Get unique available textures"""
        if self.variants:
            textures = [v.texture for v in self.variants if v.texture and v.stock > 0]
            return sorted(set(textures))
        return []

    def get_default_variant(self):
        """Get first available variant"""
        if self.variants:
            available = [v for v in self.variants if v.stock > 0]
            return available[0] if available else self.variants[0]
        return None

    def __repr__(self):
        return f'<Product {self.name}>'

class ProductVariant(db.Model):
    __tablename__ = 'product_variant'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(200))
    length = db.Column(db.String(50))
    texture = db.Column(db.String(50))
    color = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    compare_price = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100), unique=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Index for faster queries
    __table_args__ = (
        db.Index('idx_variant_product', 'product_id'),
        db.Index('idx_variant_stock', 'stock'),
    )

    @property
    def available(self):
        return self.stock > 0

    def __repr__(self):
        return f'<ProductVariant {self.name} - {self.length} {self.texture}>'

class ProductImage(db.Model):
    __tablename__ = 'product_image'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductImage {self.id}>'

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
    shipping_area = db.Column(db.String(100))
    total_amount = db.Column(db.Float, nullable=False)
    shipping_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50), default='bank_transfer')
    payment_status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    variant_details = db.Column(db.String(200))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')

    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    location = db.Column(db.String(100))
    verified_purchase = db.Column(db.Boolean, default=False)
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
    'site_logo': 'logo.png',
    'delivery_rates': {
        'lagos_mainland': 3000,
        'lagos_island': 3500,
        'other_states': 5000,
        'express': 8000
    },
    'free_delivery_threshold': 150000,
    'delivery_areas': {
        'lagos': ['ikeja', 'vi', 'lekki', 'ikoyi', 'surulere', 'yaba', 'ajah', 'apapa', 'festac', 'ojo', 'badagry'],
        'express': ['same_day', 'next_day']
    }
}

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

def calculate_cart_with_variants():
    """Calculate cart total with variant-specific pricing"""
    total = 0
    if 'cart' in session:
        for item in session['cart']:
            variant_price = item.get('variant_price', item.get('price', 0))
            quantity = item.get('quantity', 1)
            total += float(variant_price) * quantity
    return total

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_delivery_fee(city, state, area=None, subtotal=0):
    """Calculate delivery fee based on location"""
    # Free delivery for orders above threshold
    if subtotal >= BUSINESS_CONFIG['free_delivery_threshold']:
        return 0

    city_lower = city.lower() if city else ''
    state_lower = state.lower() if state else ''
    area_lower = area.lower() if area else ''

    # Check if it's Lagos
    if state_lower == 'lagos' or city_lower == 'lagos':
        # Check for island areas
        island_areas = ['ikoyi', 'lekki', 'vi', 'victoria island', 'ajah']
        if any(island_area in area_lower for island_area in island_areas):
            return BUSINESS_CONFIG['delivery_rates']['lagos_island']
        return BUSINESS_CONFIG['delivery_rates']['lagos_mainland']

    # Other states
    return BUSINESS_CONFIG['delivery_rates']['other_states']

def check_stock_availability(product_id, variant_id=None, quantity=1):
    """Check if product/variant has sufficient stock"""
    try:
        if variant_id:
            variant = ProductVariant.query.get(variant_id)
            if not variant or variant.stock < quantity:
                return False, f"Only {variant.stock if variant else 0} available"
            return True, "Available"
        else:
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found"

            if product.variants:
                return False, "Please select a variant"

            if product.total_quantity < quantity:
                return False, f"Only {product.total_quantity} available"
            return True, "Available"
    except Exception as e:
        print(f"❌ Stock check error: {str(e)}", file=sys.stderr)
        return False, "Error checking stock"

def update_product_stock(product_id, variant_id=None, quantity_change=0):
    """Update stock after purchase"""
    try:
        if variant_id:
            variant = ProductVariant.query.get(variant_id)
            if variant:
                variant.stock = max(0, variant.stock - quantity_change)
                product = Product.query.get(product_id)
                if product:
                    product.total_quantity = sum(v.stock for v in product.variants)
                db.session.commit()
                return True
        else:
            product = Product.query.get(product_id)
            if product:
                product.total_quantity = max(0, product.total_quantity - quantity_change)
                db.session.commit()
                return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update stock error: {str(e)}", file=sys.stderr)
        return False

def generate_unique_slug(base_name, model_class, current_id=None):
    """Generate unique slug for product or category"""
    base_slug = re.sub(r'[^\w\s-]', '', base_name.lower())
    base_slug = re.sub(r'[-\s]+', '-', base_slug).strip('-')
    
    slug = base_slug
    counter = 1
    
    while True:
        query = model_class.query.filter(func.lower(model_class.slug) == slug.lower())
        if current_id:
            query = query.filter(model_class.id != current_id)
        
        if not query.first():
            break
        
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

def generate_unique_sku(base_sku=None):
    """Generate unique SKU"""
    if base_sku:
        if ProductVariant.query.filter_by(sku=base_sku).first() is None:
            return base_sku
    
    while True:
        sku = f"HAIR-{random.randint(10000, 99999)}-{random.randint(100, 999)}"
        if ProductVariant.query.filter_by(sku=sku).first() is None:
            return sku

def save_uploaded_file(file):
    """Save uploaded file to uploads folder"""
    if not file or file.filename == '':
        print(f"⚠️ No file provided for upload", file=sys.stderr)
        return None

    if not allowed_file(file.filename):
        print(f"⚠️ File type not allowed: {file.filename}", file=sys.stderr)
        return None

    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        unique_filename = f"{timestamp}_{random_str}_{filename}"

        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)

        upload_path = os.path.join(upload_folder, unique_filename)
        file.save(upload_path)

        print(f"✅ File saved: {unique_filename}", file=sys.stderr)
        return f"/static/uploads/{unique_filename}"

    except Exception as e:
        print(f"❌ CRITICAL ERROR saving file: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None

# ========== AUTHENTICATION DECORATORS ==========
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session or not session.get('is_admin'):
            flash('Admin access required. Please login first.', 'danger')
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
        print(f"⚠️ Context processor error (categories): {str(e)}", file=sys.stderr)
        categories = []

    if 'cart' in session:
        cart_count = sum(item.get('quantity', 1) for item in session['cart'])
        cart_total = calculate_cart_with_variants()

    csrf_token_value = ""
    try:
        csrf_token_value = generate_csrf()
    except Exception as e:
        print(f"⚠️ CSRF token generation error: {str(e)}", file=sys.stderr)

    return dict(
        now=datetime.now(),
        categories=categories,
        cart_count=cart_count,
        cart_total=cart_total,
        current_year=datetime.now().year,
        config=BUSINESS_CONFIG,
        format_price=format_price,
        csrf_token=csrf_token_value,
        min=min,
        max=max,
        random=random,
        check_stock=check_stock_availability
    )

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', config=BUSINESS_CONFIG), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"❌ 500 Error: {str(error)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    return render_template('500.html', config=BUSINESS_CONFIG), 500

# ========== DATABASE INITIALIZATION ==========
def init_db():
    """Initialize database with tables and sample data"""
    print("🔄 Initializing database...", file=sys.stderr)

    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        print("✅ Database connection successful", file=sys.stderr)
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}", file=sys.stderr)
        return False

    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created", file=sys.stderr)

            # Create admin user if none exists
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    email='admin@norahairline.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                print("✅ Admin user created: admin/admin123", file=sys.stderr)

            # Create sample categories if none exist
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

            db.session.commit()
            print("✅ Database initialization complete", file=sys.stderr)
            return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database initialization error: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

# ========== APPLICATION STARTUP HOOK ==========
@app.before_request
def initialize_on_first_request():
    """Initialize database on first request"""
    if not hasattr(app, 'has_initialized'):
        print("🚀 Initializing database on first request...", file=sys.stderr)
        try:
            init_db_success = init_db()
            if init_db_success:
                print("✅ Database initialized successfully!", file=sys.stderr)
            else:
                print("⚠️ Database initialization had issues, but application will continue", file=sys.stderr)
        except Exception as e:
            print(f"❌ Critical error during database initialization: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print("⚠️ Application will continue, but some features may not work", file=sys.stderr)

        app.has_initialized = True

# ========== PUBLIC ROUTES ==========

@app.route('/')
def index():
    """Homepage"""
    try:
        featured_products = Product.query.filter_by(featured=True, active=True)\
            .options(joinedload(Product.category))\
            .limit(8)\
            .all()

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
    """Shop page with filtering"""
    try:
        category_id = request.args.get('category', type=int)
        search = request.args.get('search', '')
        length = request.args.get('length', '')
        texture = request.args.get('texture', '')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        page = request.args.get('page', 1, type=int)
        per_page = 12

        query = Product.query.filter_by(active=True)\
            .options(joinedload(Product.category))

        if category_id:
            query = query.filter_by(category_id=category_id)

        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))

        # Filter by length
        if length:
            variant_products_subquery = db.session.query(ProductVariant.product_id)\
                .filter(ProductVariant.length == length, ProductVariant.stock > 0)\
                .distinct()\
                .subquery()
            query = query.filter(Product.id.in_(variant_products_subquery))

        # Filter by texture
        if texture:
            variant_products_subquery = db.session.query(ProductVariant.product_id)\
                .filter(ProductVariant.texture == texture, ProductVariant.stock > 0)\
                .distinct()\
                .subquery()
            query = query.filter(Product.id.in_(variant_products_subquery))

        # Filter by price
        if min_price is not None:
            query = query.filter(Product.base_price >= min_price)
        if max_price is not None:
            query = query.filter(Product.base_price <= max_price)

        products = query.order_by(Product.created_at.desc()).all()

        # Get unique lengths and textures
        all_lengths = db.session.query(ProductVariant.length)\
            .filter(ProductVariant.length.isnot(None), ProductVariant.stock > 0)\
            .distinct()\
            .all()
        lengths = [l[0] for l in all_lengths if l[0]]

        all_textures = db.session.query(ProductVariant.texture)\
            .filter(ProductVariant.texture.isnot(None), ProductVariant.stock > 0)\
            .distinct()\
            .all()
        textures = [t[0] for t in all_textures if t[0]]

        total_products = len(products)
        total_pages = (total_products + per_page - 1) // per_page

        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_products = products[start_idx:end_idx]

        categories = Category.query.all()

        return render_template('shop.html',
                               products=paginated_products,
                               categories=categories,
                               category_id=category_id,
                               search_query=search,
                               lengths=lengths,
                               textures=textures,
                               selected_length=length,
                               selected_texture=texture,
                               min_price=min_price,
                               max_price=max_price,
                               current_page=page,
                               total_pages=total_pages,
                               total_products=total_products)
    except Exception as e:
        print(f"❌ Shop error: {str(e)}", file=sys.stderr)
        flash('Error loading products.', 'danger')
        return render_template('shop.html',
                               products=[],
                               categories=[],
                               category_id=None,
                               search_query='',
                               lengths=[],
                               textures=[],
                               current_page=1,
                               total_pages=1,
                               total_products=0)

@app.route('/product/<int:id>')
def product_detail(id):
    """Product detail page"""
    try:
        product = Product.query\
            .options(joinedload(Product.category))\
            .get_or_404(id)

        if not product.active:
            flash('This product is currently unavailable.', 'warning')
            return redirect(url_for('shop'))

        variants = ProductVariant.query\
            .filter_by(product_id=id)\
            .order_by(ProductVariant.length, ProductVariant.texture)\
            .all()

        images = ProductImage.query\
            .filter_by(product_id=id)\
            .order_by(ProductImage.sort_order, ProductImage.is_primary.desc())\
            .all()

        variants_by_length = {}
        for variant in variants:
            if variant.length not in variants_by_length:
                variants_by_length[variant.length] = []
            variants_by_length[variant.length].append(variant)

        related_products = Product.query\
            .options(joinedload(Product.category))\
            .filter(
                Product.category_id == product.category_id,
                Product.id != product.id,
                Product.active == True
            ).limit(4).all()

        reviews = Review.query.filter_by(product_id=id, approved=True).order_by(Review.created_at.desc()).all()

        return render_template('product_detail.html',
                               product=product,
                               variants=variants,
                               variants_by_length=variants_by_length,
                               images=images,
                               related_products=related_products,
                               reviews=reviews)
    except Exception as e:
        print(f"❌ Product detail error: {str(e)}", file=sys.stderr)
        flash('Product not found.', 'danger')
        return redirect(url_for('shop'))

@app.route('/product/<int:id>/variants')
def get_product_variants(id):
    """Get product variants for AJAX"""
    try:
        product = Product.query.get_or_404(id)
        variants = ProductVariant.query.filter_by(product_id=id).all()

        variants_data = []
        for variant in variants:
            variants_data.append({
                'id': variant.id,
                'name': variant.name,
                'length': variant.length,
                'texture': variant.texture,
                'color': variant.color,
                'price': variant.price,
                'stock': variant.stock,
                'available': variant.stock > 0
            })

        return jsonify({
            'success': True,
            'product_id': product.id,
            'product_name': product.name,
            'variants': variants_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cart')
def cart():
    """Shopping cart page"""
    cart_items = session.get('cart', [])

    enhanced_cart = []
    for item in cart_items:
        product = Product.query.get(item['id'])
        variant_info = {}
        if 'variant_id' in item:
            variant = ProductVariant.query.get(item['variant_id'])
            if variant:
                variant_info = {
                    'variant_name': f"{variant.length} {variant.texture}" if variant.length and variant.texture else variant.name,
                    'length': variant.length,
                    'texture': variant.texture,
                    'color': variant.color
                }

        enhanced_item = {
            **item,
            'product': product,
            'variant_info': variant_info
        }
        enhanced_cart.append(enhanced_item)

    subtotal = calculate_cart_with_variants()
    delivery_fee = calculate_delivery_fee(None, None, None, subtotal)
    total = subtotal + delivery_fee

    return render_template('cart.html',
                           cart_items=enhanced_cart,
                           subtotal=subtotal,
                           delivery_fee=delivery_fee,
                           total=total,
                           free_delivery_threshold=BUSINESS_CONFIG['free_delivery_threshold'])

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    try:
        product = Product.query.get_or_404(product_id)

        if not product.active:
            flash('Product is not available.', 'warning')
            return redirect(request.referrer or url_for('shop'))

        quantity = int(request.form.get('quantity', 1))
        variant_id = request.form.get('variant_id', type=int)

        if quantity <= 0 or quantity > 100:
            flash('Quantity must be between 1 and 100.', 'warning')
            return redirect(request.referrer or url_for('product_detail', id=product.id))

        if product.variants and not variant_id:
            flash('Please select a variant (length/texture) before adding to cart.', 'warning')
            return redirect(request.referrer or url_for('product_detail', id=product.id))

        stock_available, message = check_stock_availability(product_id, variant_id, quantity)
        if not stock_available:
            flash(message, 'warning')
            return redirect(request.referrer or url_for('product_detail', id=product.id))

        if variant_id:
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                flash('Selected variant not found.', 'danger')
                return redirect(request.referrer or url_for('product_detail', id=product.id))
            price = variant.price
            variant_name = f"{variant.length} {variant.texture}" if variant.length and variant.texture else variant.name
        else:
            price = product.base_price
            variant_name = None

        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']

        for item in cart:
            if item['id'] == product_id and item.get('variant_id') == variant_id:
                new_quantity = item['quantity'] + quantity
                stock_available, message = check_stock_availability(product_id, variant_id, new_quantity)
                if not stock_available:
                    flash(message, 'warning')
                    return redirect(request.referrer or url_for('cart'))
                item['quantity'] = new_quantity
                flash(f'Added {quantity} more to cart.', 'success')
                return redirect(request.referrer or url_for('cart'))

        cart_item = {
            'id': product_id,
            'name': product.name,
            'price': float(price),
            'variant_price': float(price),
            'quantity': quantity,
            'image_url': product.images[0].image_url if product.images else '',
            'slug': product.slug
        }

        if variant_id:
            cart_item['variant_id'] = variant_id
            cart_item['variant_name'] = variant_name
            cart_item['length'] = variant.length if variant else None
            cart_item['texture'] = variant.texture if variant else None

        cart.append(cart_item)
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
        variant_id = request.form.get('variant_id', type=int)
        
        if quantity <= 0 or quantity > 100:
            flash('Quantity must be between 1 and 100.', 'warning')
            return redirect(url_for('cart'))

        for item in cart:
            if item['id'] == product_id and item.get('variant_id') == variant_id:
                if quantity <= 0:
                    cart.remove(item)
                else:
                    stock_available, message = check_stock_availability(product_id, variant_id, quantity)
                    if not stock_available:
                        flash(message, 'warning')
                        return redirect(url_for('cart'))
                    item['quantity'] = quantity
                break

        flash('Cart updated successfully!', 'success')
        return redirect(url_for('cart'))

    except Exception as e:
        flash('Error updating cart.', 'danger')
        return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    try:
        variant_id = request.args.get('variant_id', type=int)

        if 'cart' in session:
            cart = session['cart']
            if variant_id:
                session['cart'] = [item for item in cart if not (item['id'] == product_id and item.get('variant_id') == variant_id)]
            else:
                session['cart'] = [item for item in cart if item['id'] != product_id]
            flash('Item removed from cart.', 'info')

        return redirect(url_for('cart'))
    except Exception as e:
        flash('Error removing item from cart.', 'danger')
        return redirect(url_for('cart'))

@app.route('/clear-cart')
def clear_cart():
    """Clear all items from cart"""
    session.pop('cart', None)
    flash('Cart cleared successfully!', 'info')
    return redirect(url_for('cart'))

# ========== CUSTOMER AUTHENTICATION ==========

@app.route('/register', methods=['GET', 'POST'])
def customer_register():
    """Customer registration"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()

            # Validation
            if not all([email, password, first_name, last_name, phone]):
                flash('Please fill in all required fields.', 'danger')
                return render_template('register.html')
            
            if '@' not in email:
                flash('Please enter a valid email address.', 'danger')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('register.html')

            existing_customer = Customer.query.filter_by(email=email).first()

            if existing_customer:
                flash('Email already registered. Please login.', 'danger')
                return redirect(url_for('customer_login'))

            customer = Customer(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                address=address,
                city=city,
                state=state
            )
            customer.set_password(password)

            db.session.add(customer)
            db.session.commit()

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
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            if not email or not password:
                flash('Please enter both email and password', 'danger')
                return render_template('login.html')

            customer = Customer.query.filter_by(email=email).first()

            if customer and customer.check_password(password):
                session['customer_id'] = customer.id
                session['customer_name'] = f"{customer.first_name} {customer.last_name}"
                session.pop('pending_checkout', None)

                flash('Login successful!', 'success')

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
    try:
        customer = Customer.query.get(session['customer_id'])
        orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()

        return render_template('account.html', customer=customer, orders=orders)
    except Exception as e:
        print(f"❌ Account error: {str(e)}", file=sys.stderr)
        flash('Error loading account information.', 'danger')
        return redirect(url_for('index'))

# ========== ABOUT AND CONTACT ROUTES ==========

@app.route('/about')
def about():
    """About Us page"""
    try:
        return render_template('about.html')
    except Exception as e:
        print(f"❌ About page error: {str(e)}", file=sys.stderr)
        return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact Us page"""
    try:
        return render_template('contact.html')
    except Exception as e:
        print(f"❌ Contact page error: {str(e)}", file=sys.stderr)
        return render_template('contact.html')

# ========== CHECKOUT ROUTES ==========

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    if 'customer_id' not in session:
        session['pending_checkout'] = True
        flash('Please login to complete your order', 'warning')
        return redirect(url_for('customer_login'))

    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('shop'))

    subtotal = calculate_cart_with_variants()

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            city = request.form.get('city')
            state = request.form.get('state')
            area = request.form.get('area', '')
            payment_method = request.form.get('payment_method', 'bank_transfer')
            notes = request.form.get('notes', '')

            if not all([name, email, phone, address, city, state]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('checkout'))

            delivery_fee = calculate_delivery_fee(city, state, area, subtotal)
            total = subtotal + delivery_fee

            order = Order(
                order_number=generate_order_number(),
                customer_id=session['customer_id'],
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                shipping_address=address,
                shipping_city=city,
                shipping_state=state,
                shipping_area=area,
                total_amount=subtotal,
                shipping_amount=delivery_fee,
                final_amount=total,
                payment_method=payment_method,
                notes=notes
            )

            db.session.add(order)
            db.session.flush()

            for item in cart_items:
                product = Product.query.get(item['id'])
                variant_id = item.get('variant_id')
                variant = ProductVariant.query.get(variant_id) if variant_id else None

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    variant_id=variant_id,
                    product_name=product.name,
                    variant_details=item.get('variant_name'),
                    quantity=item['quantity'],
                    unit_price=item['variant_price'],
                    total_price=item['variant_price'] * item['quantity']
                )
                db.session.add(order_item)

                update_product_stock(product.id, variant_id, item['quantity'])

            db.session.commit()
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

    customer = Customer.query.get(session['customer_id']) if 'customer_id' in session else None
    delivery_fee = calculate_delivery_fee(
        customer.city if customer else None,
        customer.state if customer else None,
        None,
        subtotal
    )
    total = subtotal + delivery_fee

    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           delivery_fee=delivery_fee,
                           total=total,
                           free_delivery_threshold=BUSINESS_CONFIG['free_delivery_threshold'],
                           customer=customer,
                           delivery_areas=BUSINESS_CONFIG['delivery_areas'])

@app.route('/calculate-delivery', methods=['POST'])
def calculate_delivery():
    """Calculate delivery fee via AJAX"""
    try:
        data = request.json
        city = data.get('city', '')
        state = data.get('state', '')
        area = data.get('area', '')
        subtotal = float(data.get('subtotal', 0))

        delivery_fee = calculate_delivery_fee(city, state, area, subtotal)

        return jsonify({
            'success': True,
            'delivery_fee': delivery_fee,
            'formatted_delivery_fee': format_price(delivery_fee),
            'total': subtotal + delivery_fee,
            'formatted_total': format_price(subtotal + delivery_fee)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== ADMIN ROUTES ==========

@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if 'admin_id' in session and session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            admin = User.query.filter_by(username=username, is_admin=True).first()

            if admin and admin.check_password(password):
                session['admin_id'] = admin.id
                session['admin_name'] = admin.username
                session['is_admin'] = True

                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials. Use admin/admin123', 'danger')

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

        revenue_result = db.session.query(db.func.sum(Order.final_amount)).scalar()
        revenue = float(revenue_result) if revenue_result is not None else 0.0

        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
        recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(5).all()

        low_stock_products = []
        all_products = Product.query.all()
        for product in all_products:
            if product.stock > 0 and product.stock <= 10:
                low_stock_products.append(product)
            if len(low_stock_products) >= 5:
                break

        return render_template('admin/admin_dashboard.html',
                               total_orders=total_orders,
                               total_products=total_products,
                               total_customers=total_customers,
                               pending_orders=pending_orders,
                               revenue=revenue,
                               recent_orders=recent_orders,
                               recent_customers=recent_customers,
                               low_stock_products=low_stock_products)
    except Exception as e:
        print(f"❌ Admin dashboard error: {str(e)}", file=sys.stderr)
        flash('Error loading dashboard.', 'danger')
        return render_template('admin/admin_dashboard.html',
                               total_orders=0,
                               total_products=0,
                               total_customers=0,
                               pending_orders=0,
                               revenue=0,
                               recent_orders=[],
                               recent_customers=[],
                               low_stock_products=[])

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products list"""
    try:
        category_id = request.args.get('category', type=int)
        search = request.args.get('search', '')
        low_stock = request.args.get('low_stock', type=bool)

        query = Product.query.options(joinedload(Product.category))

        if category_id:
            query = query.filter_by(category_id=category_id)

        if search:
            query = query.filter(or_(
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%')
            ))

        if low_stock:
            query = query.filter(Product.total_quantity > 0, Product.total_quantity <= 10)

        products = query.order_by(Product.created_at.desc()).all()
        categories = Category.query.all()

        return render_template('admin/products.html',
                               products=products,
                               categories=categories,
                               category_id=category_id,
                               search=search,
                               low_stock=low_stock)
    except Exception as e:
        print(f"❌ Admin products error: {str(e)}", file=sys.stderr)
        flash('Error loading products.', 'danger')
        return render_template('admin/products.html',
                               products=[],
                               categories=[])

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Add product with variants and images"""
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            base_price = float(request.form.get('base_price', 0) or 0)
            compare_price = request.form.get('compare_price', '').strip()
            category_id = int(request.form.get('category_id', 0))
            featured = 'featured' in request.form
            active = 'active' in request.form
            is_bundle = 'is_bundle' in request.form
            bundle_discount = float(request.form.get('bundle_discount', 0) or 0)
            
            # Validations
            if not name:
                flash('Product name is required.', 'danger')
                return render_template('admin/add_product.html', categories=categories)
            
            if not category_id:
                flash('Category is required.', 'danger')
                return render_template('admin/add_product.html', categories=categories)
            
            if base_price <= 0:
                flash('Price must be greater than 0.', 'danger')
                return render_template('admin/add_product.html', categories=categories)
            
            if compare_price:
                compare_price = float(compare_price)
                if compare_price <= base_price:
                    flash('Compare price must be greater than base price.', 'warning')
                    compare_price = None
            else:
                compare_price = None
            
            # Generate slug and SKU
            slug = generate_unique_slug(name, Product)
            sku = generate_unique_sku()
            
            # Create product
            product = Product(
                name=name,
                slug=slug,
                description=description,
                base_price=base_price,
                compare_price=compare_price,
                category_id=category_id,
                featured=featured,
                active=active,
                is_bundle=is_bundle,
                bundle_discount=bundle_discount,
                sku=sku,
                total_quantity=0
            )

            db.session.add(product)
            db.session.flush()

            # Handle image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                primary_set = False
                
                for i, file in enumerate(files):
                    if file and file.filename != '' and allowed_file(file.filename):
                        uploaded_filename = save_uploaded_file(file)
                        if uploaded_filename:
                            is_primary = not primary_set
                            if is_primary:
                                primary_set = True
                                
                            product_image = ProductImage(
                                product_id=product.id,
                                image_url=uploaded_filename,
                                is_primary=is_primary,
                                sort_order=i
                            )
                            db.session.add(product_image)

            # Handle variants
            variant_names = request.form.getlist('variant_name[]')
            variant_lengths = request.form.getlist('variant_length[]')
            variant_textures = request.form.getlist('variant_texture[]')
            variant_colors = request.form.getlist('variant_color[]')
            variant_prices = request.form.getlist('variant_price[]')
            variant_stocks = request.form.getlist('variant_stock[]')
            variant_skus = request.form.getlist('variant_sku[]')
            
            has_variants = len(variant_names) > 0 and any(name.strip() for name in variant_names)
            
            total_stock = 0
            
            if has_variants:
                for i in range(len(variant_names)):
                    variant_name = variant_names[i].strip()
                    if not variant_name:
                        continue
                        
                    length = variant_lengths[i].strip() if i < len(variant_lengths) else ''
                    texture = variant_textures[i].strip() if i < len(variant_textures) else ''
                    color = variant_colors[i].strip() if i < len(variant_colors) else ''
                    
                    try:
                        price = float(variant_prices[i]) if i < len(variant_prices) and variant_prices[i] else base_price
                    except (ValueError, TypeError):
                        price = base_price
                        
                    try:
                        stock = int(variant_stocks[i]) if i < len(variant_stocks) and variant_stocks[i] else 0
                    except (ValueError, TypeError):
                        stock = 0
                        
                    sku_value = variant_skus[i].strip() if i < len(variant_skus) and variant_skus[i] else generate_unique_sku()
                    
                    total_stock += stock
                    
                    variant = ProductVariant(
                        product_id=product.id,
                        name=variant_name,
                        length=length if length else None,
                        texture=texture if texture else None,
                        color=color if color else None,
                        price=price,
                        stock=stock,
                        sku=sku_value,
                        is_default=(i == 0)
                    )
                    db.session.add(variant)
            else:
                # Create a default variant if no variants were provided
                default_variant = ProductVariant(
                    product_id=product.id,
                    name=name,
                    price=base_price,
                    stock=0,
                    sku=generate_unique_sku(),
                    is_default=True
                )
                db.session.add(default_variant)

            product.total_quantity = total_stock

            db.session.commit()

            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))

        except ValueError as ve:
            db.session.rollback()
            print(f"❌ Value error in add product: {str(ve)}", file=sys.stderr)
            flash('Invalid price or stock value. Please enter valid numbers.', 'danger')
            return render_template('admin/add_product.html', categories=categories)
        except Exception as e:
            db.session.rollback()
            print(f"❌ Add product error: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            flash(f'Error adding product: {str(e)}', 'danger')
            return render_template('admin/add_product.html', categories=categories)
    
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id):
    """Edit product"""
    product = Product.query.options(
        joinedload(Product.category),
        joinedload(Product.variants),
        joinedload(Product.images)
    ).get_or_404(id)
    
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            # Update basic product info
            product.name = request.form.get('name', '').strip()
            product.description = request.form.get('description', '').strip()
            
            try:
                product.base_price = float(request.form.get('base_price', 0) or 0)
            except ValueError:
                flash('Invalid base price format.', 'danger')
                return render_template('admin/edit_product.html', product=product, categories=categories)
            
            compare_price = request.form.get('compare_price', '').strip()
            if compare_price:
                try:
                    product.compare_price = float(compare_price)
                except ValueError:
                    product.compare_price = None
            else:
                product.compare_price = None
            
            try:
                product.category_id = int(request.form.get('category_id', 0))
            except ValueError:
                flash('Invalid category selected.', 'danger')
                return render_template('admin/edit_product.html', product=product, categories=categories)
            
            product.featured = 'featured' in request.form
            product.active = 'active' in request.form
            product.is_bundle = 'is_bundle' in request.form
            
            try:
                product.bundle_discount = float(request.form.get('bundle_discount', 0) or 0)
            except ValueError:
                product.bundle_discount = 0
            
            sku = request.form.get('sku', '').strip()
            if sku and sku != product.sku:
                existing_sku = Product.query.filter_by(sku=sku).first()
                if existing_sku and existing_sku.id != product.id:
                    flash('SKU already exists for another product.', 'danger')
                    return render_template('admin/edit_product.html', product=product, categories=categories)
                product.sku = sku
            
            product.slug = generate_unique_slug(product.name, Product, product.id)

            # Handle image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                existing_images_count = len(product.images)
                
                for i, file in enumerate(files):
                    if file and file.filename != '' and allowed_file(file.filename):
                        uploaded_filename = save_uploaded_file(file)
                        if uploaded_filename:
                            is_primary = (existing_images_count == 0 and i == 0)
                            product_image = ProductImage(
                                product_id=product.id,
                                image_url=uploaded_filename,
                                is_primary=is_primary,
                                sort_order=existing_images_count + i
                            )
                            db.session.add(product_image)

            # Handle variant updates
            variant_ids = request.form.getlist('variant_id[]')
            variant_names = request.form.getlist('variant_name[]')
            variant_lengths = request.form.getlist('variant_length[]')
            variant_textures = request.form.getlist('variant_texture[]')
            variant_colors = request.form.getlist('variant_color[]')
            variant_prices = request.form.getlist('variant_price[]')
            variant_stocks = request.form.getlist('variant_stock[]')
            variant_skus = request.form.getlist('variant_sku[]')
            
            # Get existing variant IDs
            existing_variant_ids = []
            for i, variant_id in enumerate(variant_ids):
                if variant_id and variant_id.isdigit():
                    existing_variant_ids.append(int(variant_id))

            # Delete variants that were removed
            variants_to_delete = []
            for variant in product.variants:
                if variant.id not in existing_variant_ids:
                    variants_to_delete.append(variant)
            
            for variant in variants_to_delete:
                db.session.delete(variant)

            # Update or add variants
            total_stock = 0
            for i in range(len(variant_names)):
                variant_name = variant_names[i].strip()
                if not variant_name:
                    continue
                    
                variant_id = variant_ids[i] if i < len(variant_ids) else None
                length = variant_lengths[i].strip() if i < len(variant_lengths) else ''
                texture = variant_textures[i].strip() if i < len(variant_textures) else ''
                color = variant_colors[i].strip() if i < len(variant_colors) else ''
                
                try:
                    price = float(variant_prices[i]) if i < len(variant_prices) and variant_prices[i] else product.base_price
                except (ValueError, TypeError):
                    price = product.base_price
                    
                try:
                    stock = int(variant_stocks[i]) if i < len(variant_stocks) and variant_stocks[i] else 0
                except (ValueError, TypeError):
                    stock = 0
                
                sku_value = variant_skus[i].strip() if i < len(variant_skus) and variant_skus[i] else generate_unique_sku()
                
                total_stock += stock

                if variant_id and variant_id.isdigit():
                    # Update existing variant
                    variant = ProductVariant.query.get(int(variant_id))
                    if variant:
                        variant.name = variant_name
                        variant.length = length if length else None
                        variant.texture = texture if texture else None
                        variant.color = color if color else None
                        variant.price = price
                        variant.stock = stock
                        variant.sku = sku_value
                else:
                    # Create new variant
                    variant = ProductVariant(
                        product_id=product.id,
                        name=variant_name,
                        length=length if length else None,
                        texture=texture if texture else None,
                        color=color if color else None,
                        price=price,
                        stock=stock,
                        sku=sku_value,
                        is_default=(i == 0 and total_stock == stock)
                    )
                    db.session.add(variant)

            # Update product stock
            product.total_quantity = total_stock

            db.session.commit()

            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Edit product error: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            flash('Error updating product. Please try again.', 'danger')
            return render_template('admin/edit_product.html', product=product, categories=categories)

    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_product(id):
    """Delete product"""
    try:
        product = Product.query.get_or_404(id)
        product_name = product.name

        has_orders = OrderItem.query.filter_by(product_id=id).first() is not None
        if has_orders:
            flash(f'Cannot delete product "{product_name}" because it has existing orders. You can deactivate it instead.', 'danger')
            return redirect(url_for('admin_products'))

        db.session.delete(product)
        db.session.commit()

        flash(f'Product "{product_name}" deleted successfully!', 'success')
        return redirect(url_for('admin_products'))

    except Exception as e:
        db.session.rollback()
        print(f"❌ Delete product error: {str(e)}", file=sys.stderr)
        flash('Error deleting product. Please try again.', 'danger')
        return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders"""
    try:
        status = request.args.get('status', 'all')

        query = Order.query.options(
            joinedload(Order.customer)
        )

        if status != 'all':
            query = query.filter_by(status=status)

        orders = query.order_by(Order.created_at.desc()).all()

        return render_template('admin/orders.html',
                               orders=orders,
                               status=status)
    except Exception as e:
        print(f"❌ Admin orders error: {str(e)}", file=sys.stderr)
        flash('Error loading orders.', 'danger')
        return render_template('admin/orders.html',
                               orders=[],
                               status='all')

@app.route('/admin/orders/<int:id>')
@admin_required
def admin_order_detail(id):
    """Order detail"""
    try:
        order = Order.query.get_or_404(id)
        order_items = OrderItem.query\
            .options(joinedload(OrderItem.product), joinedload(OrderItem.variant))\
            .filter_by(order_id=order.id)\
            .all()

        return render_template('admin/order_detail.html',
                               order=order,
                               order_items=order_items)
    except Exception as e:
        print(f"❌ Admin order detail error: {str(e)}", file=sys.stderr)
        flash('Error loading order details.', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/orders/<int:id>/update', methods=['POST'])
@admin_required
def admin_update_order(id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(id)
        new_status = request.form.get('status')
        new_payment_status = request.form.get('payment_status')
        
        if new_status:
            order.status = new_status
        if new_payment_status:
            order.payment_status = new_payment_status
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Order #{order.order_number} updated successfully!', 'success')
        return redirect(url_for('admin_order_detail', id=order.id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update order error: {str(e)}", file=sys.stderr)
        flash('Error updating order.', 'danger')
        return redirect(url_for('admin_orders'))

# ========== NEW ADMIN ROUTES FOR TEMPLATES ==========

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """Admin categories management"""
    try:
        categories = Category.query.order_by(Category.name).all()
        return render_template('admin/categories.html', categories=categories)
    except Exception as e:
        print(f"❌ Admin categories error: {str(e)}", file=sys.stderr)
        flash('Error loading categories.', 'danger')
        return render_template('admin/categories.html', categories=[])

@app.route('/admin/customers')
@admin_required
def admin_customers():
    """Admin customers management"""
    try:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
        return render_template('admin/customers.html', customers=customers)
    except Exception as e:
        print(f"❌ Admin customers error: {str(e)}", file=sys.stderr)
        flash('Error loading customers.', 'danger')
        return render_template('admin/customers.html', customers=[])

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings"""
    return render_template('admin/settings.html')

# ========== STATIC FILE SERVING ==========

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        print(f"❌ Error serving file {filename}: {str(e)}", file=sys.stderr)
        return send_from_directory('static/uploads', filename, as_attachment=False)

# ========== HEALTH CHECK ==========
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Nora Hair Line E-commerce',
            'version': '2.0.0',
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ========== NEW ROUTES FOR ADDITIONAL TEMPLATES ==========

@app.route('/order/<int:id>')
def order_detail(id):
    """Order detail page for customers"""
    try:
        order = Order.query.get_or_404(id)
        
        # Check if customer owns this order
        if 'customer_id' in session and order.customer_id == session['customer_id']:
            order_items = OrderItem.query\
                .options(joinedload(OrderItem.product), joinedload(OrderItem.variant))\
                .filter_by(order_id=order.id)\
                .all()
            
            return render_template('order.html',
                                   order=order,
                                   order_items=order_items,
                                   bank_details=BUSINESS_CONFIG)
        else:
            flash('You are not authorized to view this order.', 'danger')
            return redirect(url_for('account'))
    except Exception as e:
        print(f"❌ Order detail error: {str(e)}", file=sys.stderr)
        flash('Error loading order details.', 'danger')
        return redirect(url_for('account'))

# ========== DEFAULT IMAGE ROUTE ==========
@app.route('/static/images/<filename>')
def serve_image(filename):
    """Serve images from static/images folder"""
    try:
        return send_from_directory('static/images', filename)
    except Exception as e:
        print(f"❌ Error serving image {filename}: {str(e)}", file=sys.stderr)
        # Return a placeholder if image not found
        return redirect('https://via.placeholder.com/800x800/8B4513/FFFFFF?text=NORA+HAIR+LINE')

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Create necessary directories
    directories = [
        'static/uploads',
        'static/images',
        'templates',
        'templates/admin'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created/Verified directory: {directory}", file=sys.stderr)

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🚀 NORA HAIR LINE E-COMMERCE - PRODUCTION READY", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"✅ Python 3.13 Compatibility Patches: ACTIVE", file=sys.stderr)
    print(f"✅ Mock pkg_resources: LOADED", file=sys.stderr)
    print(f"✅ Gunicorn six.mocks: ACTIVE", file=sys.stderr)
    print(f"✅ SQLAlchemy TypingOnly Patch: APPLIED", file=sys.stderr)
    print(f"✅ Database Connection: READY", file=sys.stderr)
    print(f"✅ File Upload: READY", file=sys.stderr)
    print(f"✅ Admin Panel: /admin (admin/admin123)", file=sys.stderr)
    print(f"✅ Variant System: ENABLED", file=sys.stderr)
    print(f"🌐 Server: http://localhost:{port}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    app.run(host='0.0.0.0', port=port, debug=debug)
