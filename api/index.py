import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import create_app
    # Vercel entrypoint: export Flask app object
    app = create_app()
except Exception as e:
    print(f"Error creating app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    # Create a minimal Flask app to serve error
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return jsonify({"error": str(e)}), 500

