# wsgi.py - Production entry point
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app from main
from main import app

if __name__ == "__main__":
    app.run()
