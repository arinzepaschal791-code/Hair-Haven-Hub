from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Product, Order, Review
from datetime import datetime
import os

app = Flask(__name__)

# ===== CONFIGURATION =====
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nora-hairline-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///norahairline.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix for Render PostgreSQL URL
if 'DATABASE_URL' in os.environ:
    uri = os.environ.get('DATABASE_URL')
    if uri.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = uri.replace('postgres://', 'postgresql://', 1)

# ===== INITIALIZE =====
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ===== CREATE DATABASE TABLES =====
with app.app_context():
    db.create_all()

# ===== PUBLIC ROUTES =====

@app.route('/')
def index():
    products = Product.query.limit(6).all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    if category == 'all':
        products_list = Product.query.all()
    else:
        products_list = Product.query.filter_by(category=category).all()
    return render_template('products.html', products=products_list, category=category)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def order(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        order = Order(
            customer_name=request.form['name'],
            customer_email=request.form['email'],
            customer_phone=request.form['phone'],
            product_id=product_id,
            quantity=int(request.form['quantity']),
            total_price=product.price * int(request.form['quantity'])
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash(f'Order placed successfully! Order ID: {order.id}', 'success')
        return redirect(url_for('index'))
    
    return render_template('order.html', product=product)

# ===== ADMIN ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('admin/admin_login.html')
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('✅ Login successful! Welcome to Admin Dashboard', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid username or password', 'danger')
    
    return render_template('admin/admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         recent_products=recent_products)

@app.route('/admin/products')
@login_required
def admin_products():
    products_list = Product.query.all()
    return render_template('admin/admin_dashboard.html', products=products_list)

@app.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            category = request.form['category']
            stock = int(request.form.get('stock', 100))
            
            product = Product(
                name=name,
                description=description,
                price=price,
                category=category,
                stock=stock,
                image_url=request.form.get('image_url', '')
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'✅ Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            flash(f'❌ Error adding product: {str(e)}', 'danger')
    
    return render_template('admin/add_product.html')

@app.route('/admin/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = float(request.form['price'])
            product.category = request.form['category']
            product.stock = int(request.form.get('stock', 100))
            product.image_url = request.form.get('image_url', '')
            
            db.session.commit()
            flash(f'✅ Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            flash(f'❌ Error updating product: {str(e)}', 'danger')
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/delete-product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'✅ Product "{name}" deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('👋 Logged out successfully!', 'info')
    return redirect(url_for('index'))

# ===== SETUP ROUTES =====

@app.route('/setup-admin')
def setup_admin():
    # Check if admin already exists
    existing_admin = Admin.query.filter_by(username='admin').first()
    
    if existing_admin:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Admin Exists</title></head>
        <body style="padding: 40px; text-align: center;">
            <h1>⚠️ Admin Already Exists</h1>
            <p>Admin account is already created.</p>
            <p>Username: <strong>admin</strong></p>
            <p>Password: <strong>nora123</strong></p>
            <p><a href="/admin/login">Go to Login Page</a></p>
        </body>
        </html>
        '''
    
    # Create admin with password: nora123
    hashed_password = generate_password_hash('nora123', method='pbkdf2:sha256')
    new_admin = Admin(username='admin', password=hashed_password)
    
    db.session.add(new_admin)
    db.session.commit()
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Admin Created</title></head>
    <body style="padding: 40px; text-align: center;">
        <h1>✅ Admin Setup Complete!</h1>
        <p>Username: <strong>admin</strong></p>
        <p>Password: <strong>nora123</strong></p>
        <p><a href="/admin/login">Go to Login Page</a></p>
    </body>
    </html>
    '''

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
