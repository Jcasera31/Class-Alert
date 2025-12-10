from flask import Flask, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from config import Config
import os
import atexit

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()


def create_app(config_class=Config):
    """Application factory pattern"""
    # Get the parent directory (project root)
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config_class)

    # Root landing page
    @app.route('/')
    def index():
        """Root page - show demo or redirect to login"""
        if os.getenv('VERCEL'):
            # On Vercel, show demo landing page
            return render_template('landing.html')
        else:
            # Locally, redirect to dashboard or login
            from flask_login import current_user
            if current_user.is_authenticated:
                return redirect('dashboard.home')
            return redirect('auth.login')

    # Health check endpoint for Vercel
    @app.route('/api/health')
    def health():
        return jsonify({"status": "ok", "environment": "vercel" if os.getenv('VERCEL') else "local"}), 200

    # Simple info endpoint
    @app.route('/api/info')
    def info():
        return jsonify({
            "app": "ClassAlert",
            "version": "1.0.0",
            "environment": "vercel" if os.getenv('VERCEL') else "local"
        }), 200

    # Relaxed CSP to allow Stagewise proxy/devtools and websocket connections
    @app.after_request
    def add_csp_headers(response):
        csp = " ".join([
            "default-src 'self' data: blob: http://localhost:5000 http://127.0.0.1:5000 http://localhost:3100 http://127.0.0.1:3100",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "media-src 'self' data: blob:",
            "connect-src 'self' ws: wss: http://localhost:5000 http://127.0.0.1:5000 http://localhost:3100 http://127.0.0.1:3100",
            "frame-src 'self'",
        ])
        response.headers['Content-Security-Policy'] = csp
        return response

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    # Only initialize socketio in non-serverless environments
    if not os.getenv('VERCEL'):
        socketio.init_app(app, cors_allowed_origins="*")
    migrate.init_app(app, db)

    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Import and register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.schedule import bp as schedule_bp
    app.register_blueprint(schedule_bp, url_prefix='/schedule')

    from app.upload import bp as upload_bp
    app.register_blueprint(upload_bp, url_prefix='/upload')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Import models to ensure they're registered
    from app import models

    # Create database tables (only if not on Vercel)
    if not os.getenv('VERCEL'):
        with app.app_context():
            db.create_all()

    # Start the background scheduler for notifications (only in local/development)
    # Vercel serverless doesn't support background threads
    if not os.getenv('VERCEL'):
        try:
            from app.scheduler import start_scheduler, stop_scheduler
            start_scheduler(app, socketio)
            atexit.register(stop_scheduler)
        except Exception as e:
            print(f"Warning: Could not start scheduler: {e}")

    return app
