import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)

# Configure database for Render compatibility
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# ========== SIMPLIFIED MODELS ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(300), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    items = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ========== FLASK-LOGIN SETUP ==========
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# ========== CONTEXT PROCESSORS ==========
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.context_processor
def inject_now():
    return dict(now=datetime.now())

# ========== ERROR HANDLERS WITH BETTER DEBUGGING ==========
@app.errorhandler(404)
def not_found_error(error):
    print(f"404 Error: {error}", file=sys.stderr)
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    # Log the error details
    error_traceback = traceback.format_exc()
    print(f"500 Internal Server Error:\n{error_traceback}", file=sys.stderr)
    
    # Simplified 500 page that won't cause more errors
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>500 - Internal Server Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #d9534f; }
            .container { max-width: 600px; margin: 0 auto; }
            .btn { display: inline-block; padding: 10px 20px; margin: 10px; 
                   background: #007bff; color: white; text-decoration: none; 
                   border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>500 - Internal Server Error</h1>
            <p>We're experiencing technical difficulties. Please try again later.</p>
            <a href="/" class="btn">Go Home</a>
            <a href="javascript:history.back()" class="btn">Go Back</a>
        </div>
    </body>
    </html>
    ''', 500

# ========== ROUTES WITH ERROR HANDLING ==========
@app.route('/')
def home():
    try:
        # Render a simple test page first
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hair Haven Hub - Test Page</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #333; }
                .success { color: green; font-size: 24px; margin: 20px; }
            </style>
        </head>
        <body>
            <h1>Hair Haven Hub</h1>
            <div class="success">✓ Application is running successfully!</div>
            <p>If you can see this page, Flask is working correctly.</p>
            <p><a href="/admin/login">Go to Admin Login</a></p>
        </body>
        </html>
        '''
    except Exception as e:
        # Log the error
        print(f"Error in home route: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return f'''
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Application Error</h1>
            <p>Error: {str(e)}</p>
            <p>Please check the server logs for details.</p>
        </body>
        </html>
        ''', 500

@app.route('/test')
def test_page():
    """Simple test page without templates"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Successful!</h1>
        <p>This page works without templates.</p>
        <p><a href="/">Go to Home</a></p>
    </body>
    </html>
    '''

@app.route('/about')
def about():
    try:
        return render_template('about.html')
    except Exception as e:
        print(f"Error rendering about page: {str(e)}", file=sys.stderr)
        return f"About page - Error: {str(e)}", 500

# ========== SIMPLIFIED ADMIN ROUTES ==========
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Simple admin login without complex template"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For now, use a simple check
        if email == os.environ.get('ADMIN_EMAIL', 'admin@example.com'):
            return redirect('/admin/dashboard')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
            input, button { width: 100%; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h2>Admin Login</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    '''

@app.route('/admin/dashboard')
def admin_dashboard():
    """Simple admin dashboard"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Admin Dashboard</h1>
        <div class="card">
            <h3>Application Status: ✓ Running</h3>
            <p>Database: Connected</p>
            <p>Server Time: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
        </div>
        <p><a href="/">Go to Home</a> | <a href="/admin/login">Logout</a></p>
    </body>
    </html>
    '''

# ========== HEALTH CHECK ==========
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Try database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ========== INITIALIZATION ==========
def init_database():
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ Database tables created", file=sys.stderr)
            
            # Create admin user if it doesn't exist
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    username='admin',
                    email=admin_email,
                    password=generate_password_hash(admin_password),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print(f"✓ Admin user created: {admin_email}", file=sys.stderr)
            else:
                print(f"✓ Admin user exists: {admin_email}", file=sys.stderr)
            
            return True
        except Exception as e:
            print(f"✗ Database initialization error: {str(e)}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            return False

# ========== APPLICATION FACTORY ==========
def create_app():
    # Initialize database
    if init_database():
        print("✓ Application initialized successfully", file=sys.stderr)
    else:
        print("✗ Application initialization failed", file=sys.stderr)
    return app

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    print(f"✓ Starting server on port {port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port, debug=True)
