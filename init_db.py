# init_db.py
# Helper script to initialize the database and create an admin user.
# Usage:
#   Set the ADMIN_PASSWORD env var then run: python init_db.py
#   or run without env var and you'll be prompted for a password.
import os
from getpass import getpass
from main import init_db, get_db
from werkzeug.security import generate_password_hash

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data.db")

def create_admin(username, raw_password):
    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(raw_password)
    try:
        cur.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        print(f"Admin user '{username}' created.")
    except Exception as e:
        print("Could not create admin:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    print("Initializing DB...")
    init_db()
    username = os.environ.get("ADMIN_USERNAME", "admin")
    raw_password = os.environ.get("ADMIN_PASSWORD")
    if not raw_password:
        raw_password = getpass(f"Enter password for admin '{username}': ")
        confirm = getpass("Confirm password: ")
        if raw_password != confirm:
            print("Passwords do not match. Aborting.")
            exit(1)
    create_admin(username, raw_password)
    print("Done. Set SECRET_KEY and ADMIN_PASSWORD env vars in production.")