from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong key

DATABASE = "database.db"

# --- Database helper ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Home page ---
@app.route("/")
def index():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products)

# --- Product details ---
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        flash("Product not found", "warning")
        return redirect(url_for("index"))
    return render_template("product_detail.html", product=product)

# --- Admin login ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Replace with your real credentials or DB check
        if username == "admin" and password == "password":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("admin/login.html")

# --- Admin logout ---
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

# --- Admin dashboard ---
@app.route("/admin")
def admin_dashboard():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM products")
    product_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status = 'pending'")
    pending_orders_count = cur.fetchone()["cnt"]
    conn.close()
    return render_template(
        "admin/dashboard.html",
        product_count=product_count,
        pending_orders_count=pending_orders_count
    )

# --- Admin: view products ---
@app.route("/admin/products")
def admin_products():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("admin/products.html", products=products)

# --- Admin: add product ---
@app.route("/admin/products/add", methods=["GET", "POST"])
def add_product():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            (name, price, description)
        )
        conn.commit()
        conn.close()
        flash("Product added successfully", "success")
        return redirect(url_for("admin_products"))
    return render_template("admin/add_product.html")

# --- Admin: edit product ---
@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found", "warning")
        return redirect(url_for("admin_products"))
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
        conn.execute(
            "UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?",
            (name, price, description, product_id)
        )
        conn.commit()
        conn.close()
        flash("Product updated successfully", "success")
        return redirect(url_for("admin_products"))
    conn.close()
    return render_template("admin/edit_product.html", product=product)

# --- Admin: delete product ---
@app.route("/admin/products/delete/<int:product_id>")
def delete_product(product_id):
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted successfully", "success")
    return redirect(url_for("admin_products"))

# --- Admin: view orders ---
@app.route("/admin/orders")
def admin_orders():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin/orders.html", orders=orders)

# --- Admin: update order status ---
@app.route("/admin/orders/update/<int:order_id>", methods=["POST"])
def update_order(order_id):
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    status = request.form["status"]
    conn = get_db_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    flash("Order status updated", "success")
    return redirect(url_for("admin_orders"))

# --- Run server ---
if __name__ == "__main__":
    app.run(debug=True)
