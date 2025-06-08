"""
Upload route handlers for the Legal Document Translator.

This module handles file upload endpoints, generates signed URLs for
direct upload to Supabase Storage, and creates database records.
"""

import os
import uuid
import logging
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.services.supabase_client import SupabaseClient, SupabaseClientError

logger = logging.getLogger(__name__)

# Create blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_supabase_client() -> SupabaseClient:
    """Get Supabase client from Flask app context."""
    if not hasattr(current_app, 'supabase') or current_app.supabase is None:
        raise SupabaseClientError("Supabase client not initialized")
    
    return SupabaseClient(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_SERVICE_KEY']
    )

@upload_bp.route('/signed-url', methods=['POST'])
def get_upload_signed_url():
    """
    Generate a signed URL for file upload.
    
    Expected JSON payload:
    {
        "filename": "document.pdf",
        "content_type": "application/pdf"
    }
    
    Returns:
    {
        "upload_url": "https://...",
        "file_id": "uuid",
        "job_id": "uuid"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        filename = data.get('filename')
        content_type = data.get('content_type', 'application/pdf')
        
        if not filename:
            return jsonify({"error": "filename is required"}), 400
        
        # Validate file extension
        if not allowed_file(filename):
            return jsonify({
                "error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Secure the filename
        secure_name = secure_filename(filename)
        if not secure_name:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Generate unique storage path
        storage_path = supabase.generate_storage_path("uploads", secure_name)
        
        # Generate signed upload URL
        upload_result = supabase.get_upload_signed_url(
            bucket=current_app.config['UPLOADS_BUCKET'],
            path=storage_path,
            expires_in=300  # 5 minutes
        )
        
        # Create file and job records
        job_data = supabase.create_translation_job_with_file(
            original_name=filename,
            bucket=current_app.config['UPLOADS_BUCKET'],
            storage_path=storage_path,
            src_lang=data.get('src_lang', 'gu'),
            tgt_lang=data.get('tgt_lang', 'en')
        )
        
        return jsonify({
            "upload_url": upload_result["signed_url"],
            "file_id": job_data["file"]["id"],
            "job_id": job_data["id"],
            "storage_path": storage_path
        }), 200
        
    except SupabaseClientError as e:
        logger.error(f"Supabase error in upload endpoint: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@upload_bp.route('/confirm', methods=['POST'])
def confirm_upload():
    """
    Confirm that file upload was successful and start processing.
    
    Expected JSON payload:
    {
        "job_id": "uuid"
    }
    
    Returns:
    {
        "job_id": "uuid",
        "status": "processing"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        job_id = data.get('job_id')
        if not job_id:
            return jsonify({"error": "job_id is required"}), 400
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Update job status to processing
        updated_job = supabase.update_job_progress(
            job_id=job_id,
            progress=5,
            status="processing"
        )
        
        # TODO: Trigger background processing job here
        # This will be implemented when we create the job orchestrator
        
        return jsonify({
            "job_id": job_id,
            "status": updated_job["status"],
            "progress": updated_job["progress"]
        }), 200
        
    except SupabaseClientError as e:
        logger.error(f"Supabase error in confirm upload: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in confirm upload: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@upload_bp.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    """
    Get the status of a translation job.
    
    Returns:
    {
        "job_id": "uuid",
        "status": "processing",
        "progress": 45,
        "file": {...}
    }
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get job with file data
        job_data = supabase.get_job_with_file(job_id)
        
        return jsonify({
            "job_id": job_data["id"],
            "status": job_data["status"],
            "progress": job_data["progress"],
            "src_lang": job_data["src_lang"],
            "tgt_lang": job_data["tgt_lang"],
            "error_message": job_data.get("error_message"),
            "created_at": job_data["created_at"],
            "updated_at": job_data["updated_at"],
            "file": {
                "id": job_data["files"]["id"],
                "original_name": job_data["files"]["original_name"],
                "created_at": job_data["files"]["created_at"]
            }
        }), 200
        
    except SupabaseClientError as e:
        logger.error(f"Supabase error getting job status: {str(e)}")
        return jsonify({"error": "Job not found or database error"}), 404
    
    except Exception as e:
        logger.error(f"Unexpected error getting job status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Health check for the upload blueprint
@upload_bp.route('/health', methods=['GET'])
def upload_health():
    """Health check endpoint for upload service."""
    try:
        supabase = get_supabase_client()
        return jsonify({
            "status": "healthy",
            "service": "upload",
            "supabase": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "upload",
            "error": str(e)
        }), 500