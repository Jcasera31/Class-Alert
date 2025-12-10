import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Mark that we're on Vercel before importing anything
    os.environ['VERCEL'] = 'true'
    
    from app import create_app
    # Vercel entrypoint: export Flask app object
    app = create_app()
    
except Exception as e:
    print(f"Error creating app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    
    # Create a minimal Flask app to serve error response
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    error_msg = str(e)
    
    @app.route('/')
    @app.route('/api/health')
    def error():
        return jsonify({
            "error": "App initialization failed",
            "message": error_msg
        }), 500


