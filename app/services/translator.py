"""
Sarvam AI Translation Service.

This module provides functionality to translate text using the Sarvam AI API,
with special handling for HTML structure preservation, chunking for API limits,
and robust error handling.
"""

import os
import re
import time
import json
import logging
import html
from typing import Dict, List, Optional, Union, Tuple, Callable, Any
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup

from app.services.extractor import PageText, ExtractionResult

# Configure logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_CHARS = 1000  # Sarvam API character limit per request
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_RATE_LIMIT_DELAY = 0.5  # seconds between API calls
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

class TranslationError(Exception):
    """Base exception for translation errors."""
    pass

@dataclass
class TranslatedPage:
    """
    Represents a translated page with metadata.
    """
    page_number: int
    original_text: str
    translated_text: str
    html_translated: str
    source_language: str
    target_language: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "page_number": self.page_number,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "html_translated": self.html_translated,
            "source_language": self.source_language,
            "target_language": self.target_language
        }

@dataclass
class TranslationResult:
    """
    Represents the complete result of a document translation.
    """
    pages: List[TranslatedPage]
    success: bool
    source_language: str
    target_language: str
    total_pages: int
    error: Optional[str] = None
    
    @property
    def full_translated_text(self) -> str:
        """Get the full translated text of all pages concatenated."""
        return "\n\n".join(page.translated_text for page in self.pages)
    
    @property
    def full_html_translated(self) -> str:
        """Get the full HTML translated content of all pages."""
        return "\n\n".join(page.html_translated for page in self.pages)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "pages": [page.to_dict() for page in self.pages],
            "success": self.success,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "total_pages": self.total_pages,
            "error": self.error
        }

class SarvamTranslator:
    """
    Client for the Sarvam AI Translation API with robust error handling,
    rate limiting, and HTML structure preservation.
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.sarvam.ai/v1",
        max_chars: int = DEFAULT_MAX_CHARS,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    ):
        """
        Initialize the Sarvam Translator.
        
        Args:
            api_key: Sarvam AI API key
            api_url: Base URL for the Sarvam API
            max_chars: Maximum characters per translation request
            retry_count: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (seconds)
            rate_limit_delay: Delay between API calls to avoid rate limiting
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.max_chars = max_chars
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # Validate API key
        if not api_key:
            raise TranslationError("Sarvam API key is required")
    
    def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """
        Translate a single text string using the Sarvam API.
        
        Args:
            text: Text to translate
            source_language: Source language code (e.g., "gu" for Gujarati)
            target_language: Target language code (e.g., "en" for English)
            
        Returns:
            Translated text
            
        Raises:
            TranslationError: If translation fails after retries
        """
        if not text.strip():
            return ""
        
        # Respect rate limiting
        self._respect_rate_limit()
        
        endpoint = f"{self.api_url}/translate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "text": text,
            "source_language": source_language,
            "target_language": target_language
        }
        
        # Track request time for rate limiting
        self.last_request_time = time.time()
        
        # Implement retry logic
        for attempt in range(self.retry_count):
            try:
                response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("translated_text", "")
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get("Retry-After", self.retry_delay * (2 ** attempt)))
                    logger.warning(f"Rate limited by Sarvam API. Waiting {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    error_msg = f"Sarvam API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    # Wait before retry with exponential backoff
                    if attempt < self.retry_count - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.info(f"Retrying in {wait_time:.2f} seconds (attempt {attempt + 1}/{self.retry_count})")
                        time.sleep(wait_time)
            
            except requests.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                
                # Wait before retry with exponential backoff
                if attempt < self.retry_count - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time:.2f} seconds (attempt {attempt + 1}/{self.retry_count})")
                    time.sleep(wait_time)
        
        # If we get here, all retries failed
        raise TranslationError(f"Translation failed after {self.retry_count} attempts")
    
    def _respect_rate_limit(self):
        """
        Ensure we don't exceed rate limits by adding delays between requests.
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
    
    def translate_html(
        self,
        html_content: str,
        source_language: str,
        target_language: str
    ) -> str:
        """
        Translate HTML content while preserving tags and structure.
        
        Args:
            html_content: HTML content to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translated HTML content
        """
        # Split HTML into chunks that respect tag boundaries
        chunks = self._chunk_html(html_content, self.max_chars)
        
        # Translate each chunk
        translated_chunks = []
        for chunk in chunks:
            translated_chunk = self.translate_text(chunk, source_language, target_language)
            translated_chunks.append(translated_chunk)
        
        # Reassemble chunks
        return "".join(translated_chunks)
    
    def _chunk_html(self, html_content: str, max_chars: int) -> List[str]:
        """
        Split HTML content into chunks respecting tag boundaries.
        
        Args:
            html_content: HTML content to chunk
            max_chars: Maximum characters per chunk
            
        Returns:
            List of HTML chunks
        """
        if len(html_content) <= max_chars:
            return [html_content]
        
        soup = BeautifulSoup(html_content, 'html.parser')
        chunks = []
        current_chunk = ""
        
        # Process each top-level element
        for element in soup.body.children if soup.body else soup.children:
            element_str = str(element)
            
            # If adding this element would exceed max_chars, start a new chunk
            if len(current_chunk) + len(element_str) > max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If the element itself is larger than max_chars, we need to split it
            if len(element_str) > max_chars:
                # For large text nodes, split by sentences or phrases
                if element.name is None:  # Text node
                    sentences = re.split(r'([.!?।][\s\n])', str(element))
                    for i in range(0, len(sentences), 2):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i + 1]  # Add the delimiter back
                        
                        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""
                        
                        current_chunk += sentence
                        
                        if len(current_chunk) > max_chars:
                            chunks.append(current_chunk)
                            current_chunk = ""
                else:
                    # For large elements, recursively chunk their contents
                    sub_chunks = self._chunk_html(element_str, max_chars)
                    
                    # Add first sub-chunk to current chunk if it fits
                    if sub_chunks and len(current_chunk) + len(sub_chunks[0]) <= max_chars:
                        current_chunk += sub_chunks[0]
                        sub_chunks = sub_chunks[1:]
                    
                    # Finalize current chunk if it's not empty
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = ""
                    
                    # Add remaining sub-chunks
                    chunks.extend(sub_chunks)
            else:
                current_chunk += element_str
                
                # If current chunk is getting too large, finalize it
                if len(current_chunk) > max_chars * 0.9:
                    chunks.append(current_chunk)
                    current_chunk = ""
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def translate_extraction_result(
        self,
        extraction_result: ExtractionResult,
        source_language: str,
        target_language: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> TranslationResult:
        """
        Translate an entire extraction result while preserving structure.
        
        Args:
            extraction_result: ExtractionResult from the extractor service
            source_language: Source language code
            target_language: Target language code
            progress_callback: Optional callback for progress updates
            
        Returns:
            TranslationResult object
        """
        if not extraction_result.success:
            return TranslationResult(
                pages=[],
                success=False,
                source_language=source_language,
                target_language=target_language,
                total_pages=extraction_result.total_pages,
                error=f"Extraction failed: {extraction_result.error}"
            )
        
        try:
            translated_pages = []
            total_pages = len(extraction_result.pages)
            
            for i, page in enumerate(extraction_result.pages):
                if progress_callback:
                    progress_callback(
                        i + 1,
                        total_pages,
                        f"Translating page {i + 1}/{total_pages}..."
                    )
                
                # Convert page to HTML
                html_content = self._page_to_html(page)
                
                # Translate HTML content
                html_translated = self.translate_html(
                    html_content,
                    source_language,
                    target_language
                )
                
                # Extract plain text from translated HTML
                translated_text = self._extract_text_from_html(html_translated)
                
                translated_pages.append(TranslatedPage(
                    page_number=page.page_number,
                    original_text=page.text,
                    translated_text=translated_text,
                    html_translated=html_translated,
                    source_language=source_language,
                    target_language=target_language
                ))
            
            return TranslationResult(
                pages=translated_pages,
                success=True,
                source_language=source_language,
                target_language=target_language,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.exception(f"Translation failed: {str(e)}")
            return TranslationResult(
                pages=[],
                success=False,
                source_language=source_language,
                target_language=target_language,
                total_pages=extraction_result.total_pages,
                error=f"Translation failed: {str(e)}"
            )
    
    def _page_to_html(self, page: PageText) -> str:
        """
        Convert a PageText object to HTML with structure preservation.
        
        Args:
            page: PageText object from extraction
            
        Returns:
            HTML string with preserved structure
        """
        html_parts = ['<div class="page">']
        
        # Add page number
        html_parts.append(f'<div class="page-number">{page.page_number}</div>')
        
        # Process paragraphs
        for paragraph in page.paragraphs:
            # Escape HTML in the paragraph text
            escaped_text = html.escape(paragraph)
            
            # Detect if this might be a heading (heuristic: shorter than 100 chars)
            if len(paragraph) < 100 and paragraph.strip().endswith((':','.')) and not '\n' in paragraph:
                html_parts.append(f'<h3>{escaped_text}</h3>')
            else:
                html_parts.append(f'<p>{escaped_text}</p>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """
        Extract plain text from HTML.
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n\n')

def translate_document(
    extraction_result: ExtractionResult,
    source_language: str,
    target_language: str,
    api_key: str,
    api_url: str = "https://api.sarvam.ai/v1",
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> TranslationResult:
    """
    Translate an extracted document using Sarvam AI.
    
    Args:
        extraction_result: ExtractionResult from the extractor service
        source_language: Source language code
        target_language: Target language code
        api_key: Sarvam AI API key
        api_url: Base URL for the Sarvam API
        progress_callback: Optional callback for progress updates
        
    Returns:
        TranslationResult object
    """
    translator = SarvamTranslator(api_key=api_key, api_url=api_url)
    
    return translator.translate_extraction_result(
        extraction_result,
        source_language,
        target_language,
        progress_callback
    )
