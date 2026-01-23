# main.py
# Flask e-commerce app with simple admin panel, product CRUD, reviews, and orders.
# Deployable with: gunicorn main:app
import os
import sqlite3
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session,
    send_from_directory, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "data.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Environment-configurable secrets
SECRET_KEY = os.environ.get("SECRET_KEY", "change_me_in_production")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")  # default 'admin' if not set

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=4 * 1024 * 1024  # 4MB upload limit
)

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Database helpers
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Products, Reviews, Orders, Admin
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        image_filename TEXT,
        stock INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        name TEXT,
        rating INTEGER,
        comment TEXT,
        approved INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        items_json TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

# Utility
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file_storage):
    if file_storage and allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        # Ensure unique filename by prefixing timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        filename = f"{timestamp}_{filename}"
        dest = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file_storage.save(dest)
        return filename
    return None

# Admin auth helpers
def is_logged_in():
    return session.get("admin_logged_in")

def login_admin(username):
    session["admin_logged_in"] = True
    session["admin_username"] = username

def logout_admin():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)

# Routes
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    category = request.args.get("category")
    if category:
        cur.execute("SELECT * FROM products WHERE category = ? ORDER BY created_at DESC", (category,))
    else:
        cur.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cur.fetchall()
    categories = ["Bone Straight Wigs", "Curly Wigs", "Hair Creams", "Hair Shampoos"]
    conn.close()
    return render_template("index.html", products=products, categories=categories, selected_category=category)

@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_detail(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    if not product:
        conn.close()
        abort(404)
    # Handle review submission
    if request.method == "POST":
        name = request.form.get("name", "Anonymous")
        rating = int(request.form.get("rating", 5))
        comment = request.form.get("comment", "")
        cur.execute(
            "INSERT INTO reviews (product_id, name, rating, comment, approved, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, name, rating, comment, 0, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        flash("Thanks! Your review is submitted and awaits moderation.", "success")
        return redirect(url_for("product_detail", product_id=product_id))
    # GET -> show product and approved reviews
    cur.execute("SELECT * FROM reviews WHERE product_id = ? AND approved = 1 ORDER BY created_at DESC", (product_id,))
    reviews = cur.fetchall()
    conn.close()
    return render_template("product.html", product=product, reviews=reviews)

@app.route("/cart", methods=["GET", "POST"])
def cart():
    # Simple client-side cart for demo: store in session
    cart = session.get("cart", {})
    if request.method == "POST":
        # place order
        customer_name = request.form.get("name")
        email = request.form.get("email")
        address = request.form.get("address")
        if not (customer_name and email and address and cart):
            flash("Provide name, email, address and have items in cart.", "danger")
            return redirect(url_for("cart"))
        conn = get_db()
        cur = conn.cursor()
        items_json = json.dumps(cart)
        cur.execute(
            "INSERT INTO orders (customer_name, email, address, items_json, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_name, email, address, items_json, "pending", datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        session.pop("cart", None)
        flash("Order placed! Admin will update order status.", "success")
        return redirect(url_for("index"))
    # display cart
    # Build product details for items
    conn = get_db()
    cur = conn.cursor()
    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except:
            continue
        cur.execute("SELECT * FROM products WHERE id = ?", (pid,))
        prod = cur.fetchone()
        if prod:
            subtotal = prod["price"] * int(qty)
            total += subtotal
            items.append({"product": prod, "qty": int(qty), "subtotal": subtotal})
    conn.close()
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    qty = int(request.form.get("quantity", 1))
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session["cart"] = cart
    flash("Added to cart", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def cart_remove(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Removed from cart", "info")
    return redirect(url_for("cart"))

# Admin routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin WHERE username = ?", (username,))
        admin = cur.fetchone()
        conn.close()
        if admin and check_password_hash(admin["password_hash"], password):
            login_admin(username)
            flash("Welcome, admin.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("admin_login"))
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    logout_admin()
    flash("Logged out", "info")
    return redirect(url_for("index"))

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash("Admin login required", "warning")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM products")
    product_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'pending'")
    pending_orders = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM reviews WHERE approved = 0")
    pending_reviews = cur.fetchone()["cnt"]
    conn.close()
    return render_template("admin.html", product_count=product_count, pending_orders=pending_orders, pending_reviews=pending_reviews)

# Product management
@app.route("/admin/products")
@admin_required
def admin_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cur.fetchall()
    conn.close()
    return render_template("admin_products.html", products=products)

@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def admin_product_add():
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        description = request.form.get("description")
        price = float(request.form.get("price") or 0)
        stock = int(request.form.get("stock") or 0)
        file = request.files.get("image")
        filename = save_file(file) if file else None
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, category, description, price, image_filename, stock, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, category, description, price, filename, stock, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        flash("Product added.", "success")
        return redirect(url_for("admin_products"))
    categories = ["Bone Straight Wigs", "Curly Wigs", "Hair Creams", "Hair Shampoos"]
    return render_template("admin_product_form.html", action="Add", categories=categories, product=None)

@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    if not product:
        conn.close()
        flash("Product not found.", "danger")
        return redirect(url_for("admin_products"))
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        description = request.form.get("description")
        price = float(request.form.get("price") or 0)
        stock = int(request.form.get("stock") or 0)
        file = request.files.get("image")
        filename = save_file(file) if (file and file.filename) else product["image_filename"]
        cur.execute(
            "UPDATE products SET name=?, category=?, description=?, price=?, image_filename=?, stock=? WHERE id=?",
            (name, category, description, price, filename, stock, product_id)
        )
        conn.commit()
        conn.close()
        flash("Product updated.", "success")
        return redirect(url_for("admin_products"))
    conn.close()
    categories = ["Bone Straight Wigs", "Curly Wigs", "Hair Creams", "Hair Shampoos"]
    return render_template("admin_product_form.html", action="Edit", product=product, categories=categories)

@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted.", "info")
    return redirect(url_for("admin_products"))

# Orders management
@app.route("/admin/orders")
@admin_required
def admin_orders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    conn.close()
    return render_template("admin_orders.html", orders=orders)

@app.route("/admin/orders/update/<int:order_id>", methods=["POST"])
@admin_required
def admin_order_update(order_id):
    new_status = request.form.get("status")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    flash("Order status updated.", "success")
    return redirect(url_for("admin_orders"))

# Reviews moderation
@app.route("/admin/reviews")
@admin_required
def admin_reviews():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT r.*, p.name as product_name FROM reviews r LEFT JOIN products p ON r.product_id = p.id ORDER BY r.created_at DESC")
    reviews = cur.fetchall()
    conn.close()
    return render_template("admin_reviews.html", reviews=reviews)

@app.route("/admin/reviews/approve/<int:review_id>", methods=["POST"])
@admin_required
def admin_review_approve(review_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE reviews SET approved = 1 WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review approved.", "success")
    return redirect(url_for("admin_reviews"))

@app.route("/admin/reviews/delete/<int:review_id>", methods=["POST"])
@admin_required
def admin_review_delete(review_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review deleted.", "info")
    return redirect(url_for("admin_reviews"))

# Serve uploaded images
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Initialize DB if needed
@app.before_first_request
def ensure_db():
    init_db()

# Simple health endpoint
@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    # For local development only. Use gunicorn for production on Render.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
