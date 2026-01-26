# reset_db.py
from main import app, db, init_database
import os

print("🔄 Resetting Nora Hair Line database...")

# Remove old database
if os.path.exists('norahairline.db'):
    os.remove('norahairline.db')
    print("🗑️ Removed old database file")

# Initialize new database
with app.app_context():
    init_database()

print("🎉 Database reset complete!")
print("\n🔑 ADMIN LOGIN CREDENTIALS:")
print("📧 Email: admin@norahairline.com")
print("🔐 Password: admin123 (CHANGE ON FIRST LOGIN)")
print("\n⚠️ IMPORTANT: Admin will be forced to change password on first login")
