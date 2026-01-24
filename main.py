from flask import Flask, jsonify, request
import os
from datetime import datetime

# Import models - using absolute import
try:
    # First try direct import
    from models import db, Admin, Product, Order, Review
    print("✓ All models imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: try to import without Review
    try:
        from models import db, Admin, Product, Order
        Review = None
        print("✓ Imported without Review model")
    except ImportError:
        print("✗ Failed to import models")
        raise

app = Flask(__name__)

# Database configuration for Render
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's PostgreSQL URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"Using PostgreSQL database")
else:
    # SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    print("Using SQLite database")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123456')

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        # Try dropping and recreating (for development only)
        try:
            db.drop_all()
            db.create_all()
            print("✓ Tables recreated successfully")
        except Exception as e2:
            print(f"✗ Failed to recreate tables: {e2}")

# ================= ROUTES =================

@app.route('/')
def home():
    """Homepage - API info"""
    return jsonify({
        'app': 'Hair Haven Hub API',
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'database': app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0],
        'endpoints': {
            'products': '/api/products',
            'orders': '/api/orders',
            'reviews': '/api/reviews',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

# Products endpoints
@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        products = Product.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'category': p.category,
            'stock': p.stock,
            'featured': p.featured
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category': product.category,
        'image_url': product.image_url,
        'stock': product.stock
    })

# Orders endpoints
@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    orders = Order.query.all()
    return jsonify([{
        'id': o.id,
        'customer_name': o.customer_name,
        'product_id': o.product_id,
        'quantity': o.quantity,
        'total_price': o.total_price,
        'status': o.status
    } for o in orders])

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new order"""
    data = request.get_json()
    
    # Validate required fields
    required = ['customer_name', 'customer_email', 'product_id', 'quantity']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400
    
    # Create order
    order = Order(
        customer_name=data['customer_name'],
        customer_email=data['customer_email'],
        product_id=data['product_id'],
        quantity=data['quantity'],
        total_price=data.get('total_price', 0),
        status=data.get('status', 'Pending')
    )
    
    db.session.add(order)
    db.session.commit()
    
    return jsonify({
        'message': 'Order created',
        'order_id': order.id
    }), 201

# Reviews endpoints (only if Review model exists)
if Review:
    @app.route('/api/reviews', methods=['GET'])
    def get_reviews():
        """Get all reviews"""
        reviews = Review.query.all()
        return jsonify([{
            'id': r.id,
            'product_id': r.product_id,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment[:100] if r.comment else ''
        } for r in reviews])
    
    @app.route('/api/reviews', methods=['POST'])
    def create_review():
        """Create new review"""
        data = request.get_json()
        
        review = Review(
            product_id=data['product_id'],
            customer_name=data['customer_name'],
            customer_email=data.get('customer_email', ''),
            rating=data['rating'],
            comment=data['comment']
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'message': 'Review created',
            'review_id': review.id
        }), 201
else:
    print("⚠ Review routes disabled - Review model not available")

# Admin endpoint
@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """Admin statistics"""
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_reviews': Review.query.count() if Review else 0
    }
    return jsonify(stats)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting Hair Haven Hub API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
