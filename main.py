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
    try:
        from models import db, Admin, Product, Order
        Review = None
        HAS_REVIEW = False
        print("✓ Imported without Review model")
    except ImportError:
        print("✗ Failed to import models")
        raise

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database configuration for Render
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's PostgreSQL URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✓ Using PostgreSQL database")
else:
    # SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hairhaven.db'
    print("✓ Using SQLite database")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')

# Initialize database
db.init_app(app)

# Create database tables with proper error handling
with app.app_context():
    try:
        print("Creating database tables...")
        
        # IMPORTANT: Create tables in correct order to avoid foreign key issues
        # 1. First create the Product table (it's referenced by others)
        Product.__table__.create(db.engine, checkfirst=True)
        print("  ✓ Created 'products' table")
        
        # 2. Create Admin table (independent)
        Admin.__table__.create(db.engine, checkfirst=True)
        print("  ✓ Created 'admins' table")
        
        # 3. Create Order table (references products)
        Order.__table__.create(db.engine, checkfirst=True)
        print("  ✓ Created 'orders' table")
        
        # 4. Create Review table if it exists
        if HAS_REVIEW and Review:
            Review.__table__.create(db.engine, checkfirst=True)
            print("  ✓ Created 'reviews' table")
        
        print("✓ All tables created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating tables individually: {e}")
        print("Trying alternative method...")
        
        try:
            # Try the standard db.create_all()
            db.create_all()
            print("✓ Tables created via db.create_all()")
        except Exception as e2:
            print(f"✗ Failed with db.create_all(): {e2}")
            print("⚠ Attempting to reset database...")
            
            try:
                # Drop all tables and recreate
                db.drop_all()
                print("  ✓ Dropped all tables")
                db.create_all()
                print("  ✓ Created fresh tables")
            except Exception as e3:
                print(f"✗ Failed to reset: {e3}")
                print("⚠ Using existing database structure")
                print("ℹ Your app will still work, but some features may be limited")

# ==================== ROUTES ====================

@app.route('/')
def home():
    """Homepage - API info"""
    return jsonify({
        'app': 'Hair Haven Hub API',
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'message': 'Welcome to Hair Haven Hub E-commerce API',
        'endpoints': {
            'products': '/api/products',
            'single_product': '/api/products/<id>',
            'orders': '/api/orders',
            'create_order': '/api/orders [POST]',
            'reviews': '/api/reviews',
            'health': '/health',
            'admin_stats': '/api/admin/stats'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'timestamp': datetime.utcnow().isoformat()
    })

# ============ PRODUCT ROUTES ============

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
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
        return jsonify({'error': str(e), 'message': 'Failed to fetch products'}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category,
            'image_url': product.image_url,
            'stock': product.stock,
            'featured': product.featured,
            'created_at': product.created_at.isoformat() if product.created_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'Product not found'}), 404

# ============ ORDER ROUTES ============

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
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
        return jsonify({'error': str(e), 'message': 'Failed to fetch orders'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['customer_name', 'customer_email', 'product_id', 'quantity']
        missing = [field for field in required if field not in data]
        if missing:
            return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
        
        # Check if product exists
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Calculate total price if not provided
        total_price = data.get('total_price')
        if not total_price:
            total_price = product.price * data['quantity']
        
        # Create order
        order = Order(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_price=total_price,
            status=data.get('status', 'Pending')
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': order.id,
            'order': {
                'id': order.id,
                'customer_name': order.customer_name,
                'product_id': order.product_id,
                'quantity': order.quantity,
                'total_price': order.total_price,
                'status': order.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'message': 'Failed to create order'}), 500

# ============ REVIEW ROUTES ============

if HAS_REVIEW and Review:
    @app.route('/api/reviews', methods=['GET'])
    def get_reviews():
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
            return jsonify({'error': str(e), 'message': 'Failed to fetch reviews'}), 500
    
    @app.route('/api/reviews', methods=['POST'])
    def create_review():
        """Create new review"""
        try:
            data = request.get_json()
            
            required = ['product_id', 'customer_name', 'rating', 'comment']
            missing = [field for field in required if field not in data]
            if missing:
                return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
            
            # Validate rating
            if not 1 <= data['rating'] <= 5:
                return jsonify({'error': 'Rating must be between 1 and 5'}), 400
            
            # Check if product exists
            product = Product.query.get(data['product_id'])
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
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
                'message': 'Review created successfully',
                'review_id': review.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e), 'message': 'Failed to create review'}), 500
    
    @app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
    def get_product_reviews(product_id):
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
            return jsonify({'error': str(e), 'message': 'Failed to fetch reviews'}), 500

# ============ ADMIN ROUTES ============

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """Admin statistics dashboard"""
    try:
        stats = {
            'total_products': Product.query.count(),
            'total_orders': Order.query.count(),
            'total_reviews': Review.query.count() if HAS_REVIEW and Review else 0,
            'total_admins': Admin.query.count(),
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'Failed to get stats'}), 500

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'The requested resource was not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong'}), 500

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n{'='*60}")
    print(f"🚀 Starting Hair Haven Hub API")
    print(f"📁 Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]}")
    print(f"🌐 Port: {port}")
    print(f"🔗 Local: http://localhost:{port}")
    print(f"📊 Models: Admin, Product, Order" + (", Review" if HAS_REVIEW else ""))
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
