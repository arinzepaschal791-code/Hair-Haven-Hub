# wsgi.py - Production entry point for gunicorn
import sys
import os
import types

# ========== ULTIMATE PYTHON 3.13 COMPATIBILITY PATCHES ==========
# These must run BEFORE any other imports

print("🚀 Initializing Python 3.13 compatibility patches...", file=sys.stderr)

# FIX 1: Comprehensive mock for gunicorn.six.moves
class SixMock:
    class moves:
        class urllib:
            class parse:
                @staticmethod
                def urlsplit(url):
                    from urllib.parse import urlsplit
                    return urlsplit(url)
                
                @staticmethod
                def urljoin(base, url):
                    from urllib.parse import urljoin
                    return urljoin(base, url)
                
                @staticmethod
                def urlparse(url):
                    from urllib.parse import urlparse
                    return urlparse(url)

# Install the mock
sys.modules['gunicorn.six'] = SixMock
sys.modules['gunicorn.six.moves'] = SixMock.moves
sys.modules['gunicorn.six.moves.urllib'] = SixMock.moves.urllib
sys.modules['gunicorn.six.moves.urllib.parse'] = SixMock.moves.urllib.parse
print("✅ Installed gunicorn.six mock", file=sys.stderr)

# FIX 2: Mock pkg_resources for setuptools
if 'pkg_resources' not in sys.modules:
    mock_pkg_resources = types.ModuleType('pkg_resources')
    mock_pkg_resources.working_set = type('WorkingSet', (), {
        'entry_keys': {},
        'entries': [],
        'by_key': {},
        '__iter__': lambda self: iter([])
    })()
    mock_pkg_resources.require = lambda *a, **kw: []
    mock_pkg_resources.get_distribution = lambda *a, **kw: None
    mock_pkg_resources.iter_entry_points = lambda *a, **kw: []
    mock_pkg_resources.resource_filename = lambda *a, **kw: ''
    mock_pkg_resources.resource_string = lambda *a, **kw: b''
    mock_pkg_resources.resource_stream = lambda *a, **kw: open(os.devnull, 'rb')
    sys.modules['pkg_resources'] = mock_pkg_resources
    print("✅ Installed mock pkg_resources", file=sys.stderr)

# FIX 3: Pre-import and patch SQLAlchemy
try:
    import sqlalchemy
    print(f"✅ SQLAlchemy {sqlalchemy.__version__} pre-imported", file=sys.stderr)
    
    # Apply TypingOnly patch
    import sqlalchemy.util.langhelpers
    original_init_subclass = sqlalchemy.util.langhelpers.TypingOnly.__init_subclass__
    
    def patched_init_subclass(cls, *args, **kwargs):
        for attr in ['__static_attributes__', '__firstlineno__', '__classcell__']:
            if hasattr(cls, attr):
                delattr(cls, attr)
        return original_init_subclass.__func__(cls, *args, **kwargs)
    
    sqlalchemy.util.langhelpers.TypingOnly.__init_subclass__ = classmethod(patched_init_subclass)
    print("✅ Applied SQLAlchemy TypingOnly patch", file=sys.stderr)
except ImportError:
    pass
except Exception as e:
    print(f"⚠️ SQLAlchemy patch warning: {e}", file=sys.stderr)

print("🚀 Compatibility patches applied successfully!\n", file=sys.stderr)

# ========== NOW IMPORT THE ACTUAL APPLICATION ==========
# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from main
try:
    from main import app
    print("✅ Flask application imported successfully", file=sys.stderr)
except Exception as e:
    print(f"❌ Failed to import Flask application: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise

# Export the app for gunicorn
if __name__ == "__main__":
    app.run()
