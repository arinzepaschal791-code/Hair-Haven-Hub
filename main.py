from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json
import uuid
from werkzeug.utils import secure_filename

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

# ============ DATABASE CONFIGURATION ============
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
app.config['SESSION_TYPE'] = 'filesystem'

# ============ FILE UPLOAD CONFIGURATION ============
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')

# Create upload directories if they don't exist
for folder in [UPLOAD_FOLDER, IMAGE_FOLDER, VIDEO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

# Initialize database
db.init_app(app)

# ============ CREATE DEFAULT IMAGE DIRECTORY ============
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'static',
        'static/images',
        'templates',
        'templates/admin',
        'uploads',
        'uploads/images',
        'uploads/videos'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}/")

# ============ DATABASE SETUP ============
with app.app_context():
    try:
        # Ensure all directories exist
        ensure_directories()
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # ===== CREATE DEFAULT ADMIN =====
        admin_count = Admin.query.count()
        if admin_count == 0:
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            print(f"👑 Created default admin: username='admin', password='admin123'")
        else:
            print(f"👑 Admin already exists: {admin_count} admin(s) found")
        
        # ===== CREATE SAMPLE PRODUCTS =====
        product_count = Product.query.count()
        if product_count == 0:
            # Prices in Naira
            products = [
                Product(
                    name="Premium Bone Straight Hair 24\"",
                    description="24-inch premium quality 100% human hair, bone straight texture",
                    price=134985.0,  # Naira
                    category="hair",
                    image_url="/static/images/hair1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/hair1.jpg"]),
                    stock=50,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Curly Brazilian Hair 22\"",
                    description="22-inch natural Brazilian curly hair, soft and bouncy",
                    price=149985.0,  # Naira
                    category="hair",
                    image_url="/static/images/hair2.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/hair2.jpg"]),
                    stock=30,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Lace Front Wig - Natural Black",
                    description="13x4 lace front wig, natural black color, pre-plucked",
                    price=194985.0,  # Naira
                    category="wigs",
                    image_url="/static/images/wig1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/wig1.jpg"]),
                    stock=20,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Hair Growth Oil 8oz",
                    description="Organic hair growth oil with rosemary and castor oil",
                    price=37485.0,  # Naira
                    category="care",
                    image_url="/static/images/oil1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/oil1.jpg"]),
                    stock=100,
                    featured=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Moisturizing Shampoo 16oz",
                    description="Sulfate-free moisturizing shampoo for all hair types",
                    price=28485.0,  # Naira
                    category="care",
                    image_url="/static/images/shampoo1.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/shampoo1.jpg"]),
                    stock=80,
                    featured=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Product(
                    name="Silk Press Hair 26\"",
                    description="26-inch silk press hair, ultra smooth and shiny",
                    price=179985.0,  # Naira
                    category="hair",
                    image_url="/static/images/hair3.jpg",
                    video_url="",
                    image_urls=json.dumps(["/static/images/hair3.jpg"]),
                    stock=15,
                    featured=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            # Add products to session
            for product in products:
                db.session.add(product)
            
            print(f"🛍️  Created {len(products)} sample products")
        
        else:
            print(f"🛍️  Products already exist: {product_count} product(s) found")
        
        # Commit all changes
        db.session.commit()
        print("✅ Database setup completed successfully")
        
    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")
        # Rollback in case of error
        db.session.rollback()
        import traceback
        traceback.print_exc()
# ============ END DATABASE SETUP ============

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

# ============ ADMIN PAGES ============

@app.route('/admin')
def admin():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin/products.html')

@app.route('/admin/orders')
def admin_orders():
    """Admin orders management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin/order.html')

@app.route('/admin/reviews')
def admin_reviews():
    """Admin reviews management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin/reviews.html')

@app.route('/admin/products/add')
def add_product():
    """Add product page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:product_id>')
def edit_product(product_id):
    """Edit product page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin/edit_product.html', product_id=product_id)

@app.route('/admin/logout')
def admin_logout_route():
    """Admin logout route"""
    session.clear()
    return redirect(url_for('admin'))

# ============ STATIC FILE SERVING ============

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files with fallback for missing images"""
    try:
        return send_from_directory('static', filename)
    except:
        # If file not found, try to serve from appropriate subdirectory
        if filename.startswith('images/'):
            try:
                # Try to serve a default image
                return send_from_directory('static/images', 'default-product.jpg')
            except:
                # Return 404 if default image also not found
                return "Image not found", 404
        return "File not found", 404

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    """Serve images with fallback to default image"""
    try:
        return send_from_directory('static/images', filename)
    except:
        # Return default product image if file not found
        try:
            return send_from_directory('static/images', 'default-product.jpg')
        except:
            # Create a simple default image response
            from flask import Response
            return Response(
                "Image not available",
                status=200,
                mimetype="text/plain"
            )

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    try:
        return send_from_directory('uploads', filename)
    except:
        return "File not found", 404

@app.route('/uploads/images/<path:filename>')
def serve_uploaded_images(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory('uploads/images', filename)
    except:
        return "Image not found", 404

@app.route('/uploads/videos/<path:filename>')
def serve_uploaded_videos(filename):
    """Serve uploaded videos"""
    try:
        return send_from_directory('uploads/videos', filename)
    except:
        return "Video not found", 404

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ============ FILE UPLOAD ENDPOINTS ============

@app.route('/api/upload/image', methods=['POST'])
def upload_image():
    """Upload product image"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_image_file(file.filename):
            return jsonify({'success': False, 'message': 'File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Save file
        file_path = os.path.join(IMAGE_FOLDER, unique_filename)
        file.save(file_path)
        
        # Return URL path
        url_path = f"/uploads/images/{unique_filename}"
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'url': url_path,
            'filename': unique_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    """Upload product video"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_video_file(file.filename):
            return jsonify({'success': False, 'message': 'File type not allowed. Use MP4, MOV, AVI, MKV, or WEBM'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Save file
        file_path = os.path.join(VIDEO_FOLDER, unique_filename)
        file.save(file_path)
        
        # Return URL path
        url_path = f"/uploads/videos/{unique_filename}"
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'url': url_path,
            'filename': unique_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ API ENDPOINTS ============

@app.route('/api')
def api_info():
    """API documentation"""
    return jsonify({
        'app': 'NoraHairLine',
        'version': '1.0.0',
        'status': 'online',
        'currency': 'NGN (₦)',
        'endpoints': {
            'products': {
                'GET /api/products': 'List all products',
                'GET /api/products/<id>': 'Get single product',
                'GET /api/products/featured': 'Get featured products'
            },
            'orders': {
                'GET /api/orders': 'List all orders',
                'POST /api/orders': 'Create new order'
            },
            'upload': {
                'POST /api/upload/image': 'Upload image (admin only)',
                'POST /api/upload/video': 'Upload video (admin only)'
            },
            'admin': {
                'POST /api/admin/login': 'Admin login',
                'POST /api/admin/logout': 'Admin logout',
                'GET /api/admin/dashboard': 'Dashboard stats',
                'GET /api/admin/check-auth': 'Check admin authentication',
                'POST /api/admin/products': 'Create product',
                'PUT /api/admin/products/<id>': 'Update product',
                'DELETE /api/admin/products/<id>': 'Delete product'
            },
            'health': 'GET /health'
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
        
        featured_only = request.args.get('featured', '').lower() == 'true'
        if featured_only:
            query = query.filter_by(featured=True)
            
        products = query.all()
        
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'formatted_price': f"₦{float(p.price):,.2f}",
            'category': p.category,
            'image_url': p.image_url or '/static/images/default-product.jpg',
            'video_url': p.video_url or '',
            'image_urls': json.loads(p.image_urls) if p.image_urls else [],
            'stock': p.stock,
            'featured': p.featured,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None
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
            'formatted_price': f"₦{float(product.price):,.2f}",
            'category': product.category,
            'image_url': product.image_url or '/static/images/default-product.jpg',
            'video_url': product.video_url or '',
            'image_urls': json.loads(product.image_urls) if product.image_urls else [],
            'stock': product.stock,
            'featured': product.featured,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
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
            'description': p.description[:100] + '...' if len(p.description) > 100 else p.description,
            'price': float(p.price),
            'formatted_price': f"₦{float(p.price):,.2f}",
            'category': p.category,
            'image_url': p.image_url or '/static/images/default-product.jpg',
            'video_url': p.video_url or '',
            'image_urls': json.loads(p.image_urls) if p.image_urls else []
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
            'formatted_total_price': f"₦{float(o.total_price):,.2f}",
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
        
        required_fields = ['customer_name', 'customer_email', 'product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}', 'success': False}), 400
        
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({'error': 'Product not found', 'success': False}), 404
        
        # Calculate total price in Naira
        total_price = float(product.price) * data['quantity']
        
        # Check stock
        if product.stock < data['quantity']:
            return jsonify({'error': f'Only {product.stock} items left in stock', 'success': False}), 400
        
        # Update stock
        product.stock -= data['quantity']
        
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
                'formatted_total_price': f"₦{float(order.total_price):,.2f}",
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

@app.route('/api/admin/check-auth', methods=['GET'])
def api_check_admin_auth():
    """Check if admin is logged in"""
    return jsonify({
        'logged_in': session.get('admin_logged_in', False),
        'username': session.get('admin_username', '')
    })

@app.route('/api/admin/dashboard', methods=['GET'])
def api_admin_dashboard():
    """Admin dashboard statistics"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized', 'success': False}), 401
        
        total_sales = float(db.session.query(db.func.sum(Order.total_price)).scalar() or 0)
        
        stats = {
            'total_products': Product.query.count(),
            'total_orders': Order.query.count(),
            'total_reviews': Review.query.count() if HAS_REVIEW and Review else 0,
            'total_sales': total_sales,
            'formatted_total_sales': f"₦{total_sales:,.2f}",
            'pending_orders': Order.query.filter_by(status='Pending').count(),
            'completed_orders': Order.query.filter_by(status='Completed').count(),
            'low_stock': Product.query.filter(Product.stock < 10).count(),
            'out_of_stock': Product.query.filter(Product.stock == 0).count()
        }
        
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        stats['recent_orders'] = [{
            'id': o.id,
            'customer_name': o.customer_name,
            'product_id': o.product_id,
            'total': float(o.total_price),
            'formatted_total': f"₦{float(o.total_price):,.2f}",
            'status': o.status,
            'date': o.created_at.strftime('%Y-%m-%d') if o.created_at else ''
        } for o in recent_orders]
        
        recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        stats['recent_products'] = [{
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'formatted_price': f"₦{float(p.price):,.2f}",
            'stock': p.stock
        } for p in recent_products]
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ADMIN PRODUCTS API ============

@app.route('/api/admin/products', methods=['POST'])
def api_create_product():
    """Create new product (admin only)"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        required_fields = ['name', 'description', 'price', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}', 'success': False}), 400
        
        image_urls = data.get('image_urls', [])
        if isinstance(image_urls, list):
            image_urls_json = json.dumps(image_urls)
        else:
            image_urls_json = '[]'
        
        product = Product(
            name=data['name'],
            description=data['description'],
            price=float(data['price']),
            category=data['category'],
            image_url=data.get('image_url', '/static/images/default-product.jpg'),
            video_url=data.get('video_url', ''),
            image_urls=image_urls_json,
            stock=int(data.get('stock', 100)),
            featured=bool(data.get('featured', False)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product created successfully',
            'product_id': product.id,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'formatted_price': f"₦{float(product.price):,.2f}"
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/admin/products/<int:product_id>', methods=['PUT'])
def api_update_product(product_id):
    """Update product (admin only)"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = float(data['price'])
        if 'category' in data:
            product.category = data['category']
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'video_url' in data:
            product.video_url = data['video_url']
        if 'image_urls' in data:
            image_urls = data['image_urls']
            if isinstance(image_urls, list):
                product.image_urls = json.dumps(image_urls)
        if 'stock' in data:
            product.stock = int(data['stock'])
        if 'featured' in data:
            product.featured = bool(data['featured'])
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    """Delete product (admin only)"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        product = Product.query.get_or_404(product_id)
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

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
        'version': '1.0.0',
        'currency': 'NGN (₦)'
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

# ============ MIDDLEWARE FOR ADMIN PROTECTION ============

@app.before_request
def check_admin_access():
    admin_routes = [
        '/admin/dashboard',
        '/admin/products',
        '/admin/orders',
        '/admin/reviews',
        '/admin/products/add',
        '/admin/products/edit/',
        '/admin/logout',
        '/api/upload/image',
        '/api/upload/video',
        '/api/admin/products',
        '/api/admin/dashboard'
    ]
    
    for route in admin_routes:
        if request.path.startswith(route):
            if not session.get('admin_logged_in'):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Unauthorized'}), 401
                else:
                    return redirect(url_for('admin'))

# ============ START APPLICATION ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Ensure directories exist
    ensure_directories()
    
    print(f"\n{'='*60}")
    print(f"🚀 NORAHAIRLINE - FULL WEBSITE")
    print(f"{'='*60}")
    print(f"🌐 Homepage:          https://norahairline.onrender.com")
    print(f"🛍️  Shop:              https://norahairline.onrender.com/shop")
    print(f"👑 Admin Login:       https://norahairline.onrender.com/admin")
    print(f"📊 Admin Dashboard:   https://norahairline.onrender.com/admin/dashboard")
    print(f"🛍️  Admin Products:    https://norahairline.onrender.com/admin/products")
    print(f"📦 Admin Orders:      https://norahairline.onrender.com/admin/orders")
    print(f"➕ Add Product:        https://norahairline.onrender.com/admin/products/add")
    print(f"🔧 API:               https://norahairline.onrender.com/api")
    print(f"❤️  Health Check:      https://norahairline.onrender.com/health")
    print(f"💰 Currency:          NGN (₦ - Nigerian Naira)")
    print(f"📁 Upload:            Image/Video upload enabled")
    print(f"{'='*60}")
    
    # List available templates
    if os.path.exists('templates'):
        templates = [f for f in os.listdir('templates') if f.endswith('.html')]
        print(f"📁 Templates found: {len(templates)}")
        for template in sorted(templates):
            if template not in ['admin']:  # Skip admin folder
                print(f"   • {template}")
    
    # List admin templates
    admin_template_path = 'templates/admin'
    if os.path.exists(admin_template_path):
        admin_templates = [f for f in os.listdir(admin_template_path) if f.endswith('.html')]
        print(f"👑 Admin templates: {len(admin_templates)}")
        for template in sorted(admin_templates):
            print(f"   • admin/{template}")
    
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
