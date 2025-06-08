"""
Routes package for the Legal Document Translator application.

This package contains Flask blueprints that define the application's routes:
- upload: Handles PDF file uploads and generates presigned URLs
- translate: Manages the translation process and progress tracking
- download: Provides access to translated documents

Each blueprint is registered with the Flask application in the application factory.
"""
