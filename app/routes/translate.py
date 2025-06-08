"""
Translation job orchestration route for the Legal Document Translator.

This module handles the complete translation workflow:
1. Download PDF from Supabase Storage
2. Extract text using the extractor service
3. Translate using the translator service  
4. Build output PDF using the PDF builder
5. Upload result and update job status
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, current_app

from app.services.supabase_client import SupabaseClient, SupabaseClientError
from app.services.extractor import create_extractor, ExtractionError
from app.services.translator import create_translator, TranslationError
from app.services.pdf_builder import create_pdf_builder, PDFBuildError

logger = logging.getLogger(__name__)

# Create blueprint
translate_bp = Blueprint('translate', __name__, url_prefix='/api/translate')

def get_supabase_client() -> SupabaseClient:
    """Get Supabase client from Flask app context."""
    if not hasattr(current_app, 'supabase') or current_app.supabase is None:
        raise SupabaseClientError("Supabase client not initialized")
    
    return SupabaseClient(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_SERVICE_KEY']
    )

@translate_bp.route('/start/<job_id>', methods=['POST'])
def start_translation(job_id: str):
    """
    Start the translation process for a job.
    
    Args:
        job_id: UUID of the translation job
        
    Returns:
        JSON response with job status
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get job with file data
        job_data = supabase.get_job_with_file(job_id)
        
        if job_data['status'] not in ['pending', 'processing']:
            return jsonify({
                "error": f"Job is in {job_data['status']} status and cannot be started"
            }), 400
        
        # Update status to processing
        supabase.update_job_progress(job_id, 10, "processing")
        
        # Start the translation workflow
        result = _process_translation_job(job_data, supabase)
        
        return jsonify(result), 200
        
    except SupabaseClientError as e:
        logger.error(f"Supabase error starting translation: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error starting translation: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def _process_translation_job(job_data: Dict[str, Any], supabase: SupabaseClient) -> Dict[str, Any]:
    """
    Process the complete translation workflow.
    
    Args:
        job_data: Job data from database
        supabase: Supabase client instance
        
    Returns:
        Result dictionary
    """
    job_id = job_data['id']
    file_data = job_data['files']
    
    temp_input_path = None
    temp_output_path = None
    
    try:
        # Step 1: Download PDF from Supabase Storage
        logger.info(f"Downloading PDF for job {job_id}")
        supabase.update_job_progress(job_id, 15, "extracting")
        
        temp_input_path = _download_pdf_file(supabase, file_data)
        
        # Step 2: Extract text from PDF
        logger.info(f"Extracting text for job {job_id}")
        supabase.update_job_progress(job_id, 25, "extracting")
        
        extraction_result = _extract_pdf_text(temp_input_path)
        
        # Step 3: Translate extracted text
        logger.info(f"Translating text for job {job_id}")
        supabase.update_job_progress(job_id, 40, "translating")
        
        translation_result = _translate_text(
            extraction_result, 
            job_data['src_lang'], 
            job_data['tgt_lang'],
            lambda progress, current, total: supabase.update_job_progress(
                job_id, 
                40 + int((progress / 100) * 30),  # 40-70% for translation
                "translating"
            )
        )
        
        # Step 4: Build output PDF
        logger.info(f"Building PDF for job {job_id}")
        supabase.update_job_progress(job_id, 75, "building")
        
        temp_output_path = _build_output_pdf(translation_result, file_data['original_name'])
        
        # Step 5: Upload result to Supabase Storage
        logger.info(f"Uploading result for job {job_id}")
        supabase.update_job_progress(job_id, 85, "building")
        
        output_file_id = _upload_result_pdf(supabase, temp_output_path, file_data['original_name'])
        
        # Step 6: Update job as completed
        logger.info(f"Completing job {job_id}")
        updated_job = supabase.update_job_progress(job_id, 100, "done")
        
        # Link output file to job
        supabase.client.table("translation_jobs").update({
            "output_file_id": output_file_id
        }).eq("id", job_id).execute()
        
        return {
            "job_id": job_id,
            "status": "done",
            "progress": 100,
            "output_file_id": output_file_id
        }
        
    except Exception as e:
        logger.error(f"Translation workflow failed for job {job_id}: {str(e)}")
        
        # Update job status to error
        try:
            supabase.update_job_progress(
                job_id, 
                progress=0,
                status="error", 
                error_message=str(e)
            )
        except:
            pass  # Don't fail if we can't update the error status
        
        raise
        
    finally:
        # Clean up temporary files
        for temp_path in [temp_input_path, temp_output_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

def _download_pdf_file(supabase: SupabaseClient, file_data: Dict[str, Any]) -> str:
    """Download PDF file from Supabase Storage to temporary location."""
    # Create temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='input_')
    os.close(temp_fd)  # Close the file descriptor, we just need the path
    
    try:
        # Download file from Supabase Storage
        supabase.download_file(
            bucket=file_data['bucket'],
            path=file_data['storage_path'],
            destination=temp_path
        )
        
        return temp_path
        
    except Exception as e:
        # Clean up on failure
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise Exception(f"Failed to download PDF: {str(e)}")

def _extract_pdf_text(file_path: str) -> Dict[str, Any]:
    """Extract text from PDF using the extractor service."""
    try:
        extractor = create_extractor(current_app.config.get('TESSERACT_PATH'))
        result = extractor.extract_from_file(file_path)
        
        if not result or not result.get('raw_text'):
            raise ExtractionError("No text could be extracted from the PDF")
        
        return result
        
    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")

def _translate_text(extraction_result: Dict[str, Any], src_lang: str, tgt_lang: str, progress_callback) -> Dict[str, Any]:
    """Translate extracted text using the translator service."""
    try:
        translator = create_translator(
            api_key=current_app.config['SARVAM_API_KEY'],
            api_url=current_app.config['SARVAM_API_URL'],
            max_chars=current_app.config['SARVAM_MAX_CHARS']
        )
        
        # Get text chunks for translation
        extractor = create_extractor()
        chunks = extractor.get_text_chunks(extraction_result, current_app.config['SARVAM_MAX_CHARS'])
        
        if not chunks:
            raise TranslationError("No text chunks available for translation")
        
        # Translate chunks with progress tracking
        translated_chunks = translator.translate_chunks(
            chunks, 
            src_lang, 
            tgt_lang,
            progress_callback
        )
        
        # Combine translated chunks
        translated_text = "\n\n".join([result.translated_text for result in translated_chunks])
        
        return {
            'original_text': extraction_result['raw_text'],
            'translated_text': translated_text,
            'src_lang': src_lang,
            'tgt_lang': tgt_lang,
            'chunks': len(translated_chunks),
            'extraction_method': extraction_result.get('extraction_method', 'unknown')
        }
        
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")

def _build_output_pdf(translation_result: Dict[str, Any], original_filename: str) -> str:
    """Build output PDF using the PDF builder service."""
    try:
        builder = create_pdf_builder()
        
        # Create temporary file for output
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='output_')
        os.close(temp_fd)
        
        # Generate PDF
        builder.build_pdf_from_text(
            text=translation_result['translated_text'],
            output_path=temp_path,
            title=f"Translated - {original_filename}",
            source_lang=translation_result['src_lang'],
            target_lang=translation_result['tgt_lang']
        )
        
        return temp_path
        
    except Exception as e:
        raise Exception(f"PDF building failed: {str(e)}")

def _upload_result_pdf(supabase: SupabaseClient, file_path: str, original_filename: str) -> str:
    """Upload result PDF to Supabase Storage and create file record."""
    try:
        # Generate output filename
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}_translated.pdf"
        
        # Generate storage path
        storage_path = supabase.generate_storage_path("outputs", output_filename)
        
        # Upload file
        supabase.upload_file(
            bucket=current_app.config['OUTPUTS_BUCKET'],
            path=storage_path,
            file_path=file_path,
            content_type='application/pdf'
        )
        
        # Create file record
        file_record = supabase.create_file_record(
            original_name=output_filename,
            bucket=current_app.config['OUTPUTS_BUCKET'],
            storage_path=storage_path
        )
        
        return file_record['id']
        
    except Exception as e:
        raise Exception(f"Failed to upload result PDF: {str(e)}")

# Health check for the translate blueprint
@translate_bp.route('/health', methods=['GET'])
def translate_health():
    """Health check endpoint for translate service."""
    try:
        # Check dependencies
        checks = {
            "supabase": "connected" if get_supabase_client() else "disconnected",
            "sarvam_api_key": "configured" if current_app.config.get('SARVAM_API_KEY') else "missing",
            "tesseract_path": "configured" if current_app.config.get('TESSERACT_PATH') else "default"
        }
        
        return jsonify({
            "status": "healthy",
            "service": "translate",
            "checks": checks
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "translate",
            "error": str(e)
        }), 500