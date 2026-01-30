# models.py - COMPLETE VERSION (Matches main.py structure EXACTLY)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'admin_user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, nullable=False, default=0.0)  # Renamed from price
    compare_price = db.Column(db.Float)
    sku = db.Column(db.String(100))
    total_quantity = db.Column(db.Integer, default=0)  # Total across all variants
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_bundle = db.Column(db.Boolean, default=False)
    bundle_discount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('Category', backref='products', lazy='joined')
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    
    @property
    def stock(self):
        """Calculate total stock across all variants"""
        if self.variants:
            return sum(variant.stock for variant in self.variants)
        return self.total_quantity
    
    @property
    def min_price(self):
        """Get minimum variant price"""
        if self.variants:
            prices = [v.price for v in self.variants if v.price > 0]
            return min(prices) if prices else self.base_price
        return self.base_price
    
    @property
    def max_price(self):
        """Get maximum variant price"""
        if self.variants:
            prices = [v.price for v in self.variants if v.price > 0]
            return max(prices) if prices else self.base_price
        return self.base_price
    
    @property
    def display_price(self):
        """Display price range for products with variants"""
        if self.variants and len(set(v.price for v in self.variants)) > 1:
            return f"₦{self.min_price:,.0f} - ₦{self.max_price:,.0f}"
        return f"₦{self.min_price:,.0f}"
    
    @property
    def available_lengths(self):
        """Get unique available lengths"""
        if self.variants:
            lengths = [v.length for v in self.variants if v.length and v.stock > 0]
            return sorted(set(lengths))
        return []
    
    @property
    def available_textures(self):
        """Get unique available textures"""
        if self.variants:
            textures = [v.texture for v in self.variants if v.texture and v.stock > 0]
            return sorted(set(textures))
        return []
    
    def get_default_variant(self):
        """Get first available variant"""
        if self.variants:
            available = [v for v in self.variants if v.stock > 0]
            return available[0] if available else self.variants[0]
        return None
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductVariant(db.Model):
    __tablename__ = 'product_variant'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(200))
    length = db.Column(db.String(50))
    texture = db.Column(db.String(50))
    color = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    compare_price = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100), unique=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_variant_product', 'product_id'),
        db.Index('idx_variant_stock', 'stock'),
    )
    
    @property
    def available(self):
        return self.stock > 0
    
    def __repr__(self):
        return f'<ProductVariant {self.name} - {self.length} {self.texture}>'

class ProductImage(db.Model):
    __tablename__ = 'product_image'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.id}>'

class Customer(db.Model):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Customer {self.email}>'

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    shipping_area = db.Column(db.String(100))  # Added for Lagos areas
    total_amount = db.Column(db.Float, nullable=False)
    shipping_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50), default='bank_transfer')
    payment_status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    variant_details = db.Column(db.String(200))  # Store variant info: "24\" Brazilian Body Wave"
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    location = db.Column(db.String(100))
    verified_purchase = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    
    def __repr__(self):
        return f'<Review {self.id}>'

class BundleItem(db.Model):
    __tablename__ = 'bundle_item'
    
    id = db.Column(db.Integer, primary_key=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bundle = db.relationship('Product', foreign_keys=[bundle_id], backref='bundle_items')
    product = db.relationship('Product', foreign_keys=[product_id])
    
    def __repr__(self):
        return f'<BundleItem {self.id}>'

# Note: Cart functionality is handled by session in main.py
# No Cart/CartItem models needed
