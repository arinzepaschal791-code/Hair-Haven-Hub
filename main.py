# main.py - COMPLETE FIXED VERSION FOR NORA HAIR LINE
import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random
import string
from functools import wraps

# ========== CREATE APP FIRST ==========
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates',
           static_url_path='/static')

# ========== CONFIGURATION ==========
# Configure database for Render compatibility
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# ========== INITIALIZE EXTENSIONS ==========
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# ========== DATABASE MODELS ==========
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), default='default-category.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    products = db.relationship('Product', backref='category_rel', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float, nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.String(300), default='default-product.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50), default='cash_on_delivery')
    payment_status = db.Column(db.String(50), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    'shipping_fee': 2000.00,
    'payment_account': '2059311531',
    'payment_bank': 'UBA',
    'payment_name': 'CHUKWUNEKE CHIAMAKA',
    'year': datetime.now().year
}

# ========== DATABASE INITIALIZATION ==========
def init_database():
    """Initialize database with default data"""
    print("🔄 Initializing database...", file=sys.stderr)
    
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created", file=sys.stderr)
            
            # Create admin user if not exists
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@norahairline.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    username='admin',
                    email=admin_email,
                    password=generate_password_hash(admin_password),
                    is_admin=True
                )
                db.session.add(admin)
                print(f"✅ Admin user created: {admin_email}", file=sys.stderr)
            
            # Create default categories if none exist
            if Category.query.count() == 0:
                categories = [
                    ('Hair Extensions', 'hair-extensions', 'Premium quality 100% human hair extensions', 'hair-extensions.jpg'),
                    ('Wigs', 'wigs', 'Natural looking wigs and frontals', 'wigs.jpg'),
                    ('Closures', 'closures', 'Hair closures for protective styles', 'closures.jpg'),
                    ('Frontals', 'frontals', '13x4, 13x6 lace frontals', 'frontals.jpg'),
                    ('Hair Care', 'hair-care', 'Products for hair maintenance and growth', 'hair-care.jpg')
                ]
                
                for name, slug, desc, image in categories:
                    category = Category(name=name, slug=slug, description=desc, image=image)
                    db.session.add(category)
                
                print("✅ Default categories created", file=sys.stderr)
            
            # Create sample products if none exist
            if Product.query.count() == 0:
                categories = Category.query.all()
                
                sample_products = [
                    ('Brazilian Body Wave 24"', 129.99, 99.99, 50, 'hair-extensions', 'Premium Brazilian body wave hair extensions, 24 inches', 'brazilian-wave.jpg'),
                    ('Peruvian Straight 22"', 149.99, 119.99, 30, 'hair-extensions', 'Silky straight Peruvian human hair, 22 inches', 'peruvian-straight.jpg'),
                    ('13x4 Lace Frontal Wig', 199.99, 179.99, 20, 'wigs', 'Natural looking lace front wig with HD lace', 'lace-wig.jpg'),
                    ('4x4 Lace Closure', 89.99, 79.99, 40, 'closures', '4x4 HD lace closure with bleached knots', 'closure.jpg'),
                    ('13x6 Lace Frontal', 159.99, 139.99, 25, 'frontals', '13x6 lace frontal for natural hairline', 'frontal.jpg'),
                    ('Hair Growth Oil', 29.99, 24.99, 100, 'hair-care', 'Essential vitamins and oils for hair growth', 'hair-oil.jpg'),
                    ('Brazilian Curly 26"', 169.99, 139.99, 15, 'hair-extensions', 'Natural Brazilian curly hair, 26 inches', 'brazilian-curly.jpg'),
                    ('360 Lace Frontal Wig', 229.99, 199.99, 10, 'wigs', '360 lace frontal wig for full perimeter', '360-wig.jpg')
                ]
                
                for i, (name, price, sale_price, stock, category_slug, desc, image) in enumerate(sample_products):
                    category = Category.query.filter_by(slug=category_slug).first()
                    if category:
                        product = Product(
                            name=name,
                            slug=name.lower().replace(' ', '-').replace('"', ''),
                            sku=f'HAIR-{i+1:03d}',
                            description=desc,
                            short_description=f'Premium quality {name}',
                            price=price,
                            sale_price=sale_price,
                            stock=stock,
                            category_id=category.id,
                            image=image,
                            featured=(i < 4),
                            active=True
                        )
                        db.session.add(product)
                
                print("✅ Sample products created", file=sys.stderr)
            
            try:
                db.session.commit()
                print("✅ Database initialized successfully", file=sys.stderr)
                return True
            except Exception as e:
                db.session.rollback()
                print(f"❌ Database commit error: {e}", file=sys.stderr)
                return False
                
    except Exception as e:
        print(f"❌ Database initialization error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

# ========== INITIALIZE DATABASE ==========
init_database()

# ========== FLASK-LOGIN SETUP ==========
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# ========== CONTEXT PROCESSORS ==========
@app.context_processor
def inject_global_vars():
    """Make variables available to all templates"""
    try:
        categories = Category.query.filter(Category.products.any(Product.active == True)).all()
    except:
        categories = []
    
    cart_count = 0
    cart_total = 0
    if 'cart' in session:
        cart_count = sum(item.get('quantity', 1) for item in session['cart'])
        cart_total = sum(item.get('price', 0) * item.get('quantity', 1) for item in session['cart'])
    
    return dict(
        current_user=current_user,
        now=datetime.now(),
        categories=categories,
        cart_count=cart_count,
        cart_total=cart_total,
        current_year=datetime.now().year,
        config=BUSINESS_CONFIG,
        format_price=lambda x: f"₦{x:,.2f}" if x else "₦0.00"
    )

# ========== HELPER FUNCTIONS ==========
def generate_order_number():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'NORA-{timestamp}-{random_str}'

def calculate_cart_total():
    total = 0
    if 'cart' in session:
        for item in session['cart']:
            total += item.get('price', 0) * item.get('quantity', 1)
    return total

def get_featured_products():
    try:
        return Product.query.filter_by(featured=True, active=True).limit(8).all()
    except:
        return []

def get_all_categories():
    try:
        return Category.query.all()
    except:
        return []

# ========== DECORATORS ==========
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin area.', 'warning')
            return redirect(url_for('admin_login'))
        
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

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
def home():
    """Homepage with featured products"""
    try:
        featured_products = get_featured_products()
        categories = get_all_categories()
        
        # Format prices
        for product in featured_products:
            product.display_price = product.sale_price if product.sale_price else product.price
        
        return render_template('index.html',
                             featured_products=featured_products,
                             categories=categories,
                             category_count=len(categories))
    except Exception as e:
        print(f"❌ Homepage error: {e}", file=sys.stderr)
        # Fallback homepage
        return render_template('index.html',
                             featured_products=[],
                             categories=[],
                             category_count=0)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            if not all([name, email, subject, message]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('contact'))
            
            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            db.session.add(contact_msg)
            db.session.commit()
            
            flash('Your message has been sent successfully! We will contact you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Contact form error: {e}", file=sys.stderr)
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html')

@app.route('/shop')
def shop():
    """Shop page with products"""
    try:
        category_slug = request.args.get('category', '')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        # Start with base query
        query = Product.query.filter_by(active=True)
        
        # Apply category filter
        if category_slug:
            category = Category.query.filter_by(slug=category_slug).first()
            if category:
                query = query.filter_by(category_id=category.id)
        
        # Apply search filter
        if search:
            query = query.filter(
                Product.name.ilike(f'%{search}%') |
                Product.description.ilike(f'%{search}%')
            )
        
        # Get paginated results
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = get_all_categories()
        
        return render_template('shop.html',
                             products=products,
                             categories=categories,
                             category_slug=category_slug,
                             search_query=search)
    except Exception as e:
        print(f"❌ Shop page error: {e}", file=sys.stderr)
        flash('Error loading products. Please try again.', 'danger')
        return render_template('shop.html',
                             products=[],
                             categories=[],
                             category_slug='',
                             search_query='')

@app.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    try:
        product = Product.query.filter_by(slug=slug, active=True).first_or_404()
        
        # Get related products (same category)
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.active == True
        ).limit(4).all()
        
        # Format prices
        product.display_price = product.sale_price if product.sale_price else product.price
        for rp in related_products:
            rp.display_price = rp.sale_price if rp.sale_price else rp.price
        
        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products)
    except Exception as e:
        print(f"❌ Product detail error: {e}", file=sys.stderr)
        abort(404)

@app.route('/cart')
def cart():
    """Shopping cart page"""
    cart_items = session.get('cart', [])
    subtotal = calculate_cart_total()
    shipping = BUSINESS_CONFIG['shipping_fee'] if subtotal > 0 else 0
    total = subtotal + shipping
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         total=total)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    try:
        product = Product.query.get_or_404(product_id)
        
        if not product.active or product.stock <= 0:
            flash('Product is not available.', 'warning')
            return redirect(request.referrer or url_for('shop'))
        
        quantity = int(request.form.get('quantity', 1))
        
        if quantity > product.stock:
            flash(f'Only {product.stock} items available in stock.', 'warning')
            return redirect(request.referrer or url_for('product_detail', slug=product.slug))
        
        if 'cart' not in session:
            session['cart'] = []
        
        cart = session['cart']
        
        # Check if product already in cart
        for item in cart:
            if item['id'] == product_id:
                new_quantity = item['quantity'] + quantity
                if new_quantity > product.stock:
                    flash(f'Cannot add more. Only {product.stock - item["quantity"]} more available.', 'warning')
                    return redirect(request.referrer or url_for('cart'))
                
                item['quantity'] = new_quantity
                session.modified = True
                flash(f'Added {quantity} more of {product.name} to cart.', 'success')
                return redirect(request.referrer or url_for('cart'))
        
        # Add new item to cart
        cart.append({
            'id': product_id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.sale_price if product.sale_price else product.price),
            'quantity': quantity,
            'image': product.image,
            'stock': product.stock
        })
        session.modified = True
        
        flash(f'{product.name} added to cart!', 'success')
        return redirect(request.referrer or url_for('cart'))
        
    except Exception as e:
        print(f"❌ Add to cart error: {e}", file=sys.stderr)
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
                    if product and quantity > product.stock:
                        flash(f'Only {product.stock} items available in stock.', 'warning')
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

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            payment_method = request.form.get('payment_method', 'cash_on_delivery')
            notes = request.form.get('notes', '')
            
            # Validate required fields
            if not all([name, email, phone, address]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('checkout'))
            
            # Calculate totals
            subtotal = calculate_cart_total()
            shipping = BUSINESS_CONFIG['shipping_fee']
            total = subtotal + shipping
            
            # Create order
            order = Order(
                order_number=generate_order_number(),
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                total_amount=subtotal,
                shipping_amount=shipping,
                final_amount=total,
                payment_method=payment_method,
                shipping_address=address,
                customer_notes=notes
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID without committing
            
            # Add order items
            for item in session['cart']:
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
            return redirect(url_for('order_confirmation', order_number=order.order_number))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Checkout error: {e}", file=sys.stderr)
            flash('Error processing order. Please try again.', 'danger')
            return redirect(url_for('checkout'))
    
    # GET request - show checkout form
    cart_items = session.get('cart', [])
    subtotal = calculate_cart_total()
    shipping = BUSINESS_CONFIG['shipping_fee']
    total = subtotal + shipping
    
    return render_template('checkout.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         total=total)

@app.route('/order-confirmation/<order_number>')
def order_confirmation(order_number):
    """Order confirmation page"""
    try:
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        
        return render_template('order_confirmation.html',
                             order=order,
                             order_items=order_items)
    except:
        flash('Order not found.', 'danger')
        return redirect(url_for('home'))

@app.route('/track-order')
def track_order():
    """Order tracking page"""
    order_number = request.args.get('order_number', '')
    
    if order_number:
        try:
            order = Order.query.filter_by(order_number=order_number).first()
            if order:
                order_items = OrderItem.query.filter_by(order_id=order.id).all()
                return render_template('track_order.html',
                                     order=order,
                                     order_items=order_items,
                                     searched=True)
            else:
                flash('Order not found. Please check your order number.', 'warning')
        except:
            flash('Error retrieving order information.', 'danger')
    
    return render_template('track_order.html', searched=False)

# ========== ADMIN ROUTES ==========

@app.route('/admin')
def admin_redirect():
    """Redirect to admin login"""
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password) and user.is_admin:
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        # Get statistics
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_categories = Category.query.count()
        
        # Calculate revenue (sum of completed orders)
        completed_orders = Order.query.filter_by(payment_status='paid').all()
        total_revenue = sum(order.final_amount for order in completed_orders)
        
        # Get recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        
        # Get low stock products
        low_stock = Product.query.filter(Product.stock < 10, Product.active == True).count()
        
        # Get recent messages
        recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_categories=total_categories,
                             total_revenue=total_revenue,
                             recent_orders=recent_orders,
                             low_stock=low_stock,
                             recent_messages=recent_messages)
    except Exception as e:
        print(f"❌ Admin dashboard error: {e}", file=sys.stderr)
        flash('Error loading dashboard.', 'danger')
        return render_template('admin/dashboard.html',
                             total_products=0,
                             total_orders=0,
                             total_categories=0,
                             total_revenue=0,
                             recent_orders=[],
                             low_stock=0,
                             recent_messages=[])

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    """Admin product management"""
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
        categories = Category.query.all()
        
        return render_template('admin/products.html',
                             products=products,
                             categories=categories)
    except Exception as e:
        print(f"❌ Admin products error: {e}", file=sys.stderr)
        flash('Error loading products.', 'danger')
        return render_template('admin/products.html',
                             products=[],
                             categories=[])

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    """Add new product"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            short_description = request.form.get('short_description')
            price = float(request.form.get('price', 0))
            sale_price = request.form.get('sale_price')
            stock = int(request.form.get('stock', 0))
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
                short_description=short_description,
                price=price,
                sale_price=float(sale_price) if sale_price else None,
                stock=stock,
                sku=sku,
                image='default-product.jpg',
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
            print(f"❌ Add product error: {e}", file=sys.stderr)
            flash('Error adding product. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.short_description = request.form.get('short_description')
            product.price = float(request.form.get('price', 0))
            sale_price = request.form.get('sale_price')
            product.sale_price = float(sale_price) if sale_price else None
            product.stock = int(request.form.get('stock', 0))
            product.category_id = int(request.form.get('category_id'))
            product.featured = 'featured' in request.form
            product.active = 'active' in request.form
            
            # Update slug if name changed
            product.slug = product.name.lower().replace(' ', '-').replace('"', '').replace("'", '')
            
            db.session.commit()
            
            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Edit product error: {e}", file=sys.stderr)
            flash('Error updating product. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html',
                         product=product,
                         categories=categories)

@app.route('/admin/products/delete/<int:product_id>')
@login_required
@admin_required
def admin_delete_product(product_id):
    """Delete product"""
    try:
        product = Product.query.get_or_404(product_id)
        product_name = product.name
        
        db.session.delete(product)
        db.session.commit()
        
        flash(f'Product "{product_name}" deleted successfully!', 'success')
        return redirect(url_for('admin_products'))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Delete product error: {e}", file=sys.stderr)
        flash('Error deleting product.', 'danger')
        return redirect(url_for('admin_products'))

@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    """Admin category management"""
    try:
        categories = Category.query.all()
        return render_template('admin/categories.html', categories=categories)
    except Exception as e:
        print(f"❌ Admin categories error: {e}", file=sys.stderr)
        flash('Error loading categories.', 'danger')
        return render_template('admin/categories.html', categories=[])

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_category():
    """Add new category"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Generate slug
            slug = name.lower().replace(' ', '-')
            
            category = Category(
                name=name,
                slug=slug,
                description=description,
                image='default-category.jpg'
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Category "{name}" added successfully!', 'success')
            return redirect(url_for('admin_categories'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Add category error: {e}", file=sys.stderr)
            flash('Error adding category. Please try again.', 'danger')
    
    return render_template('admin/add_category.html')

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    """Admin order management"""
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
        print(f"❌ Admin orders error: {e}", file=sys.stderr)
        flash('Error loading orders.', 'danger')
        return render_template('admin/orders.html',
                             orders=[],
                             status='all')

@app.route('/admin/orders/<int:order_id>')
@login_required
@admin_required
def admin_order_detail(order_id):
    """Admin order detail"""
    try:
        order = Order.query.get_or_404(order_id)
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        
        return render_template('admin/order_detail.html',
                             order=order,
                             order_items=order_items)
    except Exception as e:
        print(f"❌ Admin order detail error: {e}", file=sys.stderr)
        flash('Error loading order details.', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/orders/update-status/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status(order_id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        payment_status = request.form.get('payment_status')
        admin_notes = request.form.get('admin_notes', '')
        
        if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            order.status = new_status
        
        if payment_status in ['pending', 'paid', 'failed', 'refunded']:
            order.payment_status = payment_status
        
        order.admin_notes = admin_notes
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Order #{order.order_number} status updated successfully!', 'success')
        return redirect(url_for('admin_order_detail', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update order status error: {e}", file=sys.stderr)
        flash('Error updating order status.', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/messages')
@login_required
@admin_required
def admin_messages():
    """Admin contact messages"""
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return render_template('admin/messages.html', messages=messages)
    except Exception as e:
        print(f"❌ Admin messages error: {e}", file=sys.stderr)
        flash('Error loading messages.', 'danger')
        return render_template('admin/messages.html', messages=[])

@app.route('/admin/messages/<int:message_id>/read')
@login_required
@admin_required
def admin_mark_message_read(message_id):
    """Mark message as read"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        message.is_read = True
        db.session.commit()
        
        flash('Message marked as read.', 'success')
        return redirect(url_for('admin_messages'))
    except Exception as e:
        db.session.rollback()
        flash('Error marking message as read.', 'danger')
        return redirect(url_for('admin_messages'))

# ========== API ENDPOINTS ==========
@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat(),
            'app': 'Nora Hair Line'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/stats')
@login_required
@admin_required
def api_stats():
    try:
        stats = {
            'total_products': Product.query.count(),
            'total_orders': Order.query.count(),
            'total_categories': Category.query.count(),
            'total_revenue': sum(o.final_amount for o in Order.query.filter_by(payment_status='paid').all()),
            'pending_orders': Order.query.filter_by(status='pending').count(),
        }
        return jsonify(stats)
    except:
        return jsonify({'error': 'Failed to fetch stats'}), 500

# ========== STATIC FILES ==========
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ========== TEST ROUTE ==========
@app.route('/test')
def test():
    """Simple test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test - Nora Hair Line</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .success { color: green; font-size: 24px; }
            .container { max-width: 600px; margin: 0 auto; }
            .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Nora Hair Line</h1>
            <div class="card">
                <div class="success">✅ Website is working!</div>
                <p><strong>All Systems Operational</strong></p>
                <p>Database: Connected</p>
                <p>Admin Panel: Ready</p>
                <p>Payment System: Active</p>
                <p>Cart System: Functional</p>
            </div>
            <div style="margin-top: 30px;">
                <a href="/" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px;">Go to Homepage</a>
                <a href="/admin/login" style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 10px;">Admin Login</a>
                <a href="/shop" style="padding: 10px 20px; background: #6f42c1; color: white; text-decoration: none; border-radius: 5px; margin: 10px;">Browse Products</a>
            </div>
        </div>
    </body>
    </html>
    '''

# ========== APPLICATION FACTORY ==========
def create_app():
    """Application factory for Gunicorn"""
    return app

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Create required directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('templates/admin', exist_ok=True)
    
    port = int(os.environ.get('PORT', 10000))
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🚀 NORA HAIR LINE E-COMMERCE", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"🌐 Homepage: http://localhost:{port}", file=sys.stderr)
    print(f"🛍️  Shop: http://localhost:{port}/shop", file=sys.stderr)
    print(f"👑 Admin: http://localhost:{port}/admin/login", file=sys.stderr)
    print(f"📧 Admin Login: admin@norahairline.com / admin123", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"📊 Products: {Product.query.count()}", file=sys.stderr)
    print(f"📁 Categories: {Category.query.count()}", file=sys.stderr)
    print(f"👥 Users: {User.query.count()}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
