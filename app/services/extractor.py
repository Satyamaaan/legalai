"""
PDF text extraction service.

This module provides functionality to extract text from PDF documents,
with support for both searchable PDFs and scanned documents requiring OCR.
It implements a fallback strategy to maximize extraction success.
"""

import os
import re
import logging
import tempfile
from typing import Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
import PyPDF2
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import numpy as np

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class PageText:
    """
    Represents extracted text from a single PDF page with metadata.
    """
    page_number: int
    text: str
    paragraphs: List[str]
    is_ocr: bool = False
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "page_number": self.page_number,
            "text": self.text,
            "paragraphs": self.paragraphs,
            "is_ocr": self.is_ocr,
            "confidence": self.confidence
        }

@dataclass
class ExtractionResult:
    """
    Represents the complete result of a PDF text extraction.
    """
    pages: List[PageText]
    success: bool
    method_used: str
    total_pages: int
    error: Optional[str] = None
    
    @property
    def full_text(self) -> str:
        """Get the full text of all pages concatenated."""
        return "\n\n".join(page.text for page in self.pages)
    
    @property
    def is_empty(self) -> bool:
        """Check if the extraction result is empty."""
        return len(self.pages) == 0 or all(not page.text.strip() for page in self.pages)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "pages": [page.to_dict() for page in self.pages],
            "success": self.success,
            "method_used": self.method_used,
            "total_pages": self.total_pages,
            "error": self.error,
            "is_empty": self.is_empty
        }

class ExtractionError(Exception):
    """Base exception for extraction errors."""
    pass

def extract_text_from_pdf(
    pdf_path: str,
    ocr_lang: str = "guj",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    tesseract_path: Optional[str] = None
) -> ExtractionResult:
    """
    Extract text from a PDF file using multiple methods with fallback.
    
    Args:
        pdf_path: Path to the PDF file
        ocr_lang: Tesseract language code (default: "guj" for Gujarati)
        progress_callback: Optional callback function to report progress
            Args: current_page, total_pages, status_message
        tesseract_path: Optional path to tesseract executable
    
    Returns:
        ExtractionResult object containing the extracted text and metadata
    
    Raises:
        ExtractionError: If all extraction methods fail
        FileNotFoundError: If the PDF file does not exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Configure tesseract path if provided
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    # Get total page count for progress reporting
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
    except Exception as e:
        logger.error(f"Error getting page count: {str(e)}")
        total_pages = 0  # Will be updated later if possible
    
    # Try extraction methods in order
    extraction_methods = [
        (_extract_with_pdfplumber, "pdfplumber"),
        (_extract_with_pypdf2, "PyPDF2"),
        (_extract_with_ocr, "tesseract-ocr")
    ]
    
    last_error = None
    for extract_func, method_name in extraction_methods:
        try:
            logger.info(f"Attempting extraction with {method_name}")
            
            if progress_callback:
                progress_callback(0, total_pages, f"Extracting text using {method_name}...")
            
            result = extract_func(
                pdf_path, 
                total_pages=total_pages,
                progress_callback=progress_callback,
                ocr_lang=ocr_lang
            )
            
            # If extraction was successful and produced text
            if result.success and not result.is_empty:
                logger.info(f"Extraction successful with {method_name}")
                return result
            
            # If extraction was successful but produced no text, try next method
            if result.success and result.is_empty:
                logger.warning(f"Extraction with {method_name} produced no text, trying next method")
                last_error = ExtractionError(f"No text extracted with {method_name}")
            
        except Exception as e:
            logger.warning(f"Extraction with {method_name} failed: {str(e)}")
            last_error = e
    
    # If we get here, all methods failed
    error_msg = str(last_error) if last_error else "All extraction methods failed"
    logger.error(f"PDF text extraction failed: {error_msg}")
    
    return ExtractionResult(
        pages=[],
        success=False,
        method_used="none",
        total_pages=total_pages,
        error=error_msg
    )

def _extract_with_pdfplumber(
    pdf_path: str,
    total_pages: int,
    progress_callback: Optional[Callable] = None,
    **kwargs
) -> ExtractionResult:
    """
    Extract text from a PDF using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        total_pages: Total number of pages in the PDF
        progress_callback: Optional callback function to report progress
        **kwargs: Additional arguments (not used by this method)
    
    Returns:
        ExtractionResult object
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Update total_pages if it was not determined correctly
            if total_pages == 0:
                total_pages = len(pdf.pages)
            
            pages = []
            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total_pages, f"Extracting page {i + 1}/{total_pages} with pdfplumber...")
                
                # Extract text
                text = page.extract_text() or ""
                
                # Split into paragraphs (by double newlines or significant spacing)
                paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
                
                # If no paragraphs were found but there's text, treat the whole text as one paragraph
                if not paragraphs and text.strip():
                    paragraphs = [text.strip()]
                
                pages.append(PageText(
                    page_number=i + 1,
                    text=text,
                    paragraphs=paragraphs,
                    is_ocr=False,
                    confidence=1.0  # High confidence for direct extraction
                ))
            
            return ExtractionResult(
                pages=pages,
                success=True,
                method_used="pdfplumber",
                total_pages=total_pages
            )
    
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {str(e)}")
        raise ExtractionError(f"pdfplumber extraction failed: {str(e)}")

def _extract_with_pypdf2(
    pdf_path: str,
    total_pages: int,
    progress_callback: Optional[Callable] = None,
    **kwargs
) -> ExtractionResult:
    """
    Extract text from a PDF using PyPDF2.
    
    Args:
        pdf_path: Path to the PDF file
        total_pages: Total number of pages in the PDF
        progress_callback: Optional callback function to report progress
        **kwargs: Additional arguments (not used by this method)
    
    Returns:
        ExtractionResult object
    """
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Update total_pages if it was not determined correctly
            if total_pages == 0:
                total_pages = len(pdf_reader.pages)
            
            pages = []
            for i in range(total_pages):
                if progress_callback:
                    progress_callback(i + 1, total_pages, f"Extracting page {i + 1}/{total_pages} with PyPDF2...")
                
                # Extract text
                page = pdf_reader.pages[i]
                text = page.extract_text() or ""
                
                # Split into paragraphs (by double newlines or significant spacing)
                paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
                
                # If no paragraphs were found but there's text, treat the whole text as one paragraph
                if not paragraphs and text.strip():
                    paragraphs = [text.strip()]
                
                pages.append(PageText(
                    page_number=i + 1,
                    text=text,
                    paragraphs=paragraphs,
                    is_ocr=False,
                    confidence=0.9  # Slightly lower confidence than pdfplumber
                ))
            
            return ExtractionResult(
                pages=pages,
                success=True,
                method_used="PyPDF2",
                total_pages=total_pages
            )
    
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed: {str(e)}")
        raise ExtractionError(f"PyPDF2 extraction failed: {str(e)}")

def _extract_with_ocr(
    pdf_path: str,
    total_pages: int,
    progress_callback: Optional[Callable] = None,
    ocr_lang: str = "guj",
    dpi: int = 300,
    **kwargs
) -> ExtractionResult:
    """
    Extract text from a PDF using OCR (Tesseract).
    
    Args:
        pdf_path: Path to the PDF file
        total_pages: Total number of pages in the PDF
        progress_callback: Optional callback function to report progress
        ocr_lang: Tesseract language code (default: "guj" for Gujarati)
        dpi: DPI for PDF to image conversion (higher is better quality but slower)
        **kwargs: Additional arguments
    
    Returns:
        ExtractionResult object
    """
    try:
        # Convert PDF to images
        if progress_callback:
            progress_callback(0, total_pages, "Converting PDF to images for OCR...")
        
        images = convert_from_path(pdf_path, dpi=dpi)
        
        # Update total_pages if it was not determined correctly
        if total_pages == 0:
            total_pages = len(images)
        
        pages = []
        for i, image in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, total_pages, f"OCR processing page {i + 1}/{total_pages}...")
            
            # Process image with Tesseract
            ocr_config = f'--oem 3 --psm 6 -l {ocr_lang}'
            
            # Get OCR data including confidence
            ocr_data = pytesseract.image_to_data(image, config=ocr_config, output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate confidence
            text_parts = []
            confidence_values = []
            
            for j in range(len(ocr_data['text'])):
                if ocr_data['text'][j].strip():
                    text_parts.append(ocr_data['text'][j])
                    confidence_values.append(float(ocr_data['conf'][j]))
            
            # Join text parts
            text = ' '.join(text_parts)
            
            # Calculate average confidence (excluding -1 values)
            valid_confidences = [c for c in confidence_values if c >= 0]
            avg_confidence = sum(valid_confidences) / len(valid_confidences) / 100.0 if valid_confidences else 0
            
            # Split into paragraphs (using whitespace patterns)
            # For OCR, we use a more aggressive paragraph detection
            paragraphs = []
            current_para = []
            
            for line in text.split('\n'):
                if not line.strip():
                    if current_para:
                        paragraphs.append(' '.join(current_para))
                        current_para = []
                else:
                    current_para.append(line.strip())
            
            # Add the last paragraph if it exists
            if current_para:
                paragraphs.append(' '.join(current_para))
            
            # If no paragraphs were found but there's text, treat the whole text as one paragraph
            if not paragraphs and text.strip():
                paragraphs = [text.strip()]
            
            pages.append(PageText(
                page_number=i + 1,
                text=text,
                paragraphs=paragraphs,
                is_ocr=True,
                confidence=avg_confidence
            ))
        
        return ExtractionResult(
            pages=pages,
            success=True,
            method_used="tesseract-ocr",
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        raise ExtractionError(f"OCR extraction failed: {str(e)}")

def is_scanned_pdf(pdf_path: str, threshold: float = 0.1) -> bool:
    """
    Determine if a PDF is likely a scanned document.
    
    Args:
        pdf_path: Path to the PDF file
        threshold: Minimum text content ratio to consider a page as digital
    
    Returns:
        bool: True if the PDF appears to be scanned, False otherwise
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check a sample of pages (first, middle, last)
            total_pages = len(pdf.pages)
            
            if total_pages == 0:
                return False
            
            pages_to_check = [0]  # Always check first page
            
            if total_pages > 1:
                pages_to_check.append(total_pages - 1)  # Last page
            
            if total_pages > 2:
                pages_to_check.append(total_pages // 2)  # Middle page
            
            for page_idx in pages_to_check:
                page = pdf.pages[page_idx]
                
                # Get page dimensions
                width, height = page.width, page.height
                page_area = width * height
                
                # Extract text and calculate its length
                text = page.extract_text() or ""
                text_length = len(text.strip())
                
                # Calculate text density (characters per unit area)
                text_density = text_length / page_area if page_area > 0 else 0
                
                # If any page has sufficient text density, consider it not scanned
                if text_density > threshold:
                    return False
            
            # If we get here, all checked pages had low text density
            return True
    
    except Exception as e:
        logger.warning(f"Error checking if PDF is scanned: {str(e)}")
        # If we can't determine, assume it might be scanned
        return True

def extract_text_with_best_method(
    pdf_path: str,
    ocr_lang: str = "guj",
    force_ocr: bool = False,
    progress_callback: Optional[Callable] = None,
    tesseract_path: Optional[str] = None
) -> ExtractionResult:
    """
    Extract text using the most appropriate method based on PDF characteristics.
    
    Args:
        pdf_path: Path to the PDF file
        ocr_lang: Tesseract language code (default: "guj" for Gujarati)
        force_ocr: Whether to force OCR even for digital PDFs
        progress_callback: Optional callback function to report progress
        tesseract_path: Optional path to tesseract executable
    
    Returns:
        ExtractionResult object
    """
    # Configure tesseract path if provided
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    try:
        # Determine if the PDF is scanned
        if force_ocr:
            is_scanned = True
        else:
            if progress_callback:
                progress_callback(0, 1, "Analyzing PDF type...")
            
            is_scanned = is_scanned_pdf(pdf_path)
        
        # Choose extraction method based on PDF type
        if is_scanned:
            logger.info("PDF appears to be scanned or has low text content, using OCR")
            if progress_callback:
                progress_callback(0, 1, "PDF appears to be scanned, using OCR...")
            
            return _extract_with_ocr(
                pdf_path,
                total_pages=0,  # Will be determined during extraction
                progress_callback=progress_callback,
                ocr_lang=ocr_lang
            )
        else:
            logger.info("PDF appears to be digital, using text extraction")
            if progress_callback:
                progress_callback(0, 1, "PDF appears to be digital, extracting text...")
            
            return extract_text_from_pdf(
                pdf_path,
                ocr_lang=ocr_lang,
                progress_callback=progress_callback,
                tesseract_path=tesseract_path
            )
    
    except Exception as e:
        logger.error(f"Error in extract_text_with_best_method: {str(e)}")
        raise ExtractionError(f"Text extraction failed: {str(e)}")

def extract_text_from_bytes(
    pdf_bytes: bytes,
    ocr_lang: str = "guj",
    progress_callback: Optional[Callable] = None,
    tesseract_path: Optional[str] = None
) -> ExtractionResult:
    """
    Extract text from PDF bytes.
    
    Args:
        pdf_bytes: PDF file content as bytes
        ocr_lang: Tesseract language code (default: "guj" for Gujarati)
        progress_callback: Optional callback function to report progress
        tesseract_path: Optional path to tesseract executable
    
    Returns:
        ExtractionResult object
    """
    # Save bytes to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write(pdf_bytes)
    
    try:
        # Extract text from the temporary file
        result = extract_text_with_best_method(
            tmp_path,
            ocr_lang=ocr_lang,
            progress_callback=progress_callback,
            tesseract_path=tesseract_path
        )
        return result
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {tmp_path}: {str(e)}")
