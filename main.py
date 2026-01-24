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
def index():
    """Main store homepage - MUST be 'index' for url_for('index')"""
    return render_template('index.html')

@app.route('/home')
def home():
    """Alias for index"""
    return redirect(url_for('index'))

@app.route('/shop')
@app.route('/products')  # IMPORTANT: This allows url_for('products') to work
def products():
    """Products shopping page - MUST be 'products' for url_for('products')"""
    category = request.args.get('category', '')
    return render_template('products.html', category=category)

@app.route('/admin')
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('dashboard.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout page"""
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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

# ============ API ENDPOINTS ============

@app.route('/api')
def api_info():
    return jsonify({
        'app': 'NoraHairLine',
        'status': 'online',
        'endpoints': {
            'products': '/api/products',
            'orders': '/api/orders'
        }
    })

@app.route('/api/products')
def api_products():
    """API to get products"""
    try:
        category = request.args.get('category')
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
            
        products = query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'category': p.category,
            'image_url': p.image_url,
            'stock': p.stock,
            'featured': p.featured
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

# ============ ERROR PAGES ============

@app.errorhandler(404)
def page_not_found(e):
    try:
        return render_template('404.html'), 404
    except:
        return "Page not found", 404

@app.errorhandler(500)
def internal_error(e):
    try:
        return render_template('500.html'), 500
    except:
        return "Internal server error", 500

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 NoraHairLine Website Starting...")
    print(f"🌐 URL: https://norahairline.onrender.com")
    print(f"🔧 Debug: Check /health endpoint")
    app.run(host='0.0.0.0', port=port, debug=False)
