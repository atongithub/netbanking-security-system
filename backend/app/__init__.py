from flask import Flask, send_from_directory
from flask_cors import CORS
from app.utils import test_connection
from app.routes import auth_bp, admin_bp, crud_bp, user_bp, security_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='../../public', static_url_path='/')
    
    # Enable CORS for all routes
    CORS(app)
    
    # Register all blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(crud_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(security_bp)
    
    # Serve index.html for root path
    @app.route('/')
    def index():
        return send_from_directory('../../public', 'index.html')
    
    # Serve static files (CSS, JS, etc.)
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory('../../public', filename)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500
    
    return app
