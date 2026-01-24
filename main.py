#!/usr/bin/env python3
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from models import db, Admin, Product, Order, Review
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS if you have a frontend

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'sqlite:///database.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize db with app
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# ============ REVIEW ROUTES ============

@app.route('/api/reviews', methods=['GET'])
def get_all_reviews():
    """Get all reviews with optional filters"""
    product_id = request.args.get('product_id')
    min_rating = request.args.get('min_rating', type=int)
    
    query = Review.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if min_rating:
        query = query.filter(Review.rating >= min_rating)
    
    reviews = query.order_by(Review.created_at.desc()).all()
    
    return jsonify([{
        'id': r.id,
        'product_id': r.product_id,
        'customer_name': r.customer_name,
        'customer_email': r.customer_email,
        'rating': r.rating,
        'comment': r.comment,
        'created_at': r.created_at.isoformat() if r.created_at else None
    } for r in reviews])

@app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get reviews for a specific product"""
    reviews = Review.query.filter_by(product_id=product_id)\
                .order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = db.session.query(db.func.avg(Review.rating))\
                   .filter_by(product_id=product_id).scalar() or 0
    
    return jsonify({
        'product_id': product_id,
        'average_rating': round(float(avg_rating), 1),
        'total_reviews': len(reviews),
        'reviews': [{
            'id': r.id,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reviews]
    })

@app.route('/api/reviews', methods=['POST'])
def create_review():
    """Create a new review"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['product_id', 'customer_name', 'rating', 'comment']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate rating (1-5)
    if not 1 <= data['rating'] <= 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    # Check if product exists
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Create review
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
        'review_id': review.id,
        'review': {
            'id': review.id,
            'product_id': review.product_id,
            'customer_name': review.customer_name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat() if review.created_at else None
        }
    }), 201

@app.route('/api/reviews/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Get a specific review by ID"""
    review = Review.query.get_or_404(review_id)
    
    return jsonify({
        'id': review.id,
        'product_id': review.product_id,
        'customer_name': review.customer_name,
        'customer_email': review.customer_email,
        'rating': review.rating,
        'comment': review.comment,
        'created_at': review.created_at.isoformat() if review.created_at else None
    })

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Delete a review (admin only - add authentication in production)"""
    review = Review.query.get_or_404(review_id)
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'message': 'Review deleted successfully'})

# ============ PRODUCT ROUTES ============

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    products = Product.query.all()
    
    # Get average rating for each product
    products_with_ratings = []
    for product in products:
        avg_rating = db.session.query(db.func.avg(Review.rating))\
                       .filter_by(product_id=product.id).scalar() or 0
        review_count = Review.query.filter_by(product_id=product.id).count()
        
        products_with_ratings.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category,
            'image_url': product.image_url,
            'stock': product.stock,
            'featured': product.featured,
            'average_rating': round(float(avg_rating), 1),
            'review_count': review_count,
            'created_at': product.created_at.isoformat() if product.created_at else None
        })
    
    return jsonify(products_with_ratings)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product with its reviews"""
    product = Product.query.get_or_404(product_id)
    
    # Get reviews for this product
    reviews = Review.query.filter_by(product_id=product_id)\
                .order_by(Review.created_at.desc()).limit(10).all()
    
    avg_rating = db.session.query(db.func.avg(Review.rating))\
                   .filter_by(product_id=product_id).scalar() or 0
    
    return jsonify({
        'product': {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category,
            'image_url': product.image_url,
            'stock': product.stock,
            'featured': product.featured,
            'average_rating': round(float(avg_rating), 1),
            'total_reviews': Review.query.filter_by(product_id=product_id).count(),
            'created_at': product.created_at.isoformat() if product.created_at else None
        },
        'recent_reviews': [{
            'id': r.id,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reviews]
    })

# ============ ORDER ROUTES ============

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['customer_name', 'customer_email', 'product_id', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check product exists and has stock
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.stock < data['quantity']:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    # Calculate total
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
    
    # Update stock
    product.stock -= data['quantity']
    
    db.session.add(order)
    db.session.commit()
    
    return jsonify({
        'message': 'Order created successfully',
        'order_id': order.id,
        'total': total_price
    }), 201

# ============ ADMIN ROUTES ============

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Admin dashboard statistics"""
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Recent reviews
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(10).all()
    
    return jsonify({
        'stats': {
            'total_products': total_products,
            'total_orders': total_orders,
            'total_reviews': total_reviews
        },
        'recent_orders': [{
            'id': o.id,
            'customer_name': o.customer_name,
            'total_price': o.total_price,
            'status': o.status,
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in recent_orders],
        'recent_reviews': [{
            'id': r.id,
            'product_id': r.product_id,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in recent_reviews]
    })

# ============ HEALTH CHECK ============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.session.bind else 'disconnected'
    })

@app.route('/')
def home():
    """Home/API info endpoint"""
    return jsonify({
        'name': 'E-commerce API',
        'version': '1.0.0',
        'endpoints': {
            'products': '/api/products',
            'reviews': '/api/reviews',
            'orders': '/api/orders',
            'admin': '/api/admin/dashboard',
            'health': '/health'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
