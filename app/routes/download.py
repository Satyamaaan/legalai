"""
Download route handlers for the Legal Document Translator.

This module handles download endpoints for translated PDFs,
generates signed URLs for secure downloads from Supabase Storage.
"""

import logging
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, current_app, redirect

from app.services.supabase_client import SupabaseClient, SupabaseClientError

logger = logging.getLogger(__name__)

# Create blueprint
download_bp = Blueprint('download', __name__, url_prefix='/api/download')

def get_supabase_client() -> SupabaseClient:
    """Get Supabase client from Flask app context."""
    if not hasattr(current_app, 'supabase') or current_app.supabase is None:
        raise SupabaseClientError("Supabase client not initialized")
    
    return SupabaseClient(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_SERVICE_KEY']
    )

@download_bp.route('/job/<job_id>', methods=['GET'])
def download_by_job_id(job_id: str):
    """
    Get download URL for a completed translation job.
    
    Args:
        job_id: UUID of the translation job
        
    Returns:
        JSON response with download URL or redirect to download
    """
    try:
        # Get query parameters
        redirect_download = request.args.get('redirect', 'false').lower() == 'true'
        expires_in = int(request.args.get('expires', 3600))  # Default 1 hour
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get job with file data
        job_data = supabase.get_job_with_file(job_id)
        
        # Check job status
        if job_data['status'] != 'done':
            return jsonify({
                "error": f"Job is not complete. Current status: {job_data['status']}",
                "job_id": job_id,
                "status": job_data['status'],
                "progress": job_data.get('progress', 0)
            }), 400
        
        # Check if output file exists
        output_file_id = job_data.get('output_file_id')
        if not output_file_id:
            return jsonify({
                "error": "No output file available for this job",
                "job_id": job_id
            }), 404
        
        # Get output file details
        output_file = supabase.get_file_by_id(output_file_id)
        
        # Generate download URL
        download_url = supabase.get_download_signed_url(
            bucket=output_file['bucket'],
            path=output_file['storage_path'],
            expires_in=expires_in,
            download_name=output_file['original_name']
        )
        
        # Return URL or redirect
        if redirect_download:
            return redirect(download_url)
        else:
            return jsonify({
                "download_url": download_url,
                "filename": output_file['original_name'],
                "file_id": output_file_id,
                "expires_in": expires_in,
                "job_id": job_id
            }), 200
            
    except SupabaseClientError as e:
        logger.error(f"Supabase error in download endpoint: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in download endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_bp.route('/file/<file_id>', methods=['GET'])
def download_by_file_id(file_id: str):
    """
    Get download URL for a specific file.
    
    Args:
        file_id: UUID of the file
        
    Returns:
        JSON response with download URL or redirect to download
    """
    try:
        # Get query parameters
        redirect_download = request.args.get('redirect', 'false').lower() == 'true'
        expires_in = int(request.args.get('expires', 3600))  # Default 1 hour
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get file details
        file_data = supabase.get_file_by_id(file_id)
        
        # Verify this is an output file (security check)
        if file_data['bucket'] != current_app.config['OUTPUTS_BUCKET']:
            return jsonify({
                "error": "File not available for download"
            }), 403
        
        # Generate download URL
        download_url = supabase.get_download_signed_url(
            bucket=file_data['bucket'],
            path=file_data['storage_path'],
            expires_in=expires_in,
            download_name=file_data['original_name']
        )
        
        # Return URL or redirect
        if redirect_download:
            return redirect(download_url)
        else:
            return jsonify({
                "download_url": download_url,
                "filename": file_data['original_name'],
                "file_id": file_id,
                "expires_in": expires_in
            }), 200
            
    except SupabaseClientError as e:
        logger.error(f"Supabase error getting file for download: {str(e)}")
        return jsonify({"error": "File not found or database error"}), 404
    
    except Exception as e:
        logger.error(f"Unexpected error in file download: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_bp.route('/preview/<job_id>', methods=['GET'])
def preview_translated_file(job_id: str):
    """
    Get a preview/info about the translated file without downloading.
    
    Args:
        job_id: UUID of the translation job
        
    Returns:
        JSON response with file information
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get job with file data
        job_data = supabase.get_job_with_file(job_id)
        
        # Check job status
        if job_data['status'] != 'done':
            return jsonify({
                "error": f"Job is not complete. Current status: {job_data['status']}",
                "job_id": job_id,
                "status": job_data['status'],
                "progress": job_data.get('progress', 0)
            }), 400
        
        # Check if output file exists
        output_file_id = job_data.get('output_file_id')
        if not output_file_id:
            return jsonify({
                "error": "No output file available for this job",
                "job_id": job_id
            }), 404
        
        # Get output file details
        output_file = supabase.get_file_by_id(output_file_id)
        
        # Get original file details
        original_file = job_data['files']
        
        return jsonify({
            "job_id": job_id,
            "status": job_data['status'],
            "progress": job_data['progress'],
            "created_at": job_data['created_at'],
            "updated_at": job_data['updated_at'],
            "translation": {
                "source_language": job_data['src_lang'],
                "target_language": job_data['tgt_lang']
            },
            "original_file": {
                "id": original_file['id'],
                "name": original_file['original_name'],
                "size_bytes": original_file.get('size_bytes'),
                "created_at": original_file['created_at']
            },
            "translated_file": {
                "id": output_file['id'],
                "name": output_file['original_name'],
                "size_bytes": output_file.get('size_bytes'),
                "created_at": output_file['created_at']
            }
        }), 200
        
    except SupabaseClientError as e:
        logger.error(f"Supabase error in preview endpoint: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in preview endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_bp.route('/bulk', methods=['POST'])
def bulk_download_urls():
    """
    Generate download URLs for multiple jobs at once.
    
    Expected JSON payload:
    {
        "job_ids": ["uuid1", "uuid2", ...],
        "expires_in": 3600  # optional
    }
    
    Returns:
        JSON response with download URLs for each job
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        job_ids = data.get('job_ids', [])
        expires_in = data.get('expires_in', 3600)
        
        if not job_ids or not isinstance(job_ids, list):
            return jsonify({"error": "job_ids must be a non-empty list"}), 400
        
        if len(job_ids) > 50:  # Limit to prevent abuse
            return jsonify({"error": "Maximum 50 jobs per request"}), 400
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        results = []
        errors = []
        
        for job_id in job_ids:
            try:
                # Get job with file data
                job_data = supabase.get_job_with_file(job_id)
                
                if job_data['status'] != 'done':
                    errors.append({
                        "job_id": job_id,
                        "error": f"Job not complete: {job_data['status']}"
                    })
                    continue
                
                # Check if output file exists
                output_file_id = job_data.get('output_file_id')
                if not output_file_id:
                    errors.append({
                        "job_id": job_id,
                        "error": "No output file available"
                    })
                    continue
                
                # Get output file details
                output_file = supabase.get_file_by_id(output_file_id)
                
                # Generate download URL
                download_url = supabase.get_download_signed_url(
                    bucket=output_file['bucket'],
                    path=output_file['storage_path'],
                    expires_in=expires_in,
                    download_name=output_file['original_name']
                )
                
                results.append({
                    "job_id": job_id,
                    "download_url": download_url,
                    "filename": output_file['original_name'],
                    "file_id": output_file_id
                })
                
            except Exception as e:
                errors.append({
                    "job_id": job_id,
                    "error": str(e)
                })
        
        return jsonify({
            "results": results,
            "errors": errors,
            "expires_in": expires_in,
            "total_requested": len(job_ids),
            "successful": len(results),
            "failed": len(errors)
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in bulk download: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_bp.route('/cleanup', methods=['POST'])
def cleanup_expired_files():
    """
    Cleanup old files from storage (admin endpoint).
    
    Expected JSON payload:
    {
        "days_old": 30,  # Files older than this will be deleted
        "dry_run": true  # Don't actually delete, just list files
    }
    
    Returns:
        JSON response with cleanup results
    """
    try:
        # This would be an admin-only endpoint in production
        # Add authentication/authorization here
        
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        days_old = data.get('days_old', 30)
        dry_run = data.get('dry_run', True)
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # This is a placeholder - in a real implementation, you'd:
        # 1. Query files older than X days
        # 2. Delete them from storage
        # 3. Update database records
        
        return jsonify({
            "message": "Cleanup functionality not implemented yet",
            "days_old": days_old,
            "dry_run": dry_run
        }), 501  # Not Implemented
        
    except Exception as e:
        logger.error(f"Unexpected error in cleanup: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Health check for the download blueprint
@download_bp.route('/health', methods=['GET'])
def download_health():
    """Health check endpoint for download service."""
    try:
        supabase = get_supabase_client()
        return jsonify({
            "status": "healthy",
            "service": "download",
            "supabase": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "download",
            "error": str(e)
        }), 500