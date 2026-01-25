# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Changed from 50 to 100
    image_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    image_urls = db.Column(db.Text, default='[]')  # Added default value
    stock = db.Column(db.Integer, default=0)  # Changed default to 0
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with orders
    orders = db.relationship('Order', backref='product', lazy=True, cascade='all, delete-orphan')
    # Relationship with reviews
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def get_image_urls(self):
        """Helper method to parse image_urls JSON string"""
        try:
            return json.loads(self.image_urls) if self.image_urls else []
        except:
            return []
    
    def set_image_urls(self, urls_list):
        """Helper method to set image_urls as JSON string"""
        self.image_urls = json.dumps(urls_list)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)  # Changed from 200 to 100
    customer_email = db.Column(db.String(100), nullable=False)  # Changed from 200 to 100
    customer_phone = db.Column(db.String(20))  # NEW field for phone number
    customer_address = db.Column(db.Text)  # NEW field for address
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    payment_status = db.Column(db.String(50), default='Pending')  # NEW field for payment status
    notes = db.Column(db.Text)  # NEW field for order notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Added updated_at
    
    def __repr__(self):
        return f'<Order {self.id} - {self.customer_name}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)  # Changed from 200 to 100
    customer_email = db.Column(db.String(100))  # Made optional, changed from 200 to 100
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False)  # NEW field for admin approval
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Added updated_at
    
    def __repr__(self):
        return f'<Review {self.id} - Rating: {self.rating}>'

# Helper function to initialize database
def init_db(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created/updated successfully")
        
        # Check for default admin
        from werkzeug.security import generate_password_hash
        admin_count = Admin.query.count()
        if admin_count == 0:
            default_admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                created_at=datetime.utcnow()
            )
            db.session.add(default_admin)
            db.session.commit()
            print("👑 Created default admin: username='admin', password='admin123'")
        else:
            print(f"👑 Admin already exists: {admin_count} admin(s) found")
