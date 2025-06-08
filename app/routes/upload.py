"""
Upload blueprint for handling PDF file uploads.

This module defines routes for:
1. Generating presigned upload URLs for Supabase Storage
2. Validating file metadata
3. Creating file and translation job records
"""

import os
import re
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

# Create blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# Configure logger
logger = logging.getLogger(__name__)

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_MIME_TYPES = {'application/pdf'}

def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_mime_type(mime_type):
    """
    Check if the MIME type is allowed.
    
    Args:
        mime_type (str): The MIME type to check
        
    Returns:
        bool: True if MIME type is allowed, False otherwise
    """
    return mime_type in ALLOWED_MIME_TYPES

def generate_secure_storage_path(original_filename):
    """
    Generate a secure and unique storage path for a file.
    
    Args:
        original_filename (str): Original filename
        
    Returns:
        str: Secure storage path
    """
    # Secure the filename
    secure_name = secure_filename(original_filename)
    
    # Generate a unique identifier
    unique_id = str(uuid.uuid4())
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract extension
    _, ext = os.path.splitext(secure_name)
    if not ext:
        ext = '.pdf'  # Default to .pdf if no extension
    
    # Create path: timestamp_uniqueid_securename.ext
    return f"{timestamp}_{unique_id}{ext}"

@upload_bp.route('/presigned-url', methods=['POST'])
def get_presigned_upload_url():
    """
    Generate a presigned URL for uploading a PDF file to Supabase Storage.
    
    Request JSON:
    {
        "filename": "document.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1024000,
        "src_lang": "gu",  # Optional, defaults to "gu"
        "tgt_lang": "en"   # Optional, defaults to "en"
    }
    
    Returns:
        JSON with presigned URL, job ID, and upload details
    """
    try:
        # Check if Supabase client is initialized
        if not hasattr(current_app, 'supabase') or current_app.supabase is None:
            logger.error("Supabase client not initialized")
            return jsonify({
                "error": "Storage service unavailable",
                "message": "Could not connect to storage service"
            }), 503
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Bad Request",
                "message": "Missing request data"
            }), 400
        
        # Validate required fields
        required_fields = ['filename', 'mime_type', 'size_bytes']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Bad Request",
                    "message": f"Missing required field: {field}"
                }), 400
        
        filename = data['filename']
        mime_type = data['mime_type']
        size_bytes = data['size_bytes']
        src_lang = data.get('src_lang', 'gu')  # Default to Gujarati
        tgt_lang = data.get('tgt_lang', 'en')  # Default to English
        
        # Validate file extension
        if not allowed_file(filename):
            return jsonify({
                "error": "Invalid File",
                "message": "Only PDF files are allowed"
            }), 400
        
        # Validate MIME type
        if not allowed_mime_type(mime_type):
            return jsonify({
                "error": "Invalid File",
                "message": "Invalid MIME type. Only application/pdf is allowed"
            }), 400
        
        # Validate file size
        max_size = current_app.config['MAX_CONTENT_LENGTH']
        if size_bytes > max_size:
            return jsonify({
                "error": "File Too Large",
                "message": f"File exceeds maximum allowed size of {max_size / (1024 * 1024)}MB"
            }), 413
        
        # Generate secure storage path
        bucket = current_app.config['UPLOADS_BUCKET']
        storage_path = generate_secure_storage_path(filename)
        
        # Get user ID if authentication is enabled
        user_id = None
        # If auth is implemented, get user_id from session/token
        
        # Create file record in database
        from app.services.supabase_client import SupabaseClient
        supabase = SupabaseClient(
            current_app.config['SUPABASE_URL'],
            current_app.config['SUPABASE_SERVICE_KEY']
        )
        
        # Create file and job records in a single operation
        job = supabase.create_translation_job_with_file(
            original_name=filename,
            bucket=bucket,
            storage_path=storage_path,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            user_id=user_id
        )
        
        # Generate presigned upload URL
        upload_url_data = supabase.get_upload_signed_url(
            bucket=bucket,
            path=storage_path,
            expires_in=60  # URL expires in 60 seconds
        )
        
        # Return response with presigned URL and job ID
        return jsonify({
            "job_id": job["id"],
            "upload_url": upload_url_data["signed_url"],
            "file_id": job["file"]["id"],
            "storage_path": storage_path,
            "expires_in": 60,  # seconds
            "bucket": bucket
        }), 200
        
    except Exception as e:
        logger.exception(f"Error generating presigned URL: {str(e)}")
        return jsonify({
            "error": "Server Error",
            "message": "Failed to generate upload URL"
        }), 500

@upload_bp.route('/validate', methods=['POST'])
def validate_file():
    """
    Validate file metadata without generating a presigned URL.
    Useful for client-side validation before attempting upload.
    
    Request JSON:
    {
        "filename": "document.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1024000
    }
    
    Returns:
        JSON with validation result
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Bad Request",
                "message": "Missing request data"
            }), 400
        
        # Validate required fields
        required_fields = ['filename', 'mime_type', 'size_bytes']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": "Bad Request",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        filename = data['filename']
        mime_type = data['mime_type']
        size_bytes = data['size_bytes']
        
        # Validate file extension
        if not allowed_file(filename):
            return jsonify({
                "valid": False,
                "error": "Invalid file extension",
                "message": "Only PDF files are allowed"
            }), 200
        
        # Validate MIME type
        if not allowed_mime_type(mime_type):
            return jsonify({
                "valid": False,
                "error": "Invalid MIME type",
                "message": "Only application/pdf is allowed"
            }), 200
        
        # Validate file size
        max_size = current_app.config['MAX_CONTENT_LENGTH']
        if size_bytes > max_size:
            return jsonify({
                "valid": False,
                "error": "File too large",
                "message": f"File exceeds maximum allowed size of {max_size / (1024 * 1024)}MB"
            }), 200
        
        # All validations passed
        return jsonify({
            "valid": True,
            "message": "File is valid"
        }), 200
        
    except Exception as e:
        logger.exception(f"Error validating file: {str(e)}")
        return jsonify({
            "error": "Server Error",
            "message": "Failed to validate file"
        }), 500
