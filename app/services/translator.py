"""
Translation service for the Legal Document Translator.

This service handles translation using Sarvam AI's translation API,
with intelligent text chunking, retry logic, and error handling.
"""

import time
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """Custom exception for translation errors."""
    pass

class LanguageCode(Enum):
    """Supported language codes."""
    GUJARATI = "gu"
    ENGLISH = "en"
    HINDI = "hi"

@dataclass
class TranslationRequest:
    """Data class for translation request."""
    text: str
    source_language: str
    target_language: str
    chunk_id: Optional[int] = None

@dataclass
class TranslationResult:
    """Data class for translation result."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    chunk_id: Optional[int] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None

class SarvamTranslator:
    """
    Translation service using Sarvam AI API.
    
    Handles chunking, rate limiting, retries, and error recovery.
    """
    
    def __init__(
        self, 
        api_key: str, 
        api_url: str = "https://api.sarvam.ai/v1",
        max_chars_per_request: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the translator.
        
        Args:
            api_key (str): Sarvam AI API key
            api_url (str): Base URL for Sarvam API
            max_chars_per_request (int): Maximum characters per API call
            max_retries (int): Maximum retry attempts
            retry_delay (float): Initial delay between retries (seconds)
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.max_chars = max_chars_per_request
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # Translation endpoint
        self.translate_endpoint = f"{self.api_url}/translate"
        
        logger.info(f"SarvamTranslator initialized with endpoint: {self.translate_endpoint}")
    
    def translate_text(
        self, 
        text: str, 
        source_lang: str = "gu", 
        target_lang: str = "en",
        preserve_formatting: bool = True
    ) -> TranslationResult:
        """
        Translate a single text chunk.
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            preserve_formatting (bool): Whether to preserve basic formatting
            
        Returns:
            TranslationResult: Translation result
            
        Raises:
            TranslationError: If translation fails
        """
        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                processing_time=0.0
            )
        
        # Clean and prepare text
        clean_text = self._prepare_text_for_translation(text, preserve_formatting)
        
        if len(clean_text) > self.max_chars:
            raise TranslationError(
                f"Text too long ({len(clean_text)} chars). Max allowed: {self.max_chars}"
            )
        
        start_time = time.time()
        
        try:
            # Make API request with retries
            translated_text = self._make_translation_request(
                clean_text, source_lang, target_lang
            )
            
            processing_time = time.time() - start_time
            
            # Post-process translated text
            if preserve_formatting:
                translated_text = self._restore_formatting(text, translated_text)
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Translation failed for text length {len(text)}: {str(e)}")
            raise TranslationError(f"Translation failed: {str(e)}")
    
    def translate_chunks(
        self, 
        text_chunks: List[str], 
        source_lang: str = "gu", 
        target_lang: str = "en",
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> List[TranslationResult]:
        """
        Translate multiple text chunks with progress tracking.
        
        Args:
            text_chunks (list): List of text chunks to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            progress_callback (callable): Progress callback function
            
        Returns:
            list: List of TranslationResult objects
            
        Raises:
            TranslationError: If translation fails
        """
        if not text_chunks:
            return []
        
        results = []
        total_chunks = len(text_chunks)
        
        logger.info(f"Starting translation of {total_chunks} chunks")
        
        for i, chunk in enumerate(text_chunks):
            try:
                # Translate individual chunk
                result = self.translate_text(chunk, source_lang, target_lang)
                result.chunk_id = i
                results.append(result)
                
                # Call progress callback if provided
                if progress_callback:
                    progress = int((i + 1) / total_chunks * 100)
                    progress_callback(progress, i + 1, total_chunks)
                
                # Rate limiting - small delay between requests
                if i < total_chunks - 1:  # Don't delay after last chunk
                    time.sleep(0.1)
                
                logger.debug(f"Translated chunk {i + 1}/{total_chunks}")
                
            except TranslationError:
                # Re-raise translation errors
                raise
            except Exception as e:
                logger.error(f"Unexpected error translating chunk {i}: {str(e)}")
                raise TranslationError(f"Failed to translate chunk {i}: {str(e)}")
        
        logger.info(f"Successfully translated {len(results)} chunks")
        return results
    
    def _make_translation_request(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """
        Make a single translation API request with retries.
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
            
        Raises:
            TranslationError: If all retry attempts fail
        """
        payload = {
            "input": text,
            "source_language_code": source_lang,
            "target_language_code": target_lang,
            "speaker_gender": "Male",  # Default for legal documents
            "mode": "formal",  # Formal tone for legal text
            "model": "mayura:v1",  # Sarvam's translation model
            "enable_preprocessing": True
        }
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Translation attempt {attempt + 1}/{self.max_retries}")
                
                response = self.session.post(
                    self.translate_endpoint,
                    json=payload,
                    timeout=30
                )
                
                # Handle HTTP errors
                if response.status_code == 401:
                    raise TranslationError("Invalid API key")
                elif response.status_code == 429:
                    raise TranslationError("Rate limit exceeded")
                elif response.status_code == 400:
                    error_msg = "Bad request - check input parameters"
                    try:
                        error_detail = response.json().get('message', '')
                        if error_detail:
                            error_msg += f": {error_detail}"
                    except:
                        pass
                    raise TranslationError(error_msg)
                elif response.status_code >= 500:
                    raise TranslationError(f"Server error: {response.status_code}")
                elif response.status_code != 200:
                    raise TranslationError(f"API error: {response.status_code}")
                
                # Parse response
                try:
                    response_data = response.json()
                except ValueError:
                    raise TranslationError("Invalid JSON response from API")
                
                # Extract translated text
                translated_text = response_data.get('translated_text')
                if not translated_text:
                    # Try alternative response formats
                    translated_text = response_data.get('translation', '')
                    if not translated_text:
                        raise TranslationError("No translated text in API response")
                
                return translated_text
                
            except TranslationError:
                # Don't retry on client errors
                raise
            except requests.exceptions.Timeout:
                last_error = TranslationError("Request timeout")
            except requests.exceptions.ConnectionError:
                last_error = TranslationError("Connection error")
            except requests.exceptions.RequestException as e:
                last_error = TranslationError(f"Request failed: {str(e)}")
            except Exception as e:
                last_error = TranslationError(f"Unexpected error: {str(e)}")
            
            # Wait before retry with exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Retrying in {wait_time:.1f}s (attempt {attempt + 1})")
                time.sleep(wait_time)
        
        # All retries failed
        raise last_error or TranslationError("Translation failed after retries")
    
    def _prepare_text_for_translation(self, text: str, preserve_formatting: bool) -> str:
        """
        Prepare text for translation by cleaning and normalizing.
        
        Args:
            text (str): Original text
            preserve_formatting (bool): Whether to preserve formatting
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Basic cleanup
        cleaned = text.strip()
        
        # Normalize whitespace but preserve intentional line breaks
        if preserve_formatting:
            # Replace multiple spaces with single space, but keep line breaks
            cleaned = ' '.join(cleaned.split(' '))
            # Normalize line breaks
            cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        else:
            # More aggressive cleanup
            cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _restore_formatting(self, original: str, translated: str) -> str:
        """
        Attempt to restore basic formatting from original to translated text.
        
        Args:
            original (str): Original text with formatting
            translated (str): Translated text
            
        Returns:
            str: Translated text with restored formatting
        """
        if not original or not translated:
            return translated
        
        # Simple heuristic: if original had multiple paragraphs,
        # try to maintain similar structure in translation
        original_lines = original.count('\n')
        translated_lines = translated.count('\n')
        
        # If original had significant line breaks and translated doesn't,
        # try to add some structure back
        if original_lines > 2 and translated_lines == 0:
            # Split translated text by sentences and add line breaks
            sentences = translated.split('. ')
            if len(sentences) > 2:
                # Add line breaks after every 2-3 sentences
                formatted_sentences = []
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        if i < len(sentences) - 1:
                            formatted_sentences.append(sentence + '.')
                        else:
                            formatted_sentences.append(sentence)
                        
                        # Add paragraph break every 2-3 sentences
                        if (i + 1) % 3 == 0 and i < len(sentences) - 1:
                            formatted_sentences.append('\n\n')
                        elif i < len(sentences) - 1:
                            formatted_sentences.append(' ')
                
                translated = ''.join(formatted_sentences)
        
        return translated
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported language codes and names.
        
        Returns:
            dict: Mapping of language codes to names
        """
        return {
            'gu': 'Gujarati',
            'en': 'English',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'mr': 'Marathi',
            'pa': 'Punjabi',
            'or': 'Odia'
        }
    
    def validate_language_pair(self, source_lang: str, target_lang: str) -> bool:
        """
        Validate if the language pair is supported.
        
        Args:
            source_lang (str): Source language code
            target_lang (str): Target language code
            
        Returns:
            bool: True if supported
        """
        supported = self.get_supported_languages()
        return source_lang in supported and target_lang in supported
    
    def estimate_cost(self, text_chunks: List[str]) -> Dict[str, Any]:
        """
        Estimate translation cost based on text length.
        
        Args:
            text_chunks (list): List of text chunks
            
        Returns:
            dict: Cost estimation details
        """
        total_chars = sum(len(chunk) for chunk in text_chunks)
        total_requests = len(text_chunks)
        
        # Rough cost estimation (adjust based on actual Sarvam pricing)
        estimated_cost_per_1k_chars = 0.02  # Example rate
        estimated_cost = (total_chars / 1000) * estimated_cost_per_1k_chars
        
        return {
            'total_characters': total_chars,
            'total_requests': total_requests,
            'estimated_cost_usd': round(estimated_cost, 4),
            'average_chunk_size': round(total_chars / total_requests) if total_requests > 0 else 0
        }

def create_translator(
    api_key: str,
    api_url: str = "https://api.sarvam.ai/v1",
    max_chars: int = 1000
) -> SarvamTranslator:
    """
    Factory function to create a translator instance.
    
    Args:
        api_key (str): Sarvam AI API key
        api_url (str): API base URL
        max_chars (int): Maximum characters per request
        
    Returns:
        SarvamTranslator: Configured translator instance
    """
    return SarvamTranslator(
        api_key=api_key,
        api_url=api_url,
        max_chars_per_request=max_chars
    )