from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
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

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    try:
        db.create_all()
        print("✓ Database tables created")
        
        # Create a default admin if none exists
        admin = Admin.query.first()
        if not admin:
            from werkzeug.security import generate_password_hash
            default_admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
            )
            db.session.add(default_admin)
            db.session.commit()
            print("✓ Created default admin (username: admin, password: admin123)")
            
    except Exception as e:
        print(f"⚠ Database error: {e}")

# ============ WEBSITE ROUTES (HTML PAGES) ============

@app.route('/')
def home():
    """Main website homepage"""
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    """Admin dashboard"""
    return render_template('admin.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/products-page')
def products_page():
    """Products listing page"""
    return render_template('products.html')

@app.route('/cart')
def cart_page():
    """Shopping cart page"""
    return render_template('cart.html')

# Serve static files from client folder
@app.route('/client/<path:path>')
def serve_client_files(path):
    """Serve files from the client folder"""
    return send_from_directory('client', path)

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ============ API ROUTES (JSON) ============

@app.route('/api')
def api_info():
    """API information"""
    return jsonify({
        'app': 'Hair Haven Hub',
        'version': '1.0.0',
        'website': 'https://norahairline.onrender.com',
        'endpoints': {
            'products': '/api/products',
            'orders': '/api/orders',
            'reviews': '/api/reviews',
            'admin': '/api/admin',
            'health': '/health'
        }
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products (API)"""
    try:
        products = Product.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'category': p.category,
            'image_url': p.image_url,
            'stock': p.stock,
            'featured': p.featured,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders (API)"""
    try:
        orders = Order.query.all()
        return jsonify([{
            'id': o.id,
            'customer_name': o.customer_name,
            'customer_email': o.customer_email,
            'product_id': o.product_id,
            'quantity': o.quantity,
            'total_price': o.total_price,
            'status': o.status,
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    if admin:
        from werkzeug.security import check_password_hash
        if check_password_hash(admin.password, password):
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {'username': admin.username}
            })
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Admin dashboard data"""
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_reviews': Review.query.count() if HAS_REVIEW and Review else 0,
        'total_sales': db.session.query(db.func.sum(Order.total_price)).scalar() or 0
    }
    return jsonify(stats)

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# ============ ERROR HANDLING ============

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    return render_template('404.html'), 404

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n{'='*60}")
    print(f"🚀 Hair Haven Hub - Full Website")
    print(f"🌐 Website: https://norahairline.onrender.com")
    print(f"📊 Admin Panel: https://norahairline.onrender.com/admin")
    print(f"🔧 API: https://norahairline.onrender.com/api")
    print(f"📁 Static files: /static, /client")
    print(f"{'='*60}\n")
    
    # Check if templates exist
    if os.path.exists('templates'):
        print("✓ Templates folder found")
        templates = os.listdir('templates')
        print(f"  Templates: {templates}")
    
    if os.path.exists('static'):
        print("✓ Static folder found")
    
    if os.path.exists('client'):
        print("✓ Client folder found")
        client_files = os.listdir('client')
        print(f"  Client files: {client_files[:5]}...")  # Show first 5
    
    app.run(host='0.0.0.0', port=port, debug=False)
