#!/usr/bin/env python3
"""
Main entry point for the Legal Document Translator application.

This module initializes the Flask application using the application factory
and provides configuration for both development and production environments.
"""

import os
import argparse
from app import create_app

# Create the Flask application instance
app = create_app()

def parse_args():
    """Parse command-line arguments for the development server."""
    parser = argparse.ArgumentParser(description='Run the Legal Document Translator application')
    parser.add_argument(
        '--host',
        default=os.environ.get('HOST', '0.0.0.0'),
        help='Host to run the server on (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('PORT', 5000)),
        help='Port to run the server on (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=(os.environ.get('FLASK_DEBUG', '0') == '1'),
        help='Enable debug mode'
    )
    return parser.parse_args()

if __name__ == '__main__':
    # Only executed when running directly (not via Gunicorn)
    args = parse_args()
    
    # Configure the application for development
    app.logger.info(f"Starting development server on {args.host}:{args.port}")
    app.logger.info(f"Debug mode: {'enabled' if args.debug else 'disabled'}")
    
    # Run the development server
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_reloader=args.debug
    )
else:
    # When imported by a WSGI server like Gunicorn
    # The app instance is already created above and will be used
    app.logger.info("Application initialized for production")
