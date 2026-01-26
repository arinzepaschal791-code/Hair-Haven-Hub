# main.py - COMPLETE WORKING VERSION WITH HOMEPAGE & ADMIN
import os
import sys
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates',
           static_url_path='/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hair-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///norahairline.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)

# ========== MODELS ==========
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category_ref', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.Column(db.String(100), nullable=False)  # Keep for easy access
    image = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='orders')
    items = db.Column(db.Text, nullable=False)  # JSON string
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cart:
    def __init__(self):
        self.items = []
    
    def add_item(self, product_id, quantity=1):
        for item in self.items:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                return
        self.items.append({'product_id': product_id, 'quantity': quantity})
    
    def remove_item(self, product_id):
        self.items = [item for item in self.items if item['product_id'] != product_id]
    
    def update_quantity(self, product_id, quantity):
        for item in self.items:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
    
    def get_items(self):
        return self.items
    
    def clear(self):
        self.items = []
    
    def get_total(self):
        total = 0
        for item in self.items:
            product = Product.query.get(item['product_id'])
            if product:
                total += product.price * item['quantity']
        return total

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

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
    'payment_name': 'CHUKWUNEKE CHIAMAKA'
}

# Helper functions
def format_price(price):
    """Format price as Nigerian Naira"""
    try:
        return f"₦{float(price):,.2f}"
    except:
        return "₦0.00"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_cart():
    """Get or create cart in session"""
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']

def get_cart_count():
    """Get total items in cart"""
    cart = get_cart()
    return sum(item.get('quantity', 0) for item in cart)

def get_cart_total():
    """Calculate cart total"""
    cart = get_cart()
    total = 0
    for item in cart:
        product = Product.query.get(item['product_id'])
        if product:
            total += product.price * item['quantity']
    return total

# Context processor
@app.context_processor
def inject_globals():
    return {
        **WEBSITE_CONFIG,
        'now': datetime.now(),
        'cart_count': get_cart_count(),
        'cart_total': format_price(get_cart_total())
    }

# Initialize database
def init_database():
    with app.app_context():
        try:
            db.create_all()
            
            # Create admin user if not exists
            if not User.query.filter_by(is_admin=True).first():
                admin = User(
                    username='admin',
                    email='admin@norahairline.com',
                    phone='08038707795',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
            
            # Create sample categories
            categories_data = [
                {'name': 'Hair Extensions', 'slug': 'hair-extensions', 'description': '100% Human Hair Extensions'},
                {'name': 'Wigs', 'slug': 'wigs', 'description': 'Lace Frontals & Wigs'},
                {'name': 'Closures', 'slug': 'closures', 'description': 'Hair Closures'},
                {'name': 'Frontals', 'slug': 'frontals', 'description': '13x4, 13x6 Frontals'},
                {'name': 'Hair Care', 'slug': 'hair-care', 'description': 'Hair Products & Care'}
            ]
            
            for cat_data in categories_data:
                if not Category.query.filter_by(slug=cat_data['slug']).first():
                    category = Category(**cat_data)
                    db.session.add(category)
            
            # Create sample products
            if Product.query.count() == 0:
                sample_products = [
                    Product(
                        name="Brazilian Straight Hair 24''",
                        slug="brazilian-straight-hair-24",
                        description="Premium 100% Brazilian Virgin Hair, Straight Texture, 24 inches",
                        price=25000.00,
                        old_price=30000.00,
                        category="Hair Extensions",
                        image="hair1.jpg",
                        stock=50,
                        featured=True,
                        tags="brazilian,straight,virgin hair"
                    ),
                    Product(
                        name="Peruvian Curly Hair 22''",
                        slug="peruvian-curly-hair-22",
                        description="100% Peruvian Human Hair, Natural Curly Pattern, 22 inches",
                        price=28000.00,
                        old_price=35000.00,
                        category="Hair Extensions",
                        image="hair2.jpg",
                        stock=30,
                        featured=True,
                        tags="peruvian,curly,human hair"
                    ),
                    Product(
                        name="13x4 Lace Frontal Wig",
                        slug="13x4-lace-frontal-wig",
                        description="HD Lace Frontal Wig, Pre-plucked, Natural Hairline",
                        price=45000.00,
                        old_price=55000.00,
                        category="Wigs",
                        image="wig1.jpg",
                        stock=20,
                        featured=True,
                        tags="wig,frontal,hd lace"
                    ),
                    Product(
                        name="360 Lace Frontal",
                        slug="360-lace-frontal",
                        description="360 Lace Frontal, Full Perimeter, 180% Density",
                        price=38000.00,
                        old_price=45000.00,
                        category="Frontals",
                        image="frontal1.jpg",
                        stock=25,
                        featured=True,
                        tags="360,frontal,lace"
                    ),
                    Product(
                        name="4x4 Lace Closure",
                        slug="4x4-lace-closure",
                        description="4x4 HD Lace Closure, Swiss Lace, Bleached Knots",
                        price=18000.00,
                        old_price=22000.00,
                        category="Closures",
                        image="closure1.jpg",
                        stock=40,
                        featured=True,
                        tags="closure,lace,4x4"
                    ),
                    Product(
                        name="Hair Growth Oil",
                        slug="hair-growth-oil",
                        description="Organic Hair Growth Oil with Rosemary & Castor Oil",
                        price=5000.00,
                        category="Hair Care",
                        image="oil1.jpg",
                        stock=100,
                        featured=False,
                        tags="oil,hair care,growth"
                    )
                ]
                
                for product in sample_products:
                    db.session.add(product)
            
            db.session.commit()
            print("✅ Database initialized successfully")
            print("👑 Admin: admin@norahairline.com / admin123")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            db.session.rollback()

# ========== ROUTES ==========

@app.route('/')
def home():
    """Homepage"""
    try:
        featured_products = Product.query.filter_by(featured=True).limit(6).all()
        categories = Category.query.limit(5).all()
        
        # Format prices
        for product in featured_products:
            product.formatted_price = format_price(product.price)
            if product.old_price:
                product.formatted_old_price = format_price(product.old_price)
        
        return render_template('index.html',
                             featured_products=featured_products,
                             categories=categories)
    except Exception as e:
        print(f"Home error: {e}")
        return render_template('index.html',
                             featured_products=[],
                             categories=[])

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
    categories = Category.query.all()
    
    # Format prices
    for product in products:
        product.formatted_price = format_price(product.price)
        if product.old_price:
            product.formatted_old_price = format_price(product.old_price)
    
    return render_template('shop.html',
                         products=products,
                         categories=categories,
                         category=category,
                         search=search)

@app.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    product = Product.query.filter_by(slug=slug).first_or_404()
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()
    
    # Format prices
    product.formatted_price = format_price(product.price)
    if product.old_price:
        product.formatted_old_price = format_price(product.old_price)
    
    for p in related_products:
        p.formatted_price = format_price(p.price)
    
    return render_template('product_detail.html',
                         product=product,
                         related_products=related_products)

@app.route('/category/<slug>')
def category_page(slug):
    """Category page"""
    category = Category.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(category=category.name).all()
    
    for product in products:
        product.formatted_price = format_price(product.price)
    
    return render_template('category.html',
                         category=category,
                         products=products)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/cart')
def cart():
    """Cart page"""
    cart_items = []
    cart_data = get_cart()
    
    for item in cart_data:
        product = Product.query.get(item['product_id'])
        if product:
            product.formatted_price = format_price(product.price)
            product.quantity = item['quantity']
            product.subtotal = product.price * product.quantity
            product.formatted_subtotal = format_price(product.subtotal)
            cart_items.append(product)
    
    total = sum(item.subtotal for item in cart_items)
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         total=format_price(total))

@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    """Add item to cart"""
    cart = get_cart()
    
    # Check if product exists
    product = Product.query.get_or_404(product_id)
    
    # Check if already in cart
    found = False
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += 1
            found = True
            break
    
    if not found:
        cart.append({'product_id': product_id, 'quantity': 1})
    
    session['cart'] = cart
    flash(f'{product.name} added to cart!', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    cart = get_cart()
    cart = [item for item in cart if item['product_id'] != product_id]
    session['cart'] = cart
    flash('Item removed from cart', 'info')
    return redirect(url_for('cart'))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update cart quantity"""
    quantity = int(request.form.get('quantity', 1))
    
    cart = get_cart()
    for item in cart:
        if item['product_id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            break
    
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    cart_items = []
    cart_data = get_cart()
    
    if not cart_data:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
    
    for item in cart_data:
        product = Product.query.get(item['product_id'])
        if product:
            product.quantity = item['quantity']
            product.subtotal = product.price * product.quantity
            cart_items.append(product)
    
    total = sum(item.subtotal for item in cart_items)
    
    return render_template('checkout.html',
                         cart_items=cart_items,
                         total=format_price(total))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
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
        
        login_user(user)
        flash('Registration successful! Welcome!', 'success')
        return redirect(url_for('home'))
    
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
    # Get stats
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         total_revenue=format_price(total_revenue),
                         recent_orders=recent_orders,
                         recent_products=recent_products)

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products management"""
    products = Product.query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()
    
    for product in products:
        product.formatted_price = format_price(product.price)
    
    return render_template('admin/products.html',
                         products=products,
                         categories=categories)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Add product"""
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        old_price = float(request.form.get('old_price', 0)) or None
        category_id = request.form.get('category_id')
        stock = int(request.form.get('stock', 0))
        featured = 'featured' in request.form
        tags = request.form.get('tags', '')
        
        # Get category name
        category = Category.query.get(category_id)
        
        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            old_price=old_price,
            category_id=category_id,
            category=category.name if category else '',
            stock=stock,
            featured=featured,
            tags=tags
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html',
                         categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id):
    """Edit product"""
    product = Product.query.get_or_404(id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.slug = request.form.get('slug')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        old_price = request.form.get('old_price')
        product.old_price = float(old_price) if old_price else None
        product.category_id = request.form.get('category_id')
        product.stock = int(request.form.get('stock', 0))
        product.featured = 'featured' in request.form
        product.tags = request.form.get('tags', '')
        
        # Update category name
        category = Category.query.get(product.category_id)
        if category:
            product.category = category.name
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html',
                         product=product,
                         categories=categories)

@app.route('/admin/products/delete/<int:id>')
@admin_required
def admin_delete_product(id):
    """Delete product"""
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders management"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    for order in orders:
        order.formatted_total = format_price(order.total_amount)
    
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:id>')
@admin_required
def admin_order_detail(id):
    """Order detail"""
    order = Order.query.get_or_404(id)
    order.formatted_total = format_price(order.total_amount)
    
    # Parse items JSON
    items = json.loads(order.items)
    
    return render_template('admin/order_detail.html',
                         order=order,
                         items=items)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users management"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """Admin categories management"""
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings"""
    return render_template('admin/settings.html')

# ========== API ENDPOINTS ==========

@app.route('/api/products')
def api_products():
    """API: Get all products"""
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'formatted_price': format_price(p.price),
        'category': p.category,
        'image': p.image,
        'stock': p.stock,
        'featured': p.featured
    } for p in products])

@app.route('/api/categories')
def api_categories():
    """API: Get all categories"""
    categories = Category.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'slug': c.slug,
        'product_count': len(c.products)
    } for c in categories])

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ========== START APPLICATION ==========

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('templates/admin', exist_ok=True)
    
    # Initialize database
    init_database()
    
    # Run app
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n{'='*60}")
    print(f"🚀 NORA HAIR LINE E-COMMERCE")
    print(f"{'='*60}")
    print(f"🌐 Homepage: http://localhost:{port}")
    print(f"🛍️  Shop: http://localhost:{port}/shop")
    print(f"👤 Login: http://localhost:{port}/login")
    print(f"👑 Admin: http://localhost:{port}/admin")
    print(f"📧 Admin Login: admin@norahairline.com / admin123")
    print(f"{'='*60}")
    print(f"📊 Products: {Product.query.count()}")
    print(f"📦 Categories: {Category.query.count()}")
    print(f"👥 Users: {User.query.count()}")
    print(f"{'='*60}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
