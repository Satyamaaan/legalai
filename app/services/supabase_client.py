"""
Supabase client service module.

This module provides a clean abstraction over the Supabase Python SDK,
offering methods for database operations, storage management, and real-time updates.
"""

import os
import uuid
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from storage3 import StorageException
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SupabaseClientError(Exception):
    """Base exception for Supabase client errors."""
    pass

class SupabaseClient:
    """
    A service class that provides an abstraction over the Supabase Python SDK.
    
    This class handles database operations, storage management, and real-time updates
    for the Legal Document Translator application.
    """
    
    def __init__(self, url: str, key: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Supabase client.
        
        Args:
            url (str): The Supabase project URL
            key (str): The Supabase API key (service role key for admin operations)
            options (dict, optional): Additional client options
        
        Raises:
            SupabaseClientError: If initialization fails
        """
        try:
            client_options = ClientOptions(
                schema="public",
                headers={},
                **(options or {})
            )
            self.client = create_client(url, key, options=client_options)
            self.url = url
            
            # Test connection
            self._test_connection()
            
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise SupabaseClientError(f"Supabase client initialization failed: {str(e)}")
    
    def _test_connection(self) -> bool:
        """
        Test the Supabase connection by making a simple query.
        
        Returns:
            bool: True if connection is successful
            
        Raises:
            SupabaseClientError: If connection test fails
        """
        try:
            # Simple test query to verify connection
            self.client.table("translation_jobs").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
            raise SupabaseClientError(f"Supabase connection test failed: {str(e)}")
    
    # ---- Database Operations: Files ----
    
    def create_file_record(
        self, 
        original_name: str, 
        bucket: str, 
        storage_path: str, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new file record in the database.
        
        Args:
            original_name (str): Original filename
            bucket (str): Storage bucket name
            storage_path (str): Path in the storage bucket
            user_id (str, optional): User ID if authentication is enabled
            
        Returns:
            dict: The created file record
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            file_data = {
                "original_name": original_name,
                "bucket": bucket,
                "storage_path": storage_path,
            }
            
            if user_id:
                file_data["user_id"] = user_id
                
            result = self.client.table("files").insert(file_data).execute()
            
            if len(result.data) == 0:
                raise SupabaseClientError("Failed to create file record: No data returned")
                
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to create file record: {str(e)}")
            raise SupabaseClientError(f"Failed to create file record: {str(e)}")
    
    def get_file_by_id(self, file_id: str) -> Dict[str, Any]:
        """
        Get a file record by ID.
        
        Args:
            file_id (str): The file ID
            
        Returns:
            dict: The file record
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            result = self.client.table("files").select("*").eq("id", file_id).execute()
            
            if len(result.data) == 0:
                raise SupabaseClientError(f"File not found with ID: {file_id}")
                
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to get file with ID {file_id}: {str(e)}")
            raise SupabaseClientError(f"Failed to get file: {str(e)}")
    
    # ---- Database Operations: Translation Jobs ----
    
    def create_translation_job(
        self, 
        file_id: str, 
        src_lang: str = "gu", 
        tgt_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Create a new translation job in the database.
        
        Args:
            file_id (str): The file ID to translate
            src_lang (str): Source language code (default: "gu" for Gujarati)
            tgt_lang (str): Target language code (default: "en" for English)
            
        Returns:
            dict: The created job record
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            job_data = {
                "file_id": file_id,
                "status": "pending",
                "progress": 0,
                "src_lang": src_lang,
                "tgt_lang": tgt_lang
            }
            
            result = self.client.table("translation_jobs").insert(job_data).execute()
            
            if len(result.data) == 0:
                raise SupabaseClientError("Failed to create translation job: No data returned")
                
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to create translation job: {str(e)}")
            raise SupabaseClientError(f"Failed to create translation job: {str(e)}")
    
    def update_job_progress(
        self, 
        job_id: str, 
        progress: int, 
        status: Optional[str] = None, 
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the progress of a translation job.
        
        Args:
            job_id (str): The job ID
            progress (int): Progress percentage (0-100)
            status (str, optional): Job status (pending, processing, done, error)
            error_message (str, optional): Error message if status is 'error'
            
        Returns:
            dict: The updated job record
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            # Ensure progress is within bounds
            progress = max(0, min(100, progress))
            
            update_data = {
                "progress": progress,
                "updated_at": datetime.now().isoformat()
            }
            
            if status:
                update_data["status"] = status
                
            if error_message:
                update_data["error_message"] = error_message
                
            result = self.client.table("translation_jobs").update(update_data).eq("id", job_id).execute()
            
            if len(result.data) == 0:
                raise SupabaseClientError(f"Job not found with ID: {job_id}")
                
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to update job progress for job {job_id}: {str(e)}")
            raise SupabaseClientError(f"Failed to update job progress: {str(e)}")
    
    def get_job_by_id(self, job_id: str) -> Dict[str, Any]:
        """
        Get a translation job by ID.
        
        Args:
            job_id (str): The job ID
            
        Returns:
            dict: The job record
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            result = self.client.table("translation_jobs").select("*").eq("id", job_id).execute()
            
            if len(result.data) == 0:
                raise SupabaseClientError(f"Job not found with ID: {job_id}")
                
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to get job with ID {job_id}: {str(e)}")
            raise SupabaseClientError(f"Failed to get job: {str(e)}")
    
    def get_job_with_file(self, job_id: str) -> Dict[str, Any]:
        """
        Get a translation job with its associated file record.
        
        Args:
            job_id (str): The job ID
            
        Returns:
            dict: The job record with file data
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            result = self.client.table("translation_jobs") \
                .select("*, files(*)") \
                .eq("id", job_id) \
                .execute()
            
            if len(result.data) == 0:
                raise SupabaseClientError(f"Job not found with ID: {job_id}")
                
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to get job with file for job ID {job_id}: {str(e)}")
            raise SupabaseClientError(f"Failed to get job with file: {str(e)}")
    
    # ---- Storage Operations ----
    
    def get_upload_signed_url(
        self, 
        bucket: str, 
        path: str, 
        expires_in: int = 60
    ) -> Dict[str, str]:
        """
        Generate a signed URL for uploading a file.
        
        Args:
            bucket (str): Storage bucket name
            path (str): Path in the storage bucket
            expires_in (int): URL expiration time in seconds
            
        Returns:
            dict: Dictionary with signed URL and path
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            result = self.client.storage.from_(bucket).create_signed_upload_url(path, expires_in)
            
            return {
                "signed_url": result["signed_url"],
                "path": result["path"],
                "token": result.get("token", "")
            }
        except StorageException as e:
            logger.error(f"Failed to generate upload signed URL: {str(e)}")
            raise SupabaseClientError(f"Failed to generate upload signed URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating upload signed URL: {str(e)}")
            raise SupabaseClientError(f"Unexpected error generating upload signed URL: {str(e)}")
    
    def get_download_signed_url(
        self, 
        bucket: str, 
        path: str, 
        expires_in: int = 3600, 
        download_name: Optional[str] = None
    ) -> str:
        """
        Generate a signed URL for downloading a file.
        
        Args:
            bucket (str): Storage bucket name
            path (str): Path in the storage bucket
            expires_in (int): URL expiration time in seconds
            download_name (str, optional): Suggested download filename
            
        Returns:
            str: Signed download URL
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            options = {}
            if download_name:
                options["download"] = download_name
                
            result = self.client.storage.from_(bucket).create_signed_url(path, expires_in, options)
            
            return result["signedURL"]
        except StorageException as e:
            logger.error(f"Failed to generate download signed URL: {str(e)}")
            raise SupabaseClientError(f"Failed to generate download signed URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating download signed URL: {str(e)}")
            raise SupabaseClientError(f"Unexpected error generating download signed URL: {str(e)}")
    
    def upload_file(
        self, 
        bucket: str, 
        path: str, 
        file_path: str, 
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Supabase Storage.
        
        Args:
            bucket (str): Storage bucket name
            path (str): Path in the storage bucket
            file_path (str): Local file path
            content_type (str, optional): File content type
            
        Returns:
            dict: Upload result
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
                
            options = {}
            if content_type:
                options["content_type"] = content_type
                
            result = self.client.storage.from_(bucket).upload(path, file_data, options)
            
            return result
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise SupabaseClientError(f"File not found: {file_path}")
        except StorageException as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise SupabaseClientError(f"Failed to upload file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {str(e)}")
            raise SupabaseClientError(f"Unexpected error uploading file: {str(e)}")
    
    def download_file(
        self, 
        bucket: str, 
        path: str, 
        destination: str
    ) -> str:
        """
        Download a file from Supabase Storage.
        
        Args:
            bucket (str): Storage bucket name
            path (str): Path in the storage bucket
            destination (str): Local destination path
            
        Returns:
            str: Path to the downloaded file
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            # Ensure the destination directory exists
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            
            # Download the file
            result = self.client.storage.from_(bucket).download(path)
            
            # Save to destination
            with open(destination, "wb") as f:
                f.write(result)
                
            return destination
        except StorageException as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise SupabaseClientError(f"Failed to download file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error downloading file: {str(e)}")
            raise SupabaseClientError(f"Unexpected error downloading file: {str(e)}")
    
    # ---- Helper Methods ----
    
    def generate_storage_path(
        self, 
        prefix: str, 
        original_filename: str
    ) -> str:
        """
        Generate a unique storage path for a file.
        
        Args:
            prefix (str): Path prefix
            original_filename (str): Original filename
            
        Returns:
            str: Unique storage path
        """
        # Generate a unique ID
        unique_id = str(uuid.uuid4())
        
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create path: prefix/timestamp_uniqueid.ext
        return f"{prefix}/{timestamp}_{unique_id}{ext}"
    
    def create_translation_job_with_file(
        self, 
        original_name: str, 
        bucket: str, 
        storage_path: str, 
        src_lang: str = "gu", 
        tgt_lang: str = "en", 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create both a file record and a translation job in a single operation.
        
        Args:
            original_name (str): Original filename
            bucket (str): Storage bucket name
            storage_path (str): Path in the storage bucket
            src_lang (str): Source language code
            tgt_lang (str): Target language code
            user_id (str, optional): User ID if authentication is enabled
            
        Returns:
            dict: The created job record with file data
            
        Raises:
            SupabaseClientError: If the operation fails
        """
        try:
            # Create file record
            file_record = self.create_file_record(original_name, bucket, storage_path, user_id)
            
            # Create translation job
            job_record = self.create_translation_job(file_record["id"], src_lang, tgt_lang)
            
            # Return combined data
            job_record["file"] = file_record
            return job_record
        except Exception as e:
            logger.error(f"Failed to create translation job with file: {str(e)}")
            raise SupabaseClientError(f"Failed to create translation job with file: {str(e)}")
    
    def retry_operation(
        self, 
        operation_func, 
        max_retries: int = 3, 
        retry_delay: float = 1.0, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation_func: Function to retry
            max_retries (int): Maximum number of retries
            retry_delay (float): Initial delay between retries in seconds
            *args, **kwargs: Arguments to pass to the operation function
            
        Returns:
            Any: Result of the operation
            
        Raises:
            SupabaseClientError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # Calculate delay with exponential backoff
                delay = retry_delay * (2 ** attempt)
                
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay:.2f}s: {str(e)}"
                )
                
                time.sleep(delay)
        
        # If we get here, all retries failed
        logger.error(f"Operation failed after {max_retries} attempts: {str(last_error)}")
        raise SupabaseClientError(f"Operation failed after {max_retries} attempts: {str(last_error)}")
