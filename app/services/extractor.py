"""
PDF text extraction service for the Legal Document Translator.

This service handles PDF text extraction using multiple strategies:
1. pdfplumber for selectable text PDFs
2. OCR with Tesseract for scanned/image PDFs
3. Fallback to PyPDF2 for basic extraction

Returns structured HTML/text with preserved formatting.
"""

import os
import io
import logging
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import pdfplumber
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)

class ExtractionError(Exception):
    """Custom exception for PDF extraction errors."""
    pass

class PDFExtractor:
    """
    PDF text extraction service with multiple extraction strategies.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the PDF extractor.
        
        Args:
            tesseract_path (str, optional): Path to Tesseract executable
        """
        self.tesseract_path = tesseract_path
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Configure Tesseract for Gujarati
        self.tesseract_config = '--oem 3 --psm 6 -l guj+eng'
        
        # Minimum text threshold to determine if PDF has selectable text
        self.min_text_threshold = 100
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF file using the best available method.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Extraction result with text, metadata, and structure
            
        Raises:
            ExtractionError: If extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractionError(f"File not found: {file_path}")
        
        if not file_path.lower().endswith('.pdf'):
            raise ExtractionError(f"File must be a PDF: {file_path}")
        
        try:
            logger.info(f"Starting extraction for: {file_path}")
            
            # Try pdfplumber first (best for selectable text)
            result = self._extract_with_pdfplumber(file_path)
            
            # If we didn't get enough text, try OCR
            if len(result['raw_text']) < self.min_text_threshold:
                logger.info("Insufficient text found, attempting OCR extraction")
                ocr_result = self._extract_with_ocr(file_path)
                
                # Use OCR result if it has more text
                if len(ocr_result['raw_text']) > len(result['raw_text']):
                    result = ocr_result
                    result['extraction_method'] = 'ocr'
                else:
                    result['extraction_method'] = 'pdfplumber_sparse'
            else:
                result['extraction_method'] = 'pdfplumber'
            
            # Generate structured HTML
            result['structured_html'] = self._generate_structured_html(result)
            
            logger.info(f"Extraction completed. Method: {result['extraction_method']}, "
                       f"Text length: {len(result['raw_text'])}, "
                       f"Pages: {result['metadata']['page_count']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed for {file_path}: {str(e)}")
            raise ExtractionError(f"PDF extraction failed: {str(e)}")
    
    def _extract_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text using pdfplumber (best for selectable text).
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Extraction result
        """
        pages_data = []
        raw_text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text with basic structure
                    page_text = page.extract_text() or ""
                    
                    # Extract tables if any
                    tables = page.extract_tables()
                    
                    # Get page dimensions
                    page_info = {
                        'page_number': page_num,
                        'text': page_text,
                        'tables': tables,
                        'bbox': page.bbox,
                        'width': page.width,
                        'height': page.height
                    }
                    
                    pages_data.append(page_info)
                    raw_text += page_text + "\n\n"
                
                # Extract metadata
                metadata = {
                    'page_count': len(pdf.pages),
                    'metadata': pdf.metadata or {},
                    'file_size': os.path.getsize(file_path)
                }
                
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            raise ExtractionError(f"pdfplumber extraction failed: {str(e)}")
        
        return {
            'raw_text': raw_text.strip(),
            'pages': pages_data,
            'metadata': metadata,
            'extraction_method': 'pdfplumber'
        }
    
    def _extract_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text using OCR (for scanned PDFs).
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Extraction result
        """
        pages_data = []
        raw_text = ""
        
        try:
            # Convert PDF to images
            logger.info("Converting PDF to images for OCR")
            images = convert_from_path(file_path, dpi=200)
            
            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing OCR for page {page_num}")
                
                # Perform OCR on the image
                page_text = pytesseract.image_to_string(
                    image, 
                    config=self.tesseract_config
                )
                
                # Get image dimensions
                page_info = {
                    'page_number': page_num,
                    'text': page_text,
                    'tables': [],  # OCR doesn't extract tables
                    'bbox': None,
                    'width': image.width,
                    'height': image.height
                }
                
                pages_data.append(page_info)
                raw_text += page_text + "\n\n"
            
            # Basic metadata
            metadata = {
                'page_count': len(images),
                'metadata': {},
                'file_size': os.path.getsize(file_path)
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise ExtractionError(f"OCR extraction failed: {str(e)}")
        
        return {
            'raw_text': raw_text.strip(),
            'pages': pages_data,
            'metadata': metadata,
            'extraction_method': 'ocr'
        }
    
    def _extract_with_pypdf2_fallback(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback extraction using PyPDF2 (basic text extraction).
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Extraction result
        """
        pages_data = []
        raw_text = ""
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    
                    page_info = {
                        'page_number': page_num,
                        'text': page_text,
                        'tables': [],
                        'bbox': None,
                        'width': None,
                        'height': None
                    }
                    
                    pages_data.append(page_info)
                    raw_text += page_text + "\n\n"
                
                # Basic metadata
                metadata = {
                    'page_count': len(pdf_reader.pages),
                    'metadata': pdf_reader.metadata or {},
                    'file_size': os.path.getsize(file_path)
                }
                
        except Exception as e:
            logger.error(f"PyPDF2 fallback extraction failed: {str(e)}")
            raise ExtractionError(f"PyPDF2 fallback extraction failed: {str(e)}")
        
        return {
            'raw_text': raw_text.strip(),
            'pages': pages_data,
            'metadata': metadata,
            'extraction_method': 'pypdf2'
        }
    
    def _generate_structured_html(self, extraction_result: Dict[str, Any]) -> str:
        """
        Generate structured HTML from extraction result.
        
        Args:
            extraction_result (dict): Result from extraction
            
        Returns:
            str: Structured HTML
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="gu">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Extracted Legal Document</title>',
            '    <style>',
            '        body { font-family: "Noto Sans Gujarati", Arial, sans-serif; line-height: 1.6; margin: 40px; }',
            '        .page { margin-bottom: 40px; page-break-after: always; }',
            '        .page-header { font-weight: bold; color: #666; margin-bottom: 20px; }',
            '        .paragraph { margin-bottom: 15px; text-align: justify; }',
            '        .table { border-collapse: collapse; width: 100%; margin: 20px 0; }',
            '        .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }',
            '        .table th { background-color: #f2f2f2; }',
            '    </style>',
            '</head>',
            '<body>'
        ]
        
        # Add content for each page
        for page in extraction_result['pages']:
            html_parts.append(f'<div class="page">')
            html_parts.append(f'<div class="page-header">પૃષ્ઠ {page["page_number"]}</div>')
            
            # Process text into paragraphs
            page_text = page['text'].strip()
            if page_text:
                paragraphs = page_text.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        # Simple cleanup
                        para = para.replace('\n', ' ').replace('  ', ' ')
                        html_parts.append(f'<div class="paragraph">{self._escape_html(para)}</div>')
            
            # Add tables if any
            if page.get('tables'):
                for table in page['tables']:
                    if table and len(table) > 0:
                        html_parts.append('<table class="table">')
                        for row_idx, row in enumerate(table):
                            if row and any(cell for cell in row if cell):  # Skip empty rows
                                tag = 'th' if row_idx == 0 else 'td'
                                html_parts.append('<tr>')
                                for cell in row:
                                    cell_content = self._escape_html(str(cell or ''))
                                    html_parts.append(f'<{tag}>{cell_content}</{tag}>')
                                html_parts.append('</tr>')
                        html_parts.append('</table>')
            
            html_parts.append('</div>')
        
        html_parts.extend(['</body>', '</html>'])
        
        return '\n'.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def get_text_chunks(self, extraction_result: Dict[str, Any], max_chunk_size: int = 1000) -> List[str]:
        """
        Split extracted text into chunks suitable for translation.
        
        Args:
            extraction_result (dict): Result from extraction
            max_chunk_size (int): Maximum characters per chunk
            
        Returns:
            list: List of text chunks
        """
        raw_text = extraction_result['raw_text']
        if not raw_text:
            return []
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences/paragraphs
        sentences = raw_text.replace('\n\n', '\n').split('\n')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed the limit
            if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                # Add current chunk if it has content
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # Start new chunk
                if len(sentence) > max_chunk_size:
                    # Split very long sentences
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 > max_chunk_size:
                            if temp_chunk.strip():
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            temp_chunk += " " + word if temp_chunk else word
                    current_chunk = temp_chunk
                else:
                    current_chunk = sentence
            else:
                current_chunk += "\n" + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

def create_extractor(tesseract_path: Optional[str] = None) -> PDFExtractor:
    """
    Factory function to create a PDF extractor instance.
    
    Args:
        tesseract_path (str, optional): Path to Tesseract executable
        
    Returns:
        PDFExtractor: Configured extractor instance
    """
    return PDFExtractor(tesseract_path)