from flask import Flask, render_template

app = Flask(__name__)

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Admin Panel route
@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

if __name__ == "__main__":
    app.run(debug=True)
