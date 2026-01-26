# reset_database.py
from main import app, db
import os

print("🔄 Resetting Nora Hair Line database...")

with app.app_context():
    try:
        # Remove old database
        if os.path.exists('norahairline.db'):
            os.remove('norahairline.db')
            print("🗑️  Removed old database")
        
        # Create all tables
        db.create_all()
        print("✅ Created all database tables")
        
        # Import and run init_database function
        from main import init_database
        init_database()
        
        print("🎉 Database reset complete!")
        print("\nAdmin Login:")
        print("📧 Email: admin@norahairline.com")
        print("🔑 Password: admin123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
