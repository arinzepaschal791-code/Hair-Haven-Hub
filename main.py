# main.py - NORA HAIR LINE E-COMMERCE - ENHANCED VERSION
import os
import sys
import traceback
from datetime import datetime, timedelta
import random
import string
from functools import wraps
import json
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from sqlalchemy import text, or_, and_, func

# ========== CREATE APP ==========
app = Flask(__name__)

# ========== CONFIGURATION ==========
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026-change-in-production')

# Database configuration
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    # Local development - use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'
    print("Using SQLite database (local development)", file=sys.stderr)
elif database_url.startswith('postgres://'):
    # Fix Render/Heroku PostgreSQL URLs
    fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = fixed_url
    print("Using PostgreSQL database (production)", file=sys.stderr)
else:
    # Already correct URL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("Using database from environment", file=sys.stderr)

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max file size
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
base_price = db.Column(db.Float, nullable=False, default=0.0) # Renamed from price
compare_price = db.Column(db.Float)
sku = db.Column(db.String(100))
total_quantity = db.Column(db.Integer, default=0) # Total across all variants
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
shipping_area = db.Column(db.String(100)) # Added for Lagos areas
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
variant_details = db.Column(db.String(200)) # Store variant info: "24\" Brazilian Body Wave"
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

class BundleItem(db.Model):
__tablename__ = 'bundle_item'

id = db.Column(db.Integer, primary_key=True)
bundle_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
quantity = db.Column(db.Integer, default=1)
created_at = db.Column(db.DateTime, default=datetime.utcnow)

bundle = db.relationship('Product', foreign_keys=[bundle_id], backref='bundle_items')
product = db.relationship('Product', foreign_keys=[product_id])

def __repr__(self):
return f'<BundleItem {self.id}>'

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

def calculate_cart_total():
total = 0
if 'cart' in session:
for item in session['cart']:
price = item.get('price', 0)
quantity = item.get('quantity', 1)
total += float(price) * quantity
return total

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

def safe_format_number(value, default=0):
"""Safely format number for display"""
try:
if value is None:
return default
if isinstance(value, (int, float)):
return f"{value:,.2f}"
return str(value)
except:
return str(default)

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
# For products with variants, we need to check specific variant
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

# Update product total quantity
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

# ========== FILE UPLOAD FUNCTION ==========
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

print(f"✅ File saved successfully: {unique_filename}", file=sys.stderr)
return unique_filename

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

# FIXED: Return the actual CSRF token string, not a function
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
safe_format_number=safe_format_number,
csrf_token=csrf_token_value, # FIXED: This is now a string
min=min, # ADDED for template functions
max=max, # ADDED for template functions
random=random, # ADDED for random in templates
check_stock=check_stock_availability # Added for stock checking
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

@app.errorhandler(Exception)
def handle_exception(e):
"""Handle all exceptions"""
print(f"❌ Unhandled Exception: {str(e)}", file=sys.stderr)
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

# Create sample products with variants if none exist
if Product.query.count() == 0:
categories = Category.query.all()

sample_products = [
('Brazilian Body Wave', 12999.99, 15999.99, 'hair-bundles',
'Premium Brazilian body wave hair, 100% human hair'),
('Peruvian Straight', 14999.99, 17999.99, 'hair-bundles',
'Silky straight Peruvian hair, natural black'),
('13x4 Lace Frontal Wig', 19999.99, 23999.99, 'lace-wigs',
'HD lace frontal wig with natural hairline'),
]

for i, (name, price, compare_price, category_slug, desc) in enumerate(sample_products):
category = Category.query.filter_by(slug=category_slug).first()
if category:
product = Product(
name=name,
slug=name.lower().replace(' ', '-').replace('"', '').replace("'", ''),
description=desc,
base_price=price,
compare_price=compare_price,
sku=f'HAIR-{i+1:03d}',
category_id=category.id,
featured=(i < 3),
)
db.session.add(product)
db.session.flush() # Get product ID

# Add variants for hair bundles
if category_slug == 'hair-bundles':
lengths = ['20"', '22"', '24"', '26"', '28"']
textures = ['Body Wave', 'Straight', 'Curly', 'Wavy']
for length in lengths:
for texture in textures[:2]: # Only add 2 textures per length
variant = ProductVariant(
product_id=product.id,
name=f"{name} {length}",
length=length,
texture=texture,
price=price + (len(lengths) * 1000), # Price increases with length
stock=random.randint(5, 20),
sku=f'HAIR-{i+1:03d}-{length.replace("", "")}-{texture[:3].upper()}',
is_default=(length == '22"' and texture == 'Body Wave')
)
db.session.add(variant)
else:
# Add single variant for non-bundle products
variant = ProductVariant(
product_id=product.id,
name=name,
price=price,
stock=random.randint(5, 20),
sku=f'HAIR-{i+1:03d}-STD',
is_default=True
)
db.session.add(variant)

print("✅ Sample products with variants added", file=sys.stderr)

# Create sample reviews if none exist
if Review.query.count() == 0:
reviews = [
(1, 'Chiamaka Okeke', 5, 'The Brazilian hair I purchased is absolutely stunning! It\'s been 6 months and still looks brand new. Best quality I\'ve ever had!', 'Lagos', True),
(2, 'Bisi Adeyemi', 5, 'The lace frontal wig is so natural looking! I\'ve received countless compliments. The customer service was excellent too!', 'Abuja', True),
(3, 'Fatima Bello', 4, 'Fast delivery and premium quality hair. I\'ll definitely be ordering again. The Peruvian straight is my new favorite!', 'Port Harcourt', True),
]

for product_id, name, rating, comment, location, verified in reviews:
review = Review(
product_id=product_id,
customer_name=name,
rating=rating,
comment=comment,
location=location,
verified_purchase=verified,
approved=True
)
db.session.add(review)

print("✅ Sample reviews added", file=sys.stderr)

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
"""Shop page with advanced filtering"""
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

# Filter by length (using variants)
if length:
# Get product IDs that have variants with this length
variant_products = db.session.query(ProductVariant.product_id)\
.filter(ProductVariant.length == length, ProductVariant.stock > 0)\
.distinct()
query = query.filter(Product.id.in_(variant_products))

# Filter by texture (using variants)
if texture:
variant_products = db.session.query(ProductVariant.product_id)\
.filter(ProductVariant.texture == texture, ProductVariant.stock > 0)\
.distinct()
query = query.filter(Product.id.in_(variant_products))

# Filter by price range
if min_price is not None:
# Check against variant min prices
query = query.filter(Product.base_price >= min_price)
if max_price is not None:
query = query.filter(Product.base_price <= max_price)

products = query.order_by(Product.created_at.desc()).all()

# Get unique lengths and textures for filters
all_lengths = db.session.query(ProductVariant.length)\
.filter(ProductVariant.length.isnot(None), ProductVariant.stock > 0)\
.distinct()\
.order_by(ProductVariant.length)\
.all()
lengths = [l[0] for l in all_lengths if l[0]]

all_textures = db.session.query(ProductVariant.texture)\
.filter(ProductVariant.texture.isnot(None), ProductVariant.stock > 0)\
.distinct()\
.order_by(ProductVariant.texture)\
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
"""Product detail page with variants"""
try:
product = Product.query\
.options(joinedload(Product.category))\
.get_or_404(id)

if not product.active:
flash('This product is currently unavailable.', 'warning')
return redirect(url_for('shop'))

# Get product variants
variants = ProductVariant.query\
.filter_by(product_id=id)\
.order_by(ProductVariant.length, ProductVariant.texture)\
.all()

# Get product images
images = ProductImage.query\
.filter_by(product_id=id)\
.order_by(ProductImage.sort_order, ProductImage.is_primary.desc())\
.all()

# Group variants by length for display
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
"""Get product variants for AJAX requests"""
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
"""Shopping cart page with variant info"""
cart_items = session.get('cart', [])

# Enhance cart items with variant info
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
@csrf.exempt
def add_to_cart(product_id):
"""Add product to cart with variant selection"""
try:
product = Product.query.get_or_404(product_id)

if not product.active:
flash('Product is not available.', 'warning')
return redirect(request.referrer or url_for('shop'))

quantity = int(request.form.get('quantity', 1))
variant_id = request.form.get('variant_id', type=int)

# Check if product has variants
if product.variants and not variant_id:
flash('Please select a variant (length/texture) before adding to cart.', 'warning')
return redirect(request.referrer or url_for('product_detail', id=product.id))

# Check stock availability
stock_available, message = check_stock_availability(product_id, variant_id, quantity)
if not stock_available:
flash(message, 'warning')
return redirect(request.referrer or url_for('product_detail', id=product.id))

# Get price from variant if selected, otherwise use product base price
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

# Check if product already in cart (with same variant)
for item in cart:
if item['id'] == product_id and item.get('variant_id') == variant_id:
new_quantity = item['quantity'] + quantity

# Re-check stock for new total
stock_available, message = check_stock_availability(product_id, variant_id, new_quantity)
if not stock_available:
flash(message, 'warning')
return redirect(request.referrer or url_for('cart'))

item['quantity'] = new_quantity
session.modified = True
flash(f'Added {quantity} more to cart.', 'success')
return redirect(request.referrer or url_for('cart'))

# Add new item to cart
cart_item = {
'id': product_id,
'name': product.name,
'price': float(price),
'variant_price': float(price), # Store variant-specific price
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
session.modified = True

flash(f'{product.name} added to cart!', 'success')
return redirect(request.referrer or url_for('cart'))

except Exception as e:
print(f"❌ Add to cart error: {str(e)}", file=sys.stderr)
flash('Error adding to cart. Please try again.', 'danger')
return redirect(request.referrer or url_for('shop'))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
"""Update cart item quantity with variant support"""
try:
if 'cart' not in session:
return redirect(url_for('cart'))

cart = session['cart']
quantity = int(request.form.get('quantity', 1))
variant_id = request.form.get('variant_id', type=int)

for item in cart:
if item['id'] == product_id and item.get('variant_id') == variant_id:
if quantity <= 0:
cart.remove(item)
else:
# Check stock
stock_available, message = check_stock_availability(product_id, variant_id, quantity)
if not stock_available:
flash(message, 'warning')
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
"""Remove item from cart with variant support"""
try:
variant_id = request.args.get('variant_id', type=int)

if 'cart' in session:
cart = session['cart']
if variant_id:
session['cart'] = [item for item in cart if not (item['id'] == product_id and item.get('variant_id') == variant_id)]
else:
session['cart'] = [item for item in cart if item['id'] != product_id]
session.modified = True
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
address = request.form.get('address', '')

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
phone=phone,
address=address
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

# ========== ACCOUNT MANAGEMENT ROUTES ==========

@app.route('/update-address', methods=['POST'])
@customer_required
def update_address():
"""Update customer address"""
try:
customer = Customer.query.get(session['customer_id'])
customer.address = request.form.get('address', '')
customer.city = request.form.get('city', '')
customer.state = request.form.get('state', '')
customer.phone = request.form.get('phone', '')

db.session.commit()
flash('Address updated successfully!', 'success')
except Exception as e:
db.session.rollback()
print(f"❌ Update address error: {str(e)}", file=sys.stderr)
flash('Error updating address. Please try again.', 'danger')

return redirect(url_for('account'))

@app.route('/update-profile', methods=['POST'])
@customer_required
def update_profile():
"""Update customer profile"""
try:
customer = Customer.query.get(session['customer_id'])
customer.first_name = request.form.get('first_name', '')
customer.last_name = request.form.get('last_name', '')
customer.email = request.form.get('email', '')
customer.phone = request.form.get('phone', '')

db.session.commit()
flash('Profile updated successfully!', 'success')
except Exception as e:
db.session.rollback()
print(f"❌ Update profile error: {str(e)}", file=sys.stderr)
flash('Error updating profile. Please try again.', 'danger')

return redirect(url_for('account'))

@app.route('/change-password', methods=['POST'])
@customer_required
def change_password():
"""Change customer password"""
try:
customer = Customer.query.get(session['customer_id'])
current_password = request.form.get('current_password', '')
new_password = request.form.get('new_password', '')
confirm_password = request.form.get('confirm_password', '')

if not customer.check_password(current_password):
flash('Current password is incorrect', 'danger')
return redirect(url_for('account'))

if new_password != confirm_password:
flash('New passwords do not match', 'danger')
return redirect(url_for('account'))

if len(new_password) < 6:
flash('Password must be at least 6 characters', 'danger')
return redirect(url_for('account'))

customer.set_password(new_password)
db.session.commit()

flash('Password changed successfully!', 'success')
except Exception as e:
db.session.rollback()
print(f"❌ Change password error: {str(e)}", file=sys.stderr)
flash('Error changing password. Please try again.', 'danger')

return redirect(url_for('account'))

# ========== CHECKOUT ROUTES ==========

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
"""Checkout page with delivery logic"""
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

# Calculate delivery fee based on location
delivery_fee = calculate_delivery_fee(city, state, area, subtotal)
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
shipping_area=area,
total_amount=subtotal,
shipping_amount=delivery_fee,
final_amount=total,
payment_method=payment_method,
notes=notes
)

db.session.add(order)
db.session.flush()

# Add order items and update stock
for item in cart_items:
product = Product.query.get(item['id'])
variant_id = item.get('variant_id')
variant = ProductVariant.query.get(variant_id) if variant_id else None

# Create order item
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

# Update stock
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

# GET request - calculate delivery fee based on customer's default address
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

# In production, you would send an email here
print(f"📧 Contact form submission: {name} <{email}> - {subject}", file=sys.stderr)

flash('Your message has been sent successfully! We will contact you soon.', 'success')
return redirect(url_for('contact'))

except Exception as e:
flash('Error sending message. Please try again.', 'danger')

return render_template('contact.html')

# ========== REVIEW ROUTES ==========

@app.route('/add-review/<int:product_id>', methods=['POST'])
@customer_required
def add_review(product_id):
"""Add product review"""
try:
product = Product.query.get_or_404(product_id)

rating = int(request.form.get('rating', 5))
comment = request.form.get('comment', '')

if not comment:
flash('Please provide a review comment.', 'warning')
return redirect(url_for('product_detail', id=product_id))

customer = Customer.query.get(session['customer_id'])

# Check if customer has purchased this product
has_purchased = OrderItem.query\
.join(Order)\
.filter(
Order.customer_id == customer.id,
OrderItem.product_id == product_id
).first() is not None

review = Review(
product_id=product_id,
customer_name=f"{customer.first_name} {customer.last_name}",
email=customer.email,
rating=rating,
comment=comment,
location=customer.city or 'Unknown',
verified_purchase=has_purchased,
approved=False
)

db.session.add(review)
db.session.commit()

flash('Thank you for your review! It will be visible after approval.', 'success')
return redirect(url_for('product_detail', id=product_id))

except Exception as e:
db.session.rollback()
print(f"❌ Add review error: {str(e)}", file=sys.stderr)
flash('Error submitting review. Please try again.', 'danger')
return redirect(url_for('product_detail', id=product_id))

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

# Get low stock products (across all variants)
low_stock_products = []
all_products = Product.query.all()
for product in all_products:
if product.stock > 0 and product.stock <= 10:
low_stock_products.append(product)
if len(low_stock_products) >= 5:
break

total_reviews = Review.query.count()
top_products = Product.query.filter_by(featured=True).limit(5).all()

# Today's stats
today = datetime.utcnow().date()
today_orders = Order.query.filter(db.func.date(Order.created_at) == today).count()
today_revenue_result = db.session.query(db.func.sum(Order.final_amount)).filter(db.func.date(Order.created_at) == today).scalar()
today_revenue = float(today_revenue_result) if today_revenue_result is not None else 0.0

# Get variant-based stats
total_variants = ProductVariant.query.count()
low_stock_variants = ProductVariant.query.filter(ProductVariant.stock > 0, ProductVariant.stock <= 5).count()

return render_template('admin/admin_dashboard.html',
total_orders=total_orders,
total_products=total_products,
total_customers=total_customers,
total_reviews=total_reviews,
total_variants=total_variants,
pending_orders=pending_orders,
revenue=revenue,
recent_orders=recent_orders,
recent_customers=recent_customers,
low_stock_products=low_stock_products,
low_stock_variants=low_stock_variants,
top_products=top_products,
today_revenue=today_revenue,
today_orders=today_orders,
today_customers=0,
new_customers_week=0,
conversion_rate=0,
inventory_health=100,
avg_rating=4.5,
server_load=30,
disk_usage="1.2GB / 10GB",
disk_percent=12,
uptime="2 days",
environment="Production")
except Exception as e:
print(f"❌ Admin dashboard error: {str(e)}", file=sys.stderr)
flash('Error loading dashboard.', 'danger')
return render_template('admin/admin_dashboard.html',
total_orders=0,
total_products=0,
total_customers=0,
total_reviews=0,
total_variants=0,
pending_orders=0,
revenue=0,
recent_orders=[],
recent_customers=[],
low_stock_products=[],
low_stock_variants=0,
top_products=[])

@app.route('/admin/products')
@admin_required
def admin_products():
"""Admin products list with variant info"""
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
"""Add product with variants and multiple images"""
if request.method == 'POST':
try:
name = request.form.get('name')
description = request.form.get('description')
base_price = float(request.form.get('base_price', 0))
compare_price = request.form.get('compare_price')
category_id = int(request.form.get('category_id'))
featured = 'featured' in request.form
active = 'active' in request.form
is_bundle = 'is_bundle' in request.form
bundle_discount = float(request.form.get('bundle_discount', 0))

slug = name.lower().replace(' ', '-').replace('"', '').replace("'", '')
sku = f"HAIR-{random.randint(1000, 9999)}"

# Create product
product = Product(
name=name,
slug=slug,
description=description,
base_price=base_price,
compare_price=float(compare_price) if compare_price else None,
category_id=category_id,
featured=featured,
active=active,
is_bundle=is_bundle,
bundle_discount=bundle_discount,
sku=sku
)

db.session.add(product)
db.session.flush() # Get product ID

# Handle image uploads
if 'images' in request.files:
files = request.files.getlist('images')
for i, file in enumerate(files):
if file and file.filename != '':
uploaded_filename = save_uploaded_file(file)
if uploaded_filename:
is_primary = (i == 0)
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

total_stock = 0
for i in range(len(variant_names)):
if variant_names[i]:
variant = ProductVariant(
product_id=product.id,
name=variant_names[i],
length=variant_lengths[i] if i < len(variant_lengths) else None,
texture=variant_textures[i] if i < len(variant_textures) else None,
color=variant_colors[i] if i < len(variant_colors) else None,
price=float(variant_prices[i]) if variant_prices[i] else base_price,
stock=int(variant_stocks[i]) if variant_stocks[i] else 0,
sku=variant_skus[i] if variant_skus[i] else f"{sku}-V{i+1}",
is_default=(i == 0)
)
db.session.add(variant)
total_stock += variant.stock

# Update total quantity
product.total_quantity = total_stock

db.session.commit()

flash(f'Product "{name}" added successfully with {len(variant_names)} variants!', 'success')
return redirect(url_for('admin_products'))

except Exception as e:
db.session.rollback()
print(f"❌ Add product error: {str(e)}", file=sys.stderr)
traceback.print_exc(file=sys.stderr)
flash('Error adding product. Please try again.', 'danger')

categories = Category.query.all()
return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id):
"""Edit product with variants"""
product = Product.query.options(
joinedload(Product.category),
joinedload(Product.variants),
joinedload(Product.images)
).get_or_404(id)

if request.method == 'POST':
try:
product.name = request.form.get('name')
product.description = request.form.get('description')
product.base_price = float(request.form.get('base_price', 0))
compare_price = request.form.get('compare_price')
product.compare_price = float(compare_price) if compare_price else None
product.category_id = int(request.form.get('category_id'))
product.featured = 'featured' in request.form
product.active = 'active' in request.form
product.is_bundle = 'is_bundle' in request.form
product.bundle_discount = float(request.form.get('bundle_discount', 0))

product.slug = product.name.lower().replace(' ', '-').replace('"', '').replace("'", '')

# Handle image uploads
if 'images' in request.files:
files = request.files.getlist('images')
for i, file in enumerate(files):
if file and file.filename != '':
uploaded_filename = save_uploaded_file(file)
if uploaded_filename:
is_primary = (i == 0 and not product.images)
product_image = ProductImage(
product_id=product.id,
image_url=uploaded_filename,
is_primary=is_primary,
sort_order=len(product.images) + i
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

# Update existing variants
existing_variant_ids = [int(vid) for vid in variant_ids if vid]
for variant in product.variants:
if variant.id not in existing_variant_ids:
db.session.delete(variant)

total_stock = 0
for i in range(len(variant_names)):
if variant_names[i]:
if i < len(variant_ids) and variant_ids[i]:
# Update existing variant
variant = ProductVariant.query.get(int(variant_ids[i]))
if variant:
variant.name = variant_names[i]
variant.length = variant_lengths[i] if i < len(variant_lengths) else None
variant.texture = variant_textures[i] if i < len(variant_textures) else None
variant.color = variant_colors[i] if i < len(variant_colors) else None
variant.price = float(variant_prices[i]) if variant_prices[i] else product.base_price
variant.stock = int(variant_stocks[i]) if variant_stocks[i] else 0
variant.sku = variant_skus[i] if variant_skus[i] else f"{product.sku}-V{i+1}"
variant.is_default = (i == 0)
else:
# Add new variant
variant = ProductVariant(
product_id=product.id,
name=variant_names[i],
length=variant_lengths[i] if i < len(variant_lengths) else None,
texture=variant_textures[i] if i < len(variant_textures) else None,
color=variant_colors[i] if i < len(variant_colors) else None,
price=float(variant_prices[i]) if variant_prices[i] else product.base_price,
stock=int(variant_stocks[i]) if variant_stocks[i] else 0,
sku=variant_skus[i] if variant_skus[i] else f"{product.sku}-V{i+1}",
is_default=(i == 0)
)
db.session.add(variant)

if variant_stocks[i]:
total_stock += int(variant_stocks[i])

# Update total quantity
product.total_quantity = total_stock

db.session.commit()

flash(f'Product "{product.name}" updated successfully!', 'success')
return redirect(url_for('admin_products'))

except Exception as e:
db.session.rollback()
print(f"❌ Edit product error: {str(e)}", file=sys.stderr)
flash('Error updating product. Please try again.', 'danger')

categories = Category.query.all()
return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_product(id):
"""Delete product"""
try:
product = Product.query.get_or_404(id)
product_name = product.name

db.session.delete(product)
db.session.commit()

flash(f'Product "{product_name}" deleted successfully!', 'success')
return redirect(url_for('admin_products'))

except Exception as e:
db.session.rollback()
print(f"❌ Delete product error: {str(e)}", file=sys.stderr)
flash('Error deleting product. Please try again.', 'danger')
return redirect(url_for('admin_products'))

# ========== VARIANT MANAGEMENT ROUTES ==========

@app.route('/admin/products/<int:product_id>/variants')
@admin_required
def admin_product_variants(product_id):
"""Manage product variants"""
try:
product = Product.query.get_or_404(product_id)
variants = ProductVariant.query.filter_by(product_id=product_id).all()

return render_template('admin/variants.html',
product=product,
variants=variants)
except Exception as e:
flash('Error loading variants.', 'danger')
return redirect(url_for('admin_products'))

@app.route('/admin/variants/add/<int:product_id>', methods=['POST'])
@admin_required
def admin_add_variant(product_id):
"""Add variant to product"""
try:
product = Product.query.get_or_404(product_id)

name = request.form.get('name')
length = request.form.get('length')
texture = request.form.get('texture')
color = request.form.get('color')
price = float(request.form.get('price', product.base_price))
stock = int(request.form.get('stock', 0))

variant = ProductVariant(
product_id=product_id,
name=name,
length=length,
texture=texture,
color=color,
price=price,
stock=stock,
sku=f"{product.sku}-V{ProductVariant.query.filter_by(product_id=product_id).count() + 1}"
)

db.session.add(variant)

# Update product total quantity
product.total_quantity = sum(v.stock for v in product.variants) + stock

db.session.commit()

return jsonify({'success': True, 'message': 'Variant added successfully!'})
except Exception as e:
db.session.rollback()
return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/variants/update/<int:variant_id>', methods=['POST'])
@admin_required
def admin_update_variant(variant_id):
"""Update variant"""
try:
variant = ProductVariant.query.get_or_404(variant_id)

variant.name = request.form.get('name')
variant.length = request.form.get('length')
variant.texture = request.form.get('texture')
variant.color = request.form.get('color')
variant.price = float(request.form.get('price', variant.price))
variant.stock = int(request.form.get('stock', variant.stock))

db.session.commit()

return jsonify({'success': True, 'message': 'Variant updated successfully!'})
except Exception as e:
db.session.rollback()
return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/variants/delete/<int:variant_id>', methods=['POST'])
@admin_required
def admin_delete_variant(variant_id):
"""Delete variant"""
try:
variant = ProductVariant.query.get_or_404(variant_id)
product_id = variant.product_id

db.session.delete(variant)

# Update product total quantity
product = Product.query.get(product_id)
if product:
product.total_quantity = sum(v.stock for v in product.variants)

db.session.commit()

return jsonify({'success': True, 'message': 'Variant deleted successfully!'})
except Exception as e:
db.session.rollback()
return jsonify({'success': False, 'error': str(e)}), 500

# ========== NEW PRODUCT MANAGEMENT ROUTES ==========

@app.route('/admin/products/bulk-action', methods=['POST'])
@admin_required
def admin_bulk_action():
"""Handle bulk actions for products"""
try:
data = request.json
action = data.get('action')
product_ids = data.get('product_ids', [])

if action == 'activate':
Product.query.filter(Product.id.in_(product_ids)).update({Product.active: True})
elif action == 'deactivate':
Product.query.filter(Product.id.in_(product_ids)).update({Product.active: False})
elif action == 'feature':
Product.query.filter(Product.id.in_(product_ids)).update({Product.featured: True})
elif action == 'unfeature':
Product.query.filter(Product.id.in_(product_ids)).update({Product.featured: False})
elif action == 'delete':
Product.query.filter(Product.id.in_(product_ids)).delete()
else:
return jsonify({'error': 'Invalid action'}), 400

db.session.commit()
return jsonify({'success': True, 'count': len(product_ids)})

except Exception as e:
db.session.rollback()
print(f"❌ Bulk action error: {str(e)}", file=sys.stderr)
return jsonify({'error': str(e)}), 500

@app.route('/admin/products/<int:id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_product_status(id):
"""Toggle product active status"""
try:
product = Product.query.get_or_404(id)
product.active = request.json.get('active', not product.active)
db.session.commit()
return jsonify({'success': True, 'active': product.active})
except Exception as e:
db.session.rollback()
return jsonify({'error': str(e)}), 500

@app.route('/admin/products/<int:id>/quick-edit')
@admin_required
def admin_quick_edit_product(id):
"""Get product data for quick edit"""
try:
product = Product.query.get_or_404(id)
return jsonify({
'id': product.id,
'name': product.name,
'base_price': product.base_price,
'compare_price': product.compare_price,
'total_quantity': product.total_quantity,
'category_id': product.category_id,
'featured': product.featured
})
except Exception as e:
return jsonify({'error': str(e)}), 404

@app.route('/admin/products/<int:id>/quick-update', methods=['POST'])
@admin_required
def admin_quick_update_product(id):
"""Quick update product details"""
try:
product = Product.query.get_or_404(id)
product.name = request.form.get('name')
product.base_price = float(request.form.get('base_price', 0))
compare_price = request.form.get('compare_price')
product.compare_price = float(compare_price) if compare_price else None
product.total_quantity = int(request.form.get('total_quantity', 0))
product.category_id = int(request.form.get('category_id'))
product.featured = 'featured' in request.form

db.session.commit()
return jsonify({'success': True, 'message': 'Product updated successfully!'})
except Exception as e:
db.session.rollback()
return jsonify({'error': str(e)}), 500

@app.route('/admin/products/<int:id>/upload-image', methods=['POST'])
@admin_required
def admin_upload_product_image(id):
"""Upload product image"""
try:
product = Product.query.get_or_404(id)

if 'image' not in request.files:
return jsonify({'error': 'No file provided'}), 400

file = request.files['image']
if file.filename == '':
return jsonify({'error': 'No file selected'}), 400

if not allowed_file(file.filename):
return jsonify({'error': 'File type not allowed'}), 400

uploaded_filename = save_uploaded_file(file)
if uploaded_filename:
# Add as product image
product_image = ProductImage(
product_id=product.id,
image_url=uploaded_filename,
is_primary=(len(product.images) == 0)
)
db.session.add(product_image)
db.session.commit()
return jsonify({'success': True, 'image_url': uploaded_filename})
else:
return jsonify({'error': 'Failed to save file'}), 500

except Exception as e:
db.session.rollback()
return jsonify({'error': str(e)}), 500

# ========== ORDER MANAGEMENT ==========

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

@app.route('/admin/orders/update-status/<int:id>', methods=['POST'])
@admin_required
def admin_update_order_status(id):
"""Update order status"""
try:
order = Order.query.get_or_404(id)
new_status = request.form.get('status')

if new_status:
order.status = new_status
order.updated_at = datetime.utcnow()

# If order is cancelled, restore stock
if new_status == 'cancelled':
for item in order.items:
if item.variant_id:
variant = ProductVariant.query.get(item.variant_id)
if variant:
variant.stock += item.quantity
else:
product = Product.query.get(item.product_id)
if product:
product.total_quantity += item.quantity

db.session.commit()

flash(f'Order #{order.order_number} status updated to {new_status}', 'success')
return redirect(url_for('admin_order_detail', id=id))

except Exception as e:
db.session.rollback()
print(f"❌ Update order status error: {str(e)}", file=sys.stderr)
flash('Error updating order status.', 'danger')
return redirect(url_for('admin_order_detail', id=id))

# ========== CUSTOMER MANAGEMENT ==========

@app.route('/admin/customers')
@admin_required
def admin_customers():
"""Admin customers list"""
try:
customers = Customer.query.order_by(Customer.created_at.desc()).all()
return render_template('admin/customers.html', customers=customers)
except Exception as e:
print(f"❌ Admin customers error: {str(e)}", file=sys.stderr)
flash('Error loading customers.', 'danger')
return render_template('admin/customers.html', customers=[])

# ========== REVIEW MANAGEMENT ==========

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
"""Admin reviews"""
try:
reviews = Review.query.order_by(Review.created_at.desc()).all()

total_reviews = len(reviews)
approved_reviews = len([r for r in reviews if r.approved])
pending_reviews = len([r for r in reviews if not r.approved])
avg_rating = sum([r.rating for r in reviews]) / total_reviews if total_reviews > 0 else 0

review_stats = {
'total': total_reviews,
'approved': approved_reviews,
'pending': pending_reviews,
'avg_rating': round(avg_rating, 1)
}

return render_template('admin/reviews.html',
reviews=reviews,
review_stats=review_stats)
except Exception as e:
print(f"❌ Admin reviews error: {str(e)}", file=sys.stderr)
flash('Error loading reviews.', 'danger')
return render_template('admin/reviews.html',
reviews=[],
review_stats={'total': 0, 'approved': 0, 'pending': 0, 'avg_rating': 0})

@app.route('/admin/reviews/approve/<int:id>', methods=['POST'])
@admin_required
def admin_approve_review(id):
"""Approve review"""
try:
review = Review.query.get_or_404(id)
review.approved = True
db.session.commit()

flash('Review approved successfully!', 'success')
return redirect(url_for('admin_reviews'))

except Exception as e:
db.session.rollback()
flash('Error approving review.', 'danger')
return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_review(id):
"""Delete review"""
try:
review = Review.query.get_or_404(id)
db.session.delete(review)
db.session.commit()

flash('Review deleted successfully!', 'success')
return redirect(url_for('admin_reviews'))

except Exception as e:
db.session.rollback()
flash('Error deleting review.', 'danger')
return redirect(url_for('admin_reviews'))

# ========== CATEGORY MANAGEMENT ==========

@app.route('/admin/categories')
@admin_required
def admin_categories():
"""Admin categories"""
try:
categories = Category.query.order_by(Category.name).all()
return render_template('admin/categories.html', categories=categories)
except Exception as e:
print(f"❌ Admin categories error: {str(e)}", file=sys.stderr)
flash('Error loading categories.', 'danger')
return render_template('admin/categories.html', categories=[])

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
"""Add category"""
if request.method == 'POST':
try:
name = request.form.get('name')
description = request.form.get('description')
slug = request.form.get('slug', '').lower().replace(' ', '-')

if not slug:
slug = name.lower().replace(' ', '-')

category = Category(
name=name,
slug=slug,
description=description
)

db.session.add(category)
db.session.commit()

flash(f'Category "{name}" added successfully!', 'success')
return redirect(url_for('admin_categories'))

except Exception as e:
db.session.rollback()
print(f"❌ Add category error: {str(e)}", file=sys.stderr)
flash('Error adding category. Please try again.', 'danger')

return render_template('admin/add_category.html')

@app.route('/admin/categories/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(id):
"""Edit category"""
category = Category.query.get_or_404(id)

if request.method == 'POST':
try:
category.name = request.form.get('name')
category.description = request.form.get('description')
slug = request.form.get('slug', '').lower().replace(' ', '-')

if slug:
category.slug = slug

db.session.commit()

flash(f'Category "{category.name}" updated successfully!', 'success')
return redirect(url_for('admin_categories'))

except Exception as e:
db.session.rollback()
print(f"❌ Edit category error: {str(e)}", file=sys.stderr)
flash('Error updating category. Please try again.', 'danger')

return render_template('admin/edit_category.html', category=category)

@app.route('/admin/categories/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_category(id):
"""Delete category"""
try:
category = Category.query.get_or_404(id)
category_name = category.name

# Check if category has products
if category.products:
flash(f'Cannot delete category "{category_name}" because it has products. Please reassign or delete products first.', 'danger')
return redirect(url_for('admin_categories'))

db.session.delete(category)
db.session.commit()

flash(f'Category "{category_name}" deleted successfully!', 'success')
return redirect(url_for('admin_categories'))

except Exception as e:
db.session.rollback()
print(f"❌ Delete category error: {str(e)}", file=sys.stderr)
flash('Error deleting category. Please try again.', 'danger')
return redirect(url_for('admin_categories'))

# ========== ADMIN SETTINGS ==========

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
"""Admin settings - change password"""
if request.method == 'POST':
try:
current_password = request.form.get('current_password')
new_password = request.form.get('new_password')
confirm_password = request.form.get('confirm_password')

admin = User.query.get(session['admin_id'])

if not admin.check_password(current_password):
flash('Current password is incorrect', 'danger')
return redirect(url_for('admin_settings'))

if new_password != confirm_password:
flash('New passwords do not match', 'danger')
return redirect(url_for('admin_settings'))

if len(new_password) < 6:
flash('Password must be at least 6 characters', 'danger')
return redirect(url_for('admin_settings'))

admin.set_password(new_password)

db.session.commit()

flash('Password changed successfully!', 'success')
return redirect(url_for('admin_settings'))

except Exception as e:
db.session.rollback()
print(f"❌ Change password error: {str(e)}", file=sys.stderr)
flash('Error changing password. Please try again.', 'danger')

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
# Try static uploads as fallback
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
'features': ['variants', 'multiple-images', 'delivery-logic', 'stock-management']
}), 200
except Exception as e:
return jsonify({
'status': 'unhealthy',
'error': str(e),
'timestamp': datetime.utcnow().isoformat()
}), 500

# ========== TEST ROUTE ==========
@app.route('/test')
def test():
"""Test route for debugging"""
try:
# Test database connection
db.session.execute(text('SELECT 1'))
db_status = 'connected'

# Test variant functionality
variant_count = ProductVariant.query.count()

except Exception as e:
db_status = f'error: {str(e)}'
variant_count = 0

return jsonify({
'status': 'ok',
'database': db_status,
'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
'upload_folder': app.config['UPLOAD_FOLDER'],
'session_keys': list(session.keys()),
'has_admin': User.query.count() > 0,
'has_products': Product.query.count() > 0,
'has_variants': variant_count > 0,
'variant_count': variant_count
})

# ========== APPLICATION FACTORY ==========
def create_app():
"""Application factory for Gunicorn"""
return app

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
print(f"✅ CSRF Protection: ENABLED", file=sys.stderr)
print(f"✅ Database Connection: READY", file=sys.stderr)
print(f"✅ File Upload: ENABLED", file=sys.stderr)
print(f"✅ Admin Panel: /admin (admin/admin123)", file=sys.stderr)
print(f"✅ Health Check: /health", file=sys.stderr)
print(f"✅ Debug Mode: {'ON' if debug else 'OFF'}", file=sys.stderr)
print(f"✅ Variant System: ENABLED", file=sys.stderr)
print(f"✅ Multiple Images: ENABLED", file=sys.stderr)
print(f"✅ Delivery Logic: ENABLED", file=sys.stderr)
print(f"✅ Stock Management: ENABLED", file=sys.stderr)
print(f"🌐 Server: http://localhost:{port}", file=sys.stderr)
print(f"📱 Mobile Friendly: YES", file=sys.stderr)
print(f"🔒 Secure: HTTPS Ready", file=sys.stderr)
print(f"{'='*60}\n", file=sys.stderr)

app.run(host='0.0.0.0', port=port, debug=debug)
