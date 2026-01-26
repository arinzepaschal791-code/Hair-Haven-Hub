import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)

# Configure database for Render compatibility
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    orders = db.relationship('Order', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    
    def get_id(self):
        return str(self.id)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(300), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviews = db.relationship('Review', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string of order items
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Context processors
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.context_processor
def inject_now():
    return dict(now=datetime.now())

# Admin decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first', 'error')
            return redirect(url_for('admin_login'))
        
        if not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', error=error), 500

# Routes
@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return render_template('500.html'), 500

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        products = Product.query.filter(
            (Product.name.ilike(f'%{query}%')) | 
            (Product.description.ilike(f'%{query}%'))
        ).all()
    else:
        products = []
    return render_template('products.html', products=products, query=query)

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
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
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials or not an admin', 'error')
    
    return render_template('admin/admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_users = User.query.count()
        total_reviews = Review.query.count()
        
        delivered_orders = Order.query.filter_by(status='delivered').all()
        total_revenue = sum(order.total_amount for order in delivered_orders)
        
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        low_stock_products = Product.query.filter(Product.stock < 10).all()
        
        for order in recent_orders:
            try:
                order.parsed_items = json.loads(order.items)
            except:
                order.parsed_items = []
        
        return render_template('admin/admin_dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_users=total_users,
                             total_reviews=total_reviews,
                             total_revenue=total_revenue,
                             recent_orders=recent_orders,
                             low_stock_products=low_stock_products)
    except Exception as e:
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/products')
@admin_required
def admin_products():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    products = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            stock = int(request.form.get('stock'))
            category_id = int(request.form.get('category_id'))
            
            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category_id=category_id,
                image=request.form.get('image') or 'default-product.jpg'
            )
            
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price'))
            product.stock = int(request.form.get('stock'))
            product.category_id = int(request.form.get('category_id'))
            product.image = request.form.get('image') or product.image
            
            db.session.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
    
    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    try:
        product = Product.query.get_or_404(id)
        
        if product.order_items:
            flash('Cannot delete product with existing orders', 'error')
            return redirect(url_for('admin_products'))
        
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        query = Order.query
    else:
        query = Order.query.filter_by(status=status_filter)
    
    search_order = request.args.get('search_order', '')
    if search_order:
        query = query.filter(Order.order_number.ilike(f'%{search_order}%'))
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    for order in orders.items:
        try:
            order.parsed_items = json.loads(order.items)
        except:
            order.parsed_items = []
    
    order_stats = {
        'pending': Order.query.filter_by(status='pending').count(),
        'processing': Order.query.filter_by(status='processing').count(),
        'shipped': Order.query.filter_by(status='shipped').count(),
        'delivered': Order.query.filter_by(status='delivered').count(),
        'cancelled': Order.query.filter_by(status='cancelled').count(),
        'total': Order.query.count()
    }
    
    return render_template('admin/order.html', 
                         orders=orders, 
                         status_filter=status_filter,
                         order_stats=order_stats,
                         search_order=search_order)

@app.route('/admin/orders/<int:id>')
@admin_required
def view_order(id):
    order = Order.query.get_or_404(id)
    
    try:
        order.parsed_items = json.loads(order.items)
    except:
        order.parsed_items = []
    
    user = User.query.get(order.user_id)
    
    return render_template('admin/order_detail.html', order=order, user=user)

@app.route('/admin/orders/update_status/<int:id>', methods=['POST'])
@admin_required
def update_order_status(id):
    try:
        order = Order.query.get_or_404(id)
        new_status = request.form.get('status')
        
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            flash('Invalid status', 'error')
            return redirect(url_for('admin_orders'))
        
        order.status = new_status
        
        if new_status == 'cancelled' and order.status != 'cancelled':
            try:
                items = json.loads(order.items)
                for item in items:
                    product = Product.query.get(item['product_id'])
                    if product:
                        product.stock += item['quantity']
            except:
                pass
        
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order status: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_orders'))

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    filter_type = request.args.get('filter', 'all')
    
    if filter_type == 'pending':
        query = Review.query.filter_by(is_approved=False)
    elif filter_type == 'approved':
        query = Review.query.filter_by(is_approved=True)
    else:
        query = Review.query
    
    search_product = request.args.get('search_product', '')
    if search_product:
        query = query.join(Product).filter(Product.name.ilike(f'%{search_product}%'))
    
    reviews = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    review_stats = {
        'total': Review.query.count(),
        'approved': Review.query.filter_by(is_approved=True).count(),
        'pending': Review.query.filter_by(is_approved=False).count()
    }
    
    return render_template('admin/reviews.html', 
                         reviews=reviews, 
                         filter_type=filter_type,
                         review_stats=review_stats,
                         search_product=search_product)

@app.route('/admin/reviews/approve/<int:id>', methods=['POST'])
@admin_required
def approve_review(id):
    try:
        review = Review.query.get_or_404(id)
        review.is_approved = True
        db.session.commit()
        flash('Review approved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving review: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_reviews'))

@app.route('/admin/reviews/delete/<int:id>', methods=['POST'])
@admin_required
def delete_review(id):
    try:
        review = Review.query.get_or_404(id)
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting review: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_reviews'))

@app.route('/admin/api/dashboard_stats')
@admin_required
def dashboard_stats():
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_users': User.query.count(),
        'total_reviews': Review.query.count(),
        'total_revenue': sum(order.total_amount for order in Order.query.filter_by(status='delivered').all()),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'low_stock_count': Product.query.filter(Product.stock < 10).count()
    }
    return jsonify(stats)

def create_admin_user():
    with app.app_context():
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
            
            # Create default categories
            if Category.query.count() == 0:
                categories = [
                    ('Electronics', 'electronics'),
                    ('Clothing', 'clothing'),
                    ('Books', 'books'),
                    ('Home & Garden', 'home-garden')
                ]
                for name, slug in categories:
                    category = Category(name=name, slug=slug)
                    db.session.add(category)
            
            db.session.commit()
            print(f'Admin user created: {admin_email}')

# Application factory for Gunicorn
def create_app():
    return app

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
