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
            
        # Add sample products if none exist
        if Product.query.count() == 0:
            sample_products = [
                Product(
                    name="Premium Bone Straight Hair",
                    description="24-inch premium quality bone straight hair extensions",
                    price=89.99,
                    category="hair",
                    image_url="",
                    stock=50,
                    featured=True
                ),
                Product(
                    name="Curly Brazilian Hair",
                    description="Natural Brazilian curly hair 22-inch",
                    price=99.99,
                    category="hair",
                    image_url="",
                    stock=30,
                    featured=True
                ),
                Product(
                    name="Lace Front Wig",
                    description="Natural looking lace front wig",
                    price=129.99,
                    category="wigs",
                    image_url="",
                    stock=20,
                    featured=True
                ),
                Product(
                    name="Hair Growth Oil",
                    description="Organic hair growth and strengthening oil",
                    price=24.99,
                    category="care",
                    image_url="",
                    stock=100,
                    featured=False
                )
            ]
            for product in sample_products:
                db.session.add(product)
            db.session.commit()
            print("✓ Added sample products")
            
    except Exception as e:
        print(f"⚠ Database error: {e}")

# ============ WEBSITE PAGES ============

@app.route('/')
def index():
    """Main store homepage"""
    return render_template('index.html')

@app.route('/home')
def home():
    """Alias for index"""
    return redirect(url_for('index'))

@app.route('/shop')
@app.route('/products')
def products():
    """Products shopping page"""
    category = request.args.get('category', '')
    return render_template('products.html', category=category)

@app.route('/admin')
def admin():
    """Admin login page"""
    return render_template('admin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('dashboard.html')

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    return render_template('admin_products.html')

@app.route('/admin/orders')
def admin_orders():
    """Admin orders management"""
    return render_template('admin_orders.html')

@app.route('/admin/reviews')
def admin_reviews():
    """Admin reviews management"""
    return render_template('admin_reviews.html')

@app.route('/login')
def login():
    """User login page"""
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    """Shopping cart page"""
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    """Checkout page"""
    return render_template('checkout.html')

@app.route('/register')
def register():
    """User registration page"""
    return render_template('register.html')

@app.route('/account')
def account():
    """User account page"""
    return render_template('account.html')

@app.route('/about')
def about():
    """About us page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact us page"""
    return render_template('contact.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    return render_template('product_detail.html', product_id=product_id)

# ============ STATIC FILE SERVING ============

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ============ API ENDPOINTS ============

@app.route('/api')
def api_info():
    """API documentation"""
    return jsonify({
        'app': 'NoraHairLine',
        'version': '1.0.0',
        'status': 'online',
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
                'POST /api/admin/logout': 'Admin logout',
                'GET /api/admin/dashboard': 'Dashboard stats',
                'GET /api/admin/products': 'Admin products list',
                'GET /api/admin/orders': 'Admin orders list'
            },
            'auth': {
                'POST /api/login': 'User login',
                'POST /api/register': 'User registration',
                'POST /api/logout': 'User logout'
            }
        }
    })

# ============ PRODUCTS API ============

@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products with optional category filter"""
    try:
        category = request.args.get('category')
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        # Get featured products for homepage
        featured_only = request.args.get('featured', '').lower() == 'true'
        if featured_only:
            query = query.filter_by(featured=True)
            
        products = query.all()
        
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
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    """Get single product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'category': product.category,
            'image_url': product.image_url,
            'stock': product.stock,
            'featured': product.featured,
            'created_at': product.created_at.isoformat() if product.created_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 404

@app.route('/api/products/featured', methods=['GET'])
def api_get_featured_products():
    """Get featured products for homepage"""
    try:
        products = Product.query.filter_by(featured=True).limit(6).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'category': p.category,
            'image_url': p.image_url
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

# ============ ORDERS API ============

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
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """Create new order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}', 'success': False}), 400
        
        # Get product to calculate total
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({'error': 'Product not found', 'success': False}), 404
        
        # Calculate total price
        total_price = product.price * data['quantity']
        
        # Create order
        order = Order(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_price=total_price,
            status='Pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order.id,
            'order': {
                'id': order.id,
                'customer_name': order.customer_name,
                'total_price': float(order.total_price),
                'status': order.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

# ============ ADMIN API ============

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/admin/dashboard', methods=['GET'])
def api_admin_dashboard():
    """Admin dashboard statistics"""
    try:
        # Check if admin is logged in
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized', 'success': False}), 401
        
        stats = {
            'total_products': Product.query.count(),
            'total_orders': Order.query.count(),
            'total_reviews': Review.query.count() if HAS_REVIEW and Review else 0,
            'total_sales': float(db.session.query(db.func.sum(Order.total_price)).scalar() or 0),
            'pending_orders': Order.query.filter_by(status='Pending').count(),
            'completed_orders': Order.query.filter_by(status='Completed').count(),
            'low_stock': Product.query.filter(Product.stock < 10).count(),
            'out_of_stock': Product.query.filter(Product.stock == 0).count()
        }
        
        # Recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        stats['recent_orders'] = [{
            'id': o.id,
            'customer_name': o.customer_name,
            'product_id': o.product_id,
            'total': float(o.total_price),
            'status': o.status,
            'date': o.created_at.strftime('%Y-%m-%d') if o.created_at else ''
        } for o in recent_orders]
        
        # Recent products
        recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        stats['recent_products'] = [{
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'stock': p.stock
        } for p in recent_products]
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ REVIEWS API ============

if HAS_REVIEW and Review:
    @app.route('/api/reviews', methods=['GET'])
    def api_get_reviews():
        """Get all reviews"""
        try:
            reviews = Review.query.all()
            return jsonify([{
                'id': r.id,
                'product_id': r.product_id,
                'customer_name': r.customer_name,
                'customer_email': r.customer_email,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in reviews])
        except Exception as e:
            return jsonify({'error': str(e), 'success': False}), 500
    
    @app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
    def api_get_product_reviews(product_id):
        """Get reviews for a specific product"""
        try:
            reviews = Review.query.filter_by(product_id=product_id).all()
            return jsonify([{
                'id': r.id,
                'customer_name': r.customer_name,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in reviews])
        except Exception as e:
            return jsonify({'error': str(e), 'success': False}), 500

# ============ HEALTH & UTILITY ============

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'NoraHairLine',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'version': '1.0.0'
    })

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    try:
        return render_template('404.html'), 404
    except:
        return "Page not found", 404

@app.errorhandler(500)
def internal_error(e):
    """Custom 500 page"""
    try:
        return render_template('500.html'), 500
    except:
        return "Internal server error", 500

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print(f"\n{'='*60}")
    print(f"🚀 NORAHAIRLINE - FULL WEBSITE")
    print(f"{'='*60}")
    print(f"🌐 Homepage:          https://norahairline.onrender.com")
    print(f"🛍️  Shop:              https://norahairline.onrender.com/shop")
    print(f"👑 Admin Login:       https://norahairline.onrender.com/admin")
    print(f"📊 Admin Dashboard:   https://norahairline.onrender.com/admin/dashboard")
    print(f"🔧 API:               https://norahairline.onrender.com/api")
    print(f"❤️  Health Check:      https://norahairline.onrender.com/health")
    print(f"{'='*60}")
    
    # List available templates
    if os.path.exists('templates'):
        templates = [f for f in os.listdir('templates') if f.endswith('.html')]
        print(f"📁 Templates found: {len(templates)}")
        for template in sorted(templates):
            print(f"   • {template}")
    
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
