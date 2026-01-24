from flask import Flask, jsonify, request
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

app = Flask(__name__)
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

# Create tables - SIMPLIFIED
with app.app_context():
    try:
        db.create_all()
        print("✓ Database tables created")
    except Exception as e:
        print(f"⚠ Database error: {e}")
        print("⚠ Continuing with existing tables")

# ============ ROUTES ============

@app.route('/')
def home():
    return jsonify({
        'app': 'Hair Haven Hub API',
        'status': 'online',
        'endpoints': {
            'products': '/api/products',
            'orders': '/api/orders',
            'reviews': '/api/reviews',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'category': p.category,
            'stock': p.stock
        } for p in products])
    except:
        return jsonify({'products': []})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        orders = Order.query.all()
        return jsonify([{
            'id': o.id,
            'customer_name': o.customer_name,
            'total_price': o.total_price,
            'status': o.status
        } for o in orders])
    except:
        return jsonify({'orders': []})

if HAS_REVIEW and Review:
    @app.route('/api/reviews', methods=['GET'])
    def get_reviews():
        try:
            reviews = Review.query.all()
            return jsonify([{
                'id': r.id,
                'product_id': r.product_id,
                'rating': r.rating,
                'comment': r.comment[:50] if r.comment else ''
            } for r in reviews])
        except:
            return jsonify({'reviews': []})

@app.route('/api/test', methods=['GET'])
def test():
    """Test database connection"""
    try:
        product_count = Product.query.count()
        return jsonify({
            'database': 'connected',
            'products': product_count,
            'status': 'ok'
        })
    except Exception as e:
        return jsonify({
            'database': 'error',
            'error': str(e),
            'status': 'error'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
