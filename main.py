from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Product, Order
import os

app = Flask(__name__)

# ===== CONFIGURATION =====
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
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
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ===== CREATE DATABASE TABLES =====
with app.app_context():
    db.create_all()

# ===== ROUTES =====

# Home Page
@app.route('/')
def index():
    products = Product.query.limit(6).all()  # Show only 6 products on homepage
    return render_template('index.html', products=products)

# All Products Page
@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    if category == 'all':
        products = Product.query.all()
    else:
        products = Product.query.filter_by(category=category).all()
    return render_template('products.html', products=products, category=category)

# Single Product Page
@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

# Order Page
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

# Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/dashboard.html', products=products, orders=orders)

# Add Product (Admin)
@app.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        image_url = request.form.get('image_url', '')
        
        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_product.html')

# Edit Product (Admin)
@app.route('/admin/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.category = request.form['category']
        product.image_url = request.form.get('image_url', '')
        
        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_product.html', product=product)

# Delete Product (Admin)
@app.route('/admin/delete-product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    product_name = product.name
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{product_name}" deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Update Order Status
@app.route('/admin/update-order/<int:id>', methods=['POST'])
@login_required
def update_order(id):
    order = Order.query.get_or_404(id)
    new_status = request.form['status']
    
    order.status = new_status
    db.session.commit()
    
    flash(f'Order #{id} status updated to {new_status}!', 'success')
    return redirect(url_for('admin_dashboard'))

# Admin Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))

# ===== SETUP ROUTES =====

# Create Admin Account (Run once)
@app.route('/create-admin')
def create_admin():
    # Check if admin already exists
    admin = Admin.query.filter_by(username='admin').first()
    
    if not admin:
        # Create admin with password: admin123
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        new_admin = Admin(username='admin', password=hashed_password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Created</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                .success { background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }
                .info { background: #d1ecf1; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }
                .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="success">
                <h1>✅ Admin Account Created!</h1>
                <p><strong>Username:</strong> admin</p>
                <p><strong>Password:</strong> admin123</p>
            </div>
            <div class="info">
                <p><strong>⚠️ IMPORTANT:</strong> Change this password after first login!</p>
            </div>
            <a class="btn" href="/login">Go to Login Page</a>
            <a class="btn" href="/">Go to Homepage</a>
        </body>
        </html>
        '''
    else:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Exists</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                .info { background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }
                .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="info">
                <h1>ℹ️ Admin Already Exists</h1>
                <p>Admin account is already created.</p>
                <p>Use username: <strong>admin</strong> and your password to login.</p>
            </div>
            <a class="btn" href="/login">Go to Login Page</a>
            <a class="btn" href="/">Go to Homepage</a>
        </body>
        </html>
        '''

# Add Sample Products (For testing)
@app.route('/add-sample-products')
def add_sample_products():
    # Check if products already exist
    existing = Product.query.first()
    if existing:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Products Exist</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                .info { background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }
                .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="info">
                <h1>ℹ️ Products Already Exist</h1>
                <p>Sample products are already added to your database.</p>
                <p>Go to admin dashboard to add more products.</p>
            </div>
            <a class="btn" href="/">Go to Homepage</a>
            <a class="btn" href="/admin/dashboard">Go to Admin Dashboard</a>
        </body>
        </html>
        '''
    
    sample_products = [
        {
            'name': 'Premium Bone Straight Hair',
            'description': '100% Virgin Human Hair, 24 inches, Brazilian Hair, Can be dyed and styled',
            'price': 129.99,
            'category': 'hair',
            'image_url': 'https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=400&h=300&fit=crop'
        },
        {
            'name': 'Natural Curly Hair Extension',
            'description': 'Water Wave Curly Hair, 22 inches, Malaysian Hair, Tangle Free',
            'price': 99.99,
            'category': 'hair',
            'image_url': 'https://images.unsplash.com/photo-1596703923338-48f1c07e4f2e?w=400&h=300&fit=crop'
        },
        {
            'name': 'Lace Front Wig - Blonde',
            'description': 'HD Lace Front Wig, 180% Density, Pre-plucked Hairline, Bleached Knots',
            'price': 199.99,
            'category': 'wigs',
            'image_url': 'https://images.unsplash.com/photo-1585747860715-2ba37e788b70?w=400&h=300&fit=crop'
        },
        {
            'name': 'Hair Growth Shampoo',
            'description': 'Organic Hair Growth Shampoo, Sulfate Free, For All Hair Types, 500ml',
            'price': 24.99,
            'category': 'care',
            'image_url': 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=400&h=300&fit=crop'
        },
        {
            'name': 'Hair Moisturizing Cream',
            'description': 'Daily Hair Moisturizer, Shea Butter & Coconut Oil, 250ml Jar',
            'price': 19.99,
            'category': 'care',
            'image_url': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=300&fit=crop'
        },
        {
            'name': 'Silky Straight Closure',
            'description': '4x4 Silk Base Closure, 14 inches, Brazilian Straight Hair',
            'price': 89.99,
            'category': 'hair',
            'image_url': 'https://images.unsplash.com/photo-1556228578-9c360e2d0b4a?w=400&h=300&fit=crop'
        }
    ]
    
    for product_data in sample_products:
        product = Product(**product_data)
        db.session.add(product)
    
    db.session.commit()
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Products Added</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
            .success { background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }
            .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="success">
            <h1>✅ Sample Products Added!</h1>
            <p>6 sample products have been added to your database.</p>
            <p>You can now see them on the homepage.</p>
        </div>
        <a class="btn" href="/">View Homepage</a>
        <a class="btn" href="/products">View All Products</a>
        <a class="btn" href="/admin/dashboard">Go to Admin Dashboard</a>
    </body>
    </html>
    '''

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
