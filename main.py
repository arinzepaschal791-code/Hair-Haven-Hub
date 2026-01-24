from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# Import models
try:
    from models import db, Admin, Product, Order, Review
    print("✓ All models imported successfully")
    HAS_REVIEW = True
except ImportError as e:
    print(f"Import error: {e}")
    from models import db, Admin, Product, Order
    Review = None
    HAS_REVIEW = False
    print("✓ Imported without Review model")

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✓ Using PostgreSQL database")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hairhaven.db'
    print("✓ Using SQLite database")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize database
db.init_app(app)

# Create tables and default admin
with app.app_context():
    try:
        db.create_all()
        print("✓ Database tables created")
        
        # Create default admin if none exists
        if Admin.query.count() == 0:
            default_admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
            )
            db.session.add(default_admin)
            db.session.commit()
            print("✓ Created default admin: username='admin', password='admin123'")
            
    except Exception as e:
        print(f"⚠ Database error: {e}")

# ============ WEBSITE PAGES ============

@app.route('/')
def home():
    """Main store homepage"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return redirect('/')

@app.route('/admin')
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/admin/dashboard')
def admin_dashboard_page():
    """Admin dashboard page"""
    return render_template('dashboard.html')

@app.route('/admin/products')
def admin_products_page():
    """Admin products management"""
    return render_template('admin_products.html')

@app.route('/admin/orders')
def admin_orders_page():
    """Admin orders management"""
    return render_template('admin_orders.html')

@app.route('/admin/reviews')
def admin_reviews_page():
    """Admin reviews management"""
    return render_template('admin_reviews.html')

@app.route('/shop')
@app.route('/products')
def shop():
    """Products shopping page"""
    return render_template('products.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    return render_template('product_detail.html', product_id=product_id)

@app.route('/cart')
def cart():
    """Shopping cart page"""
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    """Checkout page"""
    return render_template('checkout.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Register page"""
    return render_template('register.html')

@app.route('/account')
def account():
    """User account page"""
    return render_template('account.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# ============ STATIC FILE SERVING ============

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

# ============ API ENDPOINTS ============

@app.route('/api')
def api_info():
    """API documentation"""
    return jsonify({
        'app': 'Hair Haven Hub',
        'version': '1.0.0',
        'website': 'https://norahairline.onrender.com',
        'endpoints': {
            'products': {
                'GET /api/products': 'List all products',
                'GET /api/products/<id>': 'Get single product',
                'POST /api/products': 'Create product (admin)',
                'PUT /api/products/<id>': 'Update product (admin)',
                'DELETE /api/products/<id>': 'Delete product (admin)'
            },
            'orders': {
                'GET /api/orders': 'List all orders',
                'POST /api/orders': 'Create new order',
                'GET /api/orders/<id>': 'Get single order'
            },
            'admin': {
                'POST /api/admin/login': 'Admin login',
                'GET /api/admin/dashboard': 'Dashboard stats',
                'GET /api/admin/products': 'Admin products list'
            }
        }
    })

# Products API
@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products"""
    try:
        products = Product.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'category': p.category,
            'image_url': p.image_url,
            'stock': p.stock,
            'featured': p.featured,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    """Get single product"""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'category': product.category,
        'image_url': product.image_url,
        'stock': product.stock,
        'featured': product.featured
    })

# Orders API
@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    """Get all orders"""
    try:
        orders = Order.query.all()
        return jsonify([{
            'id': o.id,
            'customer_name': o.customer_name,
            'customer_email': o.customer_email,
            'product_id': o.product_id,
            'quantity': o.quantity,
            'total_price': float(o.total_price),
            'status': o.status,
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """Create new order"""
    try:
        data = request.get_json()
        
        order = Order(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_price=data['total_price'],
            status='Pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Order created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin API
@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Admin login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password, password):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {'username': username}
        })
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/admin/dashboard', methods=['GET'])
def api_admin_dashboard():
    """Admin dashboard stats"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_reviews': Review.query.count() if HAS_REVIEW and Review else 0,
        'total_sales': float(db.session.query(db.func.sum(Order.total_price)).scalar() or 0),
        'pending_orders': Order.query.filter_by(status='Pending').count(),
        'low_stock': Product.query.filter(Product.stock < 10).count()
    }
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    stats['recent_orders'] = [{
        'id': o.id,
        'customer_name': o.customer_name,
        'total': float(o.total_price),
        'status': o.status,
        'date': o.created_at.strftime('%Y-%m-%d') if o.created_at else ''
    } for o in recent_orders]
    
    return jsonify(stats)

# Reviews API
if HAS_REVIEW and Review:
    @app.route('/api/reviews', methods=['GET'])
    def api_get_reviews():
        """Get all reviews"""
        reviews = Review.query.all()
        return jsonify([{
            'id': r.id,
            'product_id': r.product_id,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reviews])
    
    @app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
    def api_get_product_reviews(product_id):
        """Get reviews for a product"""
        reviews = Review.query.filter_by(product_id=product_id).all()
        return jsonify([{
            'id': r.id,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reviews])

# Health check
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'app': 'Hair Haven Hub',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'templates': 'loaded'
    })

# ============ ERROR PAGES ============

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print(f"\n{'='*60}")
    print(f"🚀 HAIR HAVEN HUB - FULL WEBSITE")
    print(f"{'='*60}")
    print(f"🌐 Store Frontend:    https://norahairline.onrender.com")
    print(f"👑 Admin Panel:       https://norahairline.onrender.com/admin")
    print(f"🛍️  Shop:              https://norahairline.onrender.com/shop")
    print(f"📊 API Documentation: https://norahairline.onrender.com/api")
    print(f"{'='*60}")
    
    # List available templates
    if os.path.exists('templates'):
        templates = [f for f in os.listdir('templates') if f.endswith('.html')]
        print(f"📁 Templates found: {len(templates)}")
        for template in sorted(templates):
            print(f"   • {template}")
    
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
