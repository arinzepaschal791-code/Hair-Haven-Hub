# main.py - COMPLETE FIXED VERSION FOR NORA HAIR LINE
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///norahairline.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# ========== INITIALIZE EXTENSIONS ==========
db = SQLAlchemy(app)

# ========== DATABASE MODELS ==========
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
    cost = db.Column(db.Float)
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
        """Return price as float for template formatting"""
        return float(self.price)
    
    @property
    def formatted_price(self):
        """Return formatted price string"""
        return f"₦{self.display_price:,.2f}"
    
    def __repr__(self):
        return f'<Product {self.name}>'

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
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
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    'shipping_fee': 2000.00,
    'payment_account': '2059311531',
    'payment_bank': 'UBA',
    'payment_name': 'CHUKWUNEKE CHIAMAKA',
    'year': datetime.now().year
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

# ========== AUTHENTICATION DECORATOR ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        
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
    except:
        pass
    
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
    """Homepage - MUST WORK with templates/index.html"""
    try:
        featured_products = Product.query.filter_by(featured=True, active=True).limit(8).all()
        categories = Category.query.limit(6).all()
        
        return render_template('index.html',
                             featured_products=featured_products,
                             categories=categories)
    except Exception as e:
        print(f"❌ Homepage error: {str(e)}", file=sys.stderr)
        return render_template('index.html',
                             featured_products=[],
                             categories=[])

@app.route('/shop')
def shop():
    """Shop page - uses templates/shop.html"""
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
        
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = Category.query.all()
        
        return render_template('shop.html',
                             products=products,
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
    """Product detail - uses templates/product_detail.html"""
    try:
        product = Product.query.get_or_404(id)
        
        # Get related products
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.active == True
        ).limit(4).all()
        
        # Get reviews
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
    """Shopping cart - uses templates/cart.html"""
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
            'stock': product.quantity
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

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page - uses templates/checkout.html"""
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
            payment_method = request.form.get('payment_method', 'bank_transfer')
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
                notes=notes
            )
            
            db.session.add(order)
            db.session.flush()
            
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
            return render_template('order.html',
                                 order=order,
                                 bank_details=BUSINESS_CONFIG)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Checkout error: {str(e)}", file=sys.stderr)
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

@app.route('/about')
def about():
    """About page - uses templates/about.html"""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page - uses templates/contact.html"""
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

@app.route('/account')
def account():
    """User account - uses templates/account.html"""
    return render_template('account.html')

# ========== ADMIN ROUTES ==========

@app.route('/admin')
@app.route('/admin/login')
def admin_login():
    """Admin login - uses templates/admin/admin_login.html"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.is_admin:
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password) and user.is_admin:
        session['user_id'] = user.id
        flash('Admin login successful!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid admin credentials.', 'danger')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard - uses templates/admin/admin_dashboard.html"""
    try:
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_categories = Category.query.count()
        
        # Calculate revenue
        revenue_orders = Order.query.filter_by(payment_status='paid').all()
        total_revenue = sum(order.final_amount for order in revenue_orders)
        
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        return render_template('admin/admin_dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_categories=total_categories,
                             total_revenue=total_revenue,
                             recent_orders=recent_orders)
    except Exception as e:
        print(f"❌ Admin dashboard error: {str(e)}", file=sys.stderr)
        flash('Error loading dashboard.', 'danger')
        return render_template('admin/admin_dashboard.html',
                             total_products=0,
                             total_orders=0,
                             total_categories=0,
                             total_revenue=0,
                             recent_orders=[])

@app.route('/admin/products')
@login_required
def admin_products():
    """Admin products list - uses templates/admin/products.html"""
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
@login_required
def admin_add_product():
    """Add product - uses templates/admin/add_product.html"""
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

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(id):
    """Edit product - uses templates/admin/edit_product.html"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price', 0))
            compare_price = request.form.get('compare_price')
            product.compare_price = float(compare_price) if compare_price else None
            product.quantity = int(request.form.get('quantity', 0))
            product.category_id = int(request.form.get('category_id'))
            product.featured = 'featured' in request.form
            product.active = 'active' in request.form
            
            # Update slug
            product.slug = product.name.lower().replace(' ', '-').replace('"', '').replace("'", '')
            
            db.session.commit()
            
            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Edit product error: {str(e)}", file=sys.stderr)
            flash('Error updating product. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html',
                         product=product,
                         categories=categories)

@app.route('/admin/products/delete/<int:id>')
@login_required
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
        flash('Error deleting product.', 'danger')
        return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    """Admin orders - uses templates/admin/order.html"""
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
@login_required
def admin_order_detail(id):
    """Order detail - uses templates/admin/order_detail.html"""
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

@app.route('/admin/orders/update/<int:id>', methods=['POST'])
@login_required
def admin_update_order(id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(id)
        order.status = request.form.get('status')
        order.payment_status = request.form.get('payment_status')
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Order #{order.order_number} updated successfully!', 'success')
        return redirect(url_for('admin_order_detail', id=order.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating order.', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    """Admin reviews - uses templates/admin/reviews.html"""
    try:
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        return render_template('admin/reviews.html', reviews=reviews)
    except Exception as e:
        print(f"❌ Admin reviews error: {str(e)}", file=sys.stderr)
        flash('Error loading reviews.', 'danger')
        return render_template('admin/reviews.html', reviews=[])

@app.route('/admin/reviews/approve/<int:id>')
@login_required
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

@app.route('/admin/reviews/delete/<int:id>')
@login_required
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

# ========== DATABASE INITIALIZATION ==========
def init_db():
    """Initialize database with tables and sample data"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created", file=sys.stderr)
        
        # Check if data already exists
        if Category.query.count() == 0:
            # Add sample categories for hair business
            categories = [
                Category(name='Lace Wigs', slug='lace-wigs', 
                        description='Natural looking lace front wigs with HD lace'),
                Category(name='Hair Bundles', slug='hair-bundles',
                        description='Premium 100% human hair bundles in various textures'),
                Category(name='Closures', slug='closures',
                        description='Hair closures for protective styling'),
                Category(name='Frontals', slug='frontals',
                        description='13x4 and 13x6 lace frontals'),
                Category(name='360 Wigs', slug='360-wigs',
                        description='360 lace wigs for full perimeter styling'),
                Category(name='Hair Care', slug='hair-care',
                        description='Products for hair maintenance and growth'),
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("✅ Sample categories added", file=sys.stderr)
        
        if Product.query.count() == 0:
            # Add sample hair products
            categories = Category.query.all()
            
            sample_products = [
                ('Brazilian Body Wave 24"', 129.99, 99.99, 50, 'hair-bundles', 
                 'Premium Brazilian body wave hair, 24 inches, 100% human hair', 'straight'),
                ('Peruvian Straight 22"', 149.99, 119.99, 30, 'hair-bundles',
                 'Silky straight Peruvian hair, 22 inches, natural black', 'straight'),
                ('13x4 Lace Frontal Wig', 199.99, 179.99, 20, 'lace-wigs',
                 'HD lace frontal wig with natural hairline', 'body-wave'),
                ('4x4 Lace Closure', 89.99, 79.99, 40, 'closures',
                 '4x4 HD lace closure with bleached knots', 'straight'),
                ('13x6 Lace Frontal', 159.99, 139.99, 25, 'frontals',
                 '13x6 lace frontal for natural look', 'curly'),
                ('Hair Growth Oil', 29.99, 24.99, 100, 'hair-care',
                 'Essential oils for hair growth and thickness', None),
                ('360 Lace Frontal Wig', 229.99, 199.99, 10, '360-wigs',
                 '360 lace wig for full perimeter styling', 'wavy'),
                ('Malaysian Straight 26"', 169.99, 139.99, 15, 'hair-bundles',
                 'Premium Malaysian straight hair, 26 inches', 'straight'),
            ]
            
            for i, (name, price, compare_price, quantity, category_slug, desc, texture) in enumerate(sample_products):
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
                        image_url=f'product-{i+1}.jpg'
                    )
                    db.session.add(product)
            
            db.session.commit()
            print("✅ Sample products added", file=sys.stderr)
        
        if User.query.count() == 0:
            # Add default admin user
            admin = User(
                username='admin',
                email='admin@norahairline.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created", file=sys.stderr)
        
        print("✅ Database initialization complete", file=sys.stderr)
        return True

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create required directories
    os.makedirs('static/uploads', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🚀 NORA HAIR LINE E-COMMERCE", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"🌐 Homepage: http://localhost:{port}", file=sys.stderr)
    print(f"🛍️  Shop: http://localhost:{port}/shop", file=sys.stderr)
    print(f"👑 Admin: http://localhost:{port}/admin", file=sys.stderr)
    print(f"📧 Admin Login: admin@norahairline.com / admin123", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    app.run(host='0.0.0.0', port=port, debug=True)
