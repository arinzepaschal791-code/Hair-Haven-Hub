import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random
import string

app = Flask(__name__)

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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# ========== DATABASE MODELS ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='product_category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float, nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.String(300), default='default-product.jpg')
    images = db.Column(db.Text, nullable=True)  # JSON string for multiple images
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='product_reviewed', lazy=True)
    order_items = db.relationship('OrderItem', backref='product_ordered', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0)
    shipping_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, processing, shipped, delivered, cancelled, refunded
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    shipping_address = db.Column(db.Text, nullable=False)
    billing_address = db.Column(db.Text, nullable=True)
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order_parent', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    categories = Category.query.filter_by().all()
    cart_count = 0
    if 'cart' in session:
        cart_count = len(session['cart'])
    
    return dict(
        current_user=current_user,
        now=datetime.now(),
        categories=categories,
        cart_count=cart_count,
        current_year=datetime.now().year,
        app_name="Hair Haven Hub"
    )

# ========== HELPER FUNCTIONS ==========
def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'ORD-{timestamp}-{random_str}'

def generate_sku(name):
    """Generate SKU from product name"""
    prefix = ''.join([word[:3].upper() for word in name.split()[:2]])
    random_num = ''.join(random.choices(string.digits, k=6))
    return f'{prefix}-{random_num}'

def calculate_cart_total():
    """Calculate cart total from session"""
    total = 0
    if 'cart' in session:
        for item in session['cart']:
            total += item.get('price', 0) * item.get('quantity', 1)
    return total

# ========== DECORATORS ==========
def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
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
    # Log the error
    app.logger.error(f'500 Error: {error}')
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

# ========== PUBLIC ROUTES ==========
@app.route('/')
def home():
    """Homepage with featured products"""
    try:
        # Get featured products
        featured_products = Product.query.filter_by(featured=True, active=True).limit(8).all()
        
        # Get new arrivals (latest products)
        new_products = Product.query.filter_by(active=True).order_by(Product.created_at.desc()).limit(8).all()
        
        # Get categories for homepage
        categories = Category.query.all()
        
        # Get featured reviews
        featured_reviews = Review.query.filter_by(is_featured=True, is_approved=True).limit(3).all()
        
        return render_template('index.html',
                             featured_products=featured_products,
                             new_products=new_products,
                             categories=categories,
                             featured_reviews=featured_reviews)
    except Exception as e:
        app.logger.error(f'Homepage error: {e}')
        # Fallback to simple homepage if template error
        return render_template('index.html')

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
            
            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            db.session.add(contact_msg)
            db.session.commit()
            
            flash('Your message has been sent successfully! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html')

@app.route('/products')
def products():
    """Products listing page"""
    category_id = request.args.get('category', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search_query = request.args.get('q', '')
    
    # Build query
    query = Product.query.filter_by(active=True)
    
    # Apply category filter
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Apply search filter
    if search_query:
        query = query.filter(
            Product.name.ilike(f'%{search_query}%') |
            Product.description.ilike(f'%{search_query}%') |
            Product.short_description.ilike(f'%{search_query}%')
        )
    
    # Paginate results
    products_paginated = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.all()
    selected_category = Category.query.get(category_id) if category_id else None
    
    return render_template('products.html',
                         products=products_paginated,
                         categories=categories,
                         selected_category=selected_category,
                         search_query=search_query)

@app.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()
    
    # Get related products (same category)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.active == True
    ).limit(4).all()
    
    # Get approved reviews for this product
    reviews = Review.query.filter_by(
        product_id=product.id,
        is_approved=True
    ).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = 0
    if reviews:
        avg_rating = sum([r.rating for r in reviews]) / len(reviews)
    
    return render_template('product_detail.html',
                         product=product,
                         related_products=related_products,
                         reviews=reviews,
                         avg_rating=round(avg_rating, 1))

@app.route('/cart')
def cart():
    """Shopping cart page"""
    cart_items = session.get('cart', [])
    subtotal = calculate_cart_total()
    tax = subtotal * 0.08  # Example 8% tax
    shipping = 0 if subtotal == 0 else 5.99  # Example shipping
    total = subtotal + tax + shipping
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         tax=tax,
                         shipping=shipping,
                         total=total)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    
    if not product.active or product.stock <= 0:
        flash('Product is not available.', 'warning')
        return redirect(request.referrer or url_for('products'))
    
    quantity = int(request.form.get('quantity', 1))
    
    # Initialize cart if not exists
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if product already in cart
    cart = session['cart']
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += quantity
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

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update cart item quantity"""
    if 'cart' not in session:
        return redirect(url_for('cart'))
    
    quantity = int(request.form.get('quantity', 1))
    
    # Update quantity in cart
    for item in session['cart']:
        if item['id'] == product_id:
            if quantity <= 0:
                session['cart'].remove(item)
            else:
                item['quantity'] = quantity
            session.modified = True
            break
    
    flash('Cart updated!', 'success')
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
        session.modified = True
        flash('Item removed from cart.', 'info')
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        try:
            # Create order
            order_number = generate_order_number()
            subtotal = calculate_cart_total()
            tax = subtotal * 0.08
            shipping = 5.99
            total = subtotal + tax + shipping
            
            order = Order(
                order_number=order_number,
                user_id=current_user.id,
                total_amount=subtotal,
                tax_amount=tax,
                shipping_amount=shipping,
                final_amount=total,
                payment_method=request.form.get('payment_method', 'credit_card'),
                shipping_address=request.form.get('shipping_address'),
                billing_address=request.form.get('billing_address', request.form.get('shipping_address')),
                customer_notes=request.form.get('notes', '')
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
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
                    
                    # Update product stock
                    product.stock -= item['quantity']
            
            db.session.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            flash(f'Order #{order_number} placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_number=order_number))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Checkout error: {e}')
            flash('Error processing order. Please try again.', 'danger')
    
    # Calculate totals for checkout page
    subtotal = calculate_cart_total()
    tax = subtotal * 0.08
    shipping = 5.99 if subtotal > 0 else 0
    total = subtotal + tax + shipping
    
    return render_template('checkout.html',
                         subtotal=subtotal,
                         tax=tax,
                         shipping=shipping,
                         total=total)

@app.route('/order-confirmation/<order_number>')
@login_required
def order_confirmation(order_number):
    """Order confirmation page"""
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template('order_confirmation.html', order=order)

@app.route('/my-orders')
@login_required
def my_orders():
    """User's order history"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/search')
def search():
    """Search products"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('products'))
    
    products = Product.query.filter(
        (Product.name.ilike(f'%{query}%')) |
        (Product.description.ilike(f'%{query}%')) |
        (Product.short_description.ilike(f'%{query}%'))
    ).filter_by(active=True).all()
    
    return render_template('search_results.html',
                         products=products,
                         query=query,
                         results_count=len(products))

# ========== ADMIN ROUTES ==========
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
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
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials or not an admin.', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
@admin_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    # Statistics
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    total_reviews = Review.query.count()
    
    # Revenue calculations
    completed_orders = Order.query.filter_by(payment_status='paid').all()
    total_revenue = sum(order.final_amount for order in completed_orders)
    
    # Recent data
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(10).all()
    pending_reviews = Review.query.filter_by(is_approved=False).count()
    low_stock = Product.query.filter(Product.stock < 10, Product.active == True).count()
    
    # Chart data (last 7 days orders)
    last_week = datetime.utcnow() - timedelta(days=7)
    daily_orders = []
    for i in range(7):
        day = last_week + timedelta(days=i+1)
        count = Order.query.filter(
            Order.created_at >= day.replace(hour=0, minute=0, second=0),
            Order.created_at < day.replace(hour=23, minute=59, second=59)
        ).count()
        daily_orders.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         total_reviews=total_reviews,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         recent_products=recent_products,
                         pending_reviews=pending_reviews,
                         low_stock=low_stock,
                         daily_orders=daily_orders)

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    """Admin product management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    products = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    """Add new product"""
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            stock = int(request.form.get('stock'))
            category_id = int(request.form.get('category_id'))
            
            # Generate slug and SKU
            slug = name.lower().replace(' ', '-').replace('/', '-')
            sku = generate_sku(name)
            
            product = Product(
                name=name,
                slug=slug,
                sku=sku,
                description=description,
                short_description=request.form.get('short_description', ''),
                price=price,
                sale_price=float(request.form.get('sale_price')) if request.form.get('sale_price') else None,
                stock=stock,
                category_id=category_id,
                image=request.form.get('image') or 'default-product.jpg',
                featured=bool(request.form.get('featured')),
                active=bool(request.form.get('active'))
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
    
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    """Edit product"""
    product = Product.query.get_or_404(id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.slug = product.name.lower().replace(' ', '-').replace('/', '-')
            product.description = request.form.get('description')
            product.short_description = request.form.get('short_description', '')
            product.price = float(request.form.get('price'))
            product.sale_price = float(request.form.get('sale_price')) if request.form.get('sale_price') else None
            product.stock = int(request.form.get('stock'))
            product.category_id = int(request.form.get('category_id'))
            product.image = request.form.get('image') or product.image
            product.featured = bool(request.form.get('featured'))
            product.active = bool(request.form.get('active'))
            
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    
    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    """Delete product"""
    product = Product.query.get_or_404(id)
    
    # Check if product has orders
    if product.order_items:
        flash('Cannot delete product with existing orders. Deactivate instead.', 'warning')
        return redirect(url_for('admin_products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{product.name}" deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    """Admin order management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = Order.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Search
    search_term = request.args.get('search', '')
    if search_term:
        query = query.filter(
            (Order.order_number.ilike(f'%{search_term}%')) |
            (Order.user_id.in_([u.id for u in User.query.filter(
                (User.email.ilike(f'%{search_term}%')) |
                (User.username.ilike(f'%{search_term}%'))
            ).all()]))
        )
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistics
    stats = {
        'pending': Order.query.filter_by(status='pending').count(),
        'processing': Order.query.filter_by(status='processing').count(),
        'shipped': Order.query.filter_by(status='shipped').count(),
        'delivered': Order.query.filter_by(status='delivered').count(),
        'total': Order.query.count()
    }
    
    return render_template('admin/orders.html',
                         orders=orders,
                         status_filter=status_filter,
                         stats=stats,
                         search_term=search_term)

@app.route('/admin/orders/<int:id>')
@login_required
@admin_required
def view_order(id):
    """View order details"""
    order = Order.query.get_or_404(id)
    order_items = OrderItem.query.filter_by(order_id=id).all()
    
    return render_template('admin/order_detail.html',
                         order=order,
                         order_items=order_items)

@app.route('/admin/orders/update/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_order(id):
    """Update order status"""
    order = Order.query.get_or_404(id)
    
    status = request.form.get('status')
    payment_status = request.form.get('payment_status')
    tracking_number = request.form.get('tracking_number')
    admin_notes = request.form.get('admin_notes')
    
    if status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']:
        order.status = status
    
    if payment_status in ['pending', 'paid', 'failed', 'refunded']:
        order.payment_status = payment_status
    
    if tracking_number:
        order.tracking_number = tracking_number
    
    if admin_notes:
        order.admin_notes = admin_notes
    
    db.session.commit()
    
    flash(f'Order #{order.order_number} updated successfully!', 'success')
    return redirect(url_for('view_order', id=id))

@app.route('/admin/reviews')
@login_required
@admin_required
def admin_reviews():
    """Review management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    filter_type = request.args.get('filter', 'all')
    
    # Build query
    query = Review.query
    
    if filter_type == 'pending':
        query = query.filter_by(is_approved=False)
    elif filter_type == 'approved':
        query = query.filter_by(is_approved=True)
    elif filter_type == 'featured':
        query = query.filter_by(is_featured=True)
    
    reviews = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/reviews.html',
                         reviews=reviews,
                         filter_type=filter_type)

@app.route('/admin/reviews/approve/<int:id>')
@login_required
@admin_required
def approve_review(id):
    """Approve review"""
    review = Review.query.get_or_404(id)
    review.is_approved = True
    db.session.commit()
    
    flash('Review approved!', 'success')
    return redirect(request.referrer or url_for('admin_reviews'))

@app.route('/admin/reviews/feature/<int:id>')
@login_required
@admin_required
def feature_review(id):
    """Feature/unfeature review"""
    review = Review.query.get_or_404(id)
    review.is_featured = not review.is_featured
    db.session.commit()
    
    action = 'featured' if review.is_featured else 'unfeatured'
    flash(f'Review {action}!', 'success')
    return redirect(request.referrer or url_for('admin_reviews'))

@app.route('/admin/reviews/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_review(id):
    """Delete review"""
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    
    flash('Review deleted!', 'success')
    return redirect(request.referrer or url_for('admin_reviews'))

@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    """Category management"""
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    """Add category"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            slug = name.lower().replace(' ', '-')
            description = request.form.get('description', '')
            
            category = Category(
                name=name,
                slug=slug,
                description=description
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Category "{name}" added!', 'success')
            return redirect(url_for('admin_categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'danger')
    
    return render_template('admin/add_category.html')

@app.route('/admin/customers')
@login_required
@admin_required
def admin_customers():
    """Customer management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    customers = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/contact-messages')
@login_required
@admin_required
def contact_messages():
    """Contact messages"""
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contact_messages.html', messages=messages)

# ========== API ENDPOINTS ==========
@app.route('/api/products')
def api_products():
    """API endpoint for products"""
    products = Product.query.filter_by(active=True).limit(50).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'price': p.price,
        'sale_price': p.sale_price,
        'image': p.image,
        'category': p.product_category.name if p.product_category else ''
    } for p in products])

@app.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for dashboard stats"""
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_revenue': sum(o.final_amount for o in Order.query.filter_by(payment_status='paid').all()),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'new_customers': User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
    }
    return jsonify(stats)

# ========== INITIALIZATION ==========
def init_database():
    """Initialize database with default data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create admin user if not exists
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
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
            print(f"✓ Admin user created: {admin_email}")
        
        # Create default categories if none exist
        if Category.query.count() == 0:
            categories = [
                ('Hair Extensions', 'hair-extensions', 'Premium quality hair extensions'),
                ('Wigs', 'wigs', 'Natural looking wigs'),
                ('Hair Care', 'hair-care', 'Products for hair maintenance'),
                ('Accessories', 'accessories', 'Hair accessories'),
                ('Tools', 'tools', 'Hair styling tools')
            ]
            
            for name, slug, desc in categories:
                category = Category(name=name, slug=slug, description=desc)
                db.session.add(category)
            
            print("✓ Default categories created")
        
        # Create sample products if none exist
        if Product.query.count() == 0:
            categories = Category.query.all()
            
            sample_products = [
                ('Brazilian Body Wave', 129.99, 99.99, 50, 'Premium Brazilian body wave hair extensions'),
                ('Peruvian Straight', 149.99, 119.99, 30, 'Silky straight Peruvian hair'),
                ('Lace Front Wig', 199.99, None, 20, 'Natural looking lace front wig'),
                ('Hair Vitamins', 29.99, 24.99, 100, 'Essential vitamins for hair growth'),
                ('Hair Dryer', 89.99, 79.99, 25, 'Professional hair dryer')
            ]
            
            for i, (name, price, sale_price, stock, desc) in enumerate(sample_products):
                category = categories[i % len(categories)]
                product = Product(
                    name=name,
                    slug=name.lower().replace(' ', '-'),
                    sku=generate_sku(name),
                    description=desc,
                    short_description=f'Premium quality {name.lower()}',
                    price=price,
                    sale_price=sale_price,
                    stock=stock,
                    category_id=category.id,
                    image=f'product-{i+1}.jpg',
                    featured=(i < 3),
                    active=True
                )
                db.session.add(product)
            
            print("✓ Sample products created")
        
        try:
            db.session.commit()
            print("✓ Database initialized successfully")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Database initialization error: {e}")

# ========== APPLICATION FACTORY ==========
def create_app():
    """Application factory for Gunicorn"""
    init_database()
    return app

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    print(f"🚀 Hair Haven Hub starting on port {port}")
    print(f"📊 Admin login: {os.environ.get('ADMIN_EMAIL', 'admin@example.com')}")
    print(f"🔗 Website: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
