"""
Flask application factory module.

This module provides the application factory function for creating Flask app
instances with proper configuration, extensions, and blueprint registration.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config (dict, optional): Test configuration to override default configs.
    
    Returns:
        Flask: Configured Flask application instance.
    """
    # Create Flask app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
        UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER', './tmp/uploads'),
        MAX_CONTENT_LENGTH=int(os.environ.get('MAX_CONTENT_LENGTH', 20 * 1024 * 1024)),  # 20MB default
        SUPABASE_URL=os.environ.get('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.environ.get('SUPABASE_ANON_KEY'),
        SUPABASE_SERVICE_KEY=os.environ.get('SUPABASE_SERVICE_KEY'),
        UPLOADS_BUCKET=os.environ.get('UPLOADS_BUCKET', 'uploads'),
        OUTPUTS_BUCKET=os.environ.get('OUTPUTS_BUCKET', 'outputs'),
        SARVAM_API_KEY=os.environ.get('SARVAM_API_KEY'),
        SARVAM_API_URL=os.environ.get('SARVAM_API_URL', 'https://api.sarvam.ai/v1'),
        SARVAM_MAX_CHARS=int(os.environ.get('SARVAM_MAX_CHARS', 1000)),
        ENV=os.environ.get('ENV', 'development'),
        TESSERACT_PATH=os.environ.get('TESSERACT_PATH', ''),
        TEMP_PDF_DIR=os.environ.get('TEMP_PDF_DIR', './tmp/pdfs')
    )
    
    # Override config with test config if provided
    if test_config is not None:
        app.config.update(test_config)
    
    # Ensure upload and temp directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_PDF_DIR'], exist_ok=True)
    
    # Configure CORS
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    
    # Initialize Supabase client
    @app.before_first_request
    def init_supabase():
        """Initialize Supabase client before first request."""
        if not app.config['SUPABASE_URL'] or not app.config['SUPABASE_SERVICE_KEY']:
            app.logger.warning("Supabase credentials not set. Storage and database features will not work.")
            app.supabase = None
        else:
            try:
                app.supabase = create_client(
                    app.config['SUPABASE_URL'],
                    app.config['SUPABASE_SERVICE_KEY']
                )
                app.logger.info("Supabase client initialized successfully.")
            except Exception as e:
                app.logger.error(f"Failed to initialize Supabase client: {str(e)}")
                app.supabase = None
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Proof of life route
    @app.route('/health')
    def health_check():
        """Health check endpoint to verify the app is running."""
        supabase_status = "connected" if app.supabase else "not connected"
        return jsonify({
            "status": "healthy",
            "environment": app.config['ENV'],
            "supabase": supabase_status
        })
    
    return app

def configure_logging(app):
    """
    Configure application logging based on environment.
    
    Args:
        app (Flask): Flask application instance.
    """
    log_level_name = os.environ.get('LOG_LEVEL', 'DEBUG')
    log_level = getattr(logging, log_level_name)
    
    if app.config['ENV'] == 'production':
        # In production, log to file with rotation
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        file_handler = RotatingFileHandler(
            'logs/legalai.log', 
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
    else:
        # In development, log to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(console_handler)
    
    app.logger.setLevel(log_level)
    app.logger.info(f'LegalAI startup with {app.config["ENV"]} configuration')

def register_blueprints(app):
    """
    Register Flask blueprints.
    
    Args:
        app (Flask): Flask application instance.
    """
    # Import blueprints here to avoid circular imports
    try:
        from app.routes.upload import upload_bp
        app.register_blueprint(upload_bp)
        app.logger.info("Registered upload blueprint")
    except ImportError:
        app.logger.warning("Upload blueprint not found or failed to load")
    
    try:
        from app.routes.translate import translate_bp
        app.register_blueprint(translate_bp)
        app.logger.info("Registered translate blueprint")
    except ImportError:
        app.logger.warning("Translate blueprint not found or failed to load")
    
    try:
        from app.routes.download import download_bp
        app.register_blueprint(download_bp)
        app.logger.info("Registered download blueprint")
    except ImportError:
        app.logger.warning("Download blueprint not found or failed to load")
    
        try:
        from app.routes.health import health_bp
        app.register_blueprint(health_bp)
        app.logger.info("Registered health blueprint")
    except ImportError:
        app.logger.warning("Health blueprint not found or failed to load")

def register_error_handlers(app):
    """
    Register custom error handlers.
    
    Args:
        app (Flask): Flask application instance.
    """
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            "error": "Bad Request",
            "message": str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found."
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            "error": "File Too Large",
            "message": f"The file exceeds the maximum allowed size of {app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)}MB."
        }), 413
    
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Server Error: {str(error)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }), 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        app.logger.error(f"Unhandled Exception: {str(error)}")
        return jsonify({
            "error": "Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }), 500

