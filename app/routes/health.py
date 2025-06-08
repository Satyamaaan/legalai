"""
Health check routes for the Legal Document Translator.

This module provides health check endpoints for monitoring the application status.
"""

from flask import Blueprint, jsonify, current_app

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the application is running.
    
    Returns:
    {
        "status": "healthy",
        "environment": "development",
        "supabase": "connected"
    }
    """
    supabase_status = "connected" if hasattr(current_app, 'supabase') and current_app.supabase else "not connected"
    
    return jsonify({
        "status": "healthy",
        "environment": current_app.config.get('ENV', 'unknown'),
        "supabase": supabase_status
    }), 200

@health_bp.route('/status', methods=['GET'])
def status_check():
    """
    Detailed status check with service information.
    
    Returns detailed information about the application and its services.
    """
    services = {}
    
    # Check Supabase
    if hasattr(current_app, 'supabase') and current_app.supabase:
        services['supabase'] = {
            "status": "connected",
            "url": current_app.config.get('SUPABASE_URL', 'not configured')
        }
    else:
        services['supabase'] = {
            "status": "not connected",
            "url": current_app.config.get('SUPABASE_URL', 'not configured')
        }
    
    # Check configuration
    config_status = {
        "upload_folder": current_app.config.get('UPLOAD_FOLDER'),
        "temp_pdf_dir": current_app.config.get('TEMP_PDF_DIR'),
        "max_content_length": current_app.config.get('MAX_CONTENT_LENGTH'),
        "sarvam_configured": bool(current_app.config.get('SARVAM_API_KEY'))
    }
    
    return jsonify({
        "status": "healthy",
        "environment": current_app.config.get('ENV', 'unknown'),
        "services": services,
        "configuration": config_status
    }), 200 