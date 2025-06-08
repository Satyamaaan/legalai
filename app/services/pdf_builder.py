"""
PDF builder service for the Legal Document Translator.

This service generates well-formatted PDF documents from translated text
using WeasyPrint, with support for proper typography, pagination, and
multilingual content.
"""

import os
import logging
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

class PDFBuildError(Exception):
    """Custom exception for PDF building errors."""
    pass

class PDFBuilder:
    """
    PDF builder service that creates formatted PDFs from translated text.
    """
    
    def __init__(self):
        """Initialize the PDF builder."""
        # FontConfiguration is no longer needed in WeasyPrint 60+
        # Font handling is now automatic
        
        # Default CSS for PDF styling
        self.default_css = """
        @page {
            size: A4;
            margin: 2.5cm 2cm;
            @top-center {
                content: "Translated Legal Document";
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: "Noto Sans", "Arial", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            text-align: justify;
        }
        
        .document-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }
        
        .document-title {
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .document-subtitle {
            font-size: 12pt;
            color: #666;
            margin-bottom: 5px;
        }
        
        .translation-info {
            font-size: 10pt;
            color: #888;
            font-style: italic;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        .paragraph {
            margin-bottom: 15px;
            text-indent: 1em;
        }
        
        .paragraph.no-indent {
            text-indent: 0;
        }
        
        .heading {
            font-size: 14pt;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 15px;
            color: #2c3e50;
            text-indent: 0;
        }
        
        .section {
            margin-bottom: 20px;
        }
        
        .gujarati {
            font-family: "Noto Sans Gujarati", "Shruti", sans-serif;
            font-size: 12pt;
            line-height: 1.8;
        }
        
        .english {
            font-family: "Noto Sans", "Arial", sans-serif;
            font-size: 11pt;
        }
        
        .legal-clause {
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
        }
        
        .signature-section {
            margin-top: 40px;
            page-break-inside: avoid;
        }
        
        .footer-info {
            position: fixed;
            bottom: 1cm;
            left: 2cm;
            right: 2cm;
            font-size: 9pt;
            color: #888;
            text-align: center;
        }
        """
    
    def build_pdf_from_text(
        self,
        text: str,
        output_path: str,
        title: str = "Translated Document",
        source_lang: str = "gu",
        target_lang: str = "en",
        custom_css: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a PDF from translated text.
        
        Args:
            text (str): Translated text content
            output_path (str): Path where PDF should be saved
            title (str): Document title
            source_lang (str): Source language code
            target_lang (str): Target language code
            custom_css (str, optional): Custom CSS styling
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: Path to the generated PDF
            
        Raises:
            PDFBuildError: If PDF generation fails
        """
        try:
            logger.info(f"Building PDF: {title}")
            
            # Generate HTML content
            html_content = self._generate_html_content(
                text, title, source_lang, target_lang, metadata
            )
            
            # Prepare CSS
            css_content = custom_css or self.default_css
            
            # Create PDF using WeasyPrint
            self._create_pdf_with_weasyprint(
                html_content, css_content, output_path
            )
            
            logger.info(f"PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise PDFBuildError(f"Failed to generate PDF: {str(e)}")
    
    def build_pdf_from_html(
        self,
        html_content: str,
        output_path: str,
        custom_css: Optional[str] = None
    ) -> str:
        """
        Build a PDF from HTML content.
        
        Args:
            html_content (str): HTML content
            output_path (str): Path where PDF should be saved
            custom_css (str, optional): Custom CSS styling
            
        Returns:
            str: Path to the generated PDF
            
        Raises:
            PDFBuildError: If PDF generation fails
        """
        try:
            css_content = custom_css or self.default_css
            self._create_pdf_with_weasyprint(
                html_content, css_content, output_path
            )
            return output_path
            
        except Exception as e:
            logger.error(f"PDF generation from HTML failed: {str(e)}")
            raise PDFBuildError(f"Failed to generate PDF from HTML: {str(e)}")
    
    def _generate_html_content(
        self,
        text: str,
        title: str,
        source_lang: str,
        target_lang: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate HTML content from text.
        
        Args:
            text (str): Text content
            title (str): Document title
            source_lang (str): Source language code
            target_lang (str): Target language code
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: Generated HTML content
        """
        # Language names mapping
        lang_names = {
            'gu': 'ગુજરાતી (Gujarati)',
            'en': 'English',
            'hi': 'हिन्दी (Hindi)'
        }
        
        source_lang_name = lang_names.get(source_lang, source_lang.upper())
        target_lang_name = lang_names.get(target_lang, target_lang.upper())
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Process text into paragraphs
        processed_content = self._process_text_content(text, target_lang)
        
        # Build HTML
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="{}">'.format(target_lang),
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>{self._escape_html(title)}</title>',
            '</head>',
            '<body>',
            '    <div class="document-header">',
            f'        <div class="document-title">{self._escape_html(title)}</div>',
            f'        <div class="document-subtitle">Legal Document Translation</div>',
            f'        <div class="translation-info">',
            f'            Translated from {source_lang_name} to {target_lang_name}<br>',
            f'            Generated on {timestamp}',
            f'        </div>',
            '    </div>',
            '',
            '    <div class="document-content">',
            processed_content,
            '    </div>',
            '',
            '    <div class="footer-info">',
            '        This document was automatically translated. Please verify important legal terms.',
            '    </div>',
            '</body>',
            '</html>'
        ]
        
        return '\n'.join(html_parts)
    
    def _process_text_content(self, text: str, target_lang: str) -> str:
        """
        Process text content and convert to structured HTML.
        
        Args:
            text (str): Raw text content
            target_lang (str): Target language code
            
        Returns:
            str: Processed HTML content
        """
        if not text:
            return '<div class="paragraph">No content available.</div>'
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        html_parts = []
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            
            # Clean up the paragraph
            para = para.replace('\n', ' ').replace('  ', ' ')
            
            # Detect if this might be a heading
            if self._is_likely_heading(para):
                html_parts.append(
                    f'<div class="heading">{self._escape_html(para)}</div>'
                )
            else:
                # Add language-specific class
                lang_class = "gujarati" if target_lang == "gu" else "english"
                indent_class = "no-indent" if i == 0 else ""
                
                html_parts.append(
                    f'<div class="paragraph {lang_class} {indent_class}">{self._escape_html(para)}</div>'
                )
        
        return '\n'.join(html_parts)
    
    def _is_likely_heading(self, text: str) -> bool:
        """
        Heuristic to determine if text is likely a heading.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            bool: True if likely a heading
        """
        # Simple heuristics for heading detection
        if len(text) < 100 and (
            text.strip().endswith(':') or
            text.strip().endswith('.') and len(text) < 50 or
            text.isupper() or
            text.startswith(('SECTION', 'CHAPTER', 'ARTICLE', 'CLAUSE'))
        ):
            return True
        return False
    
    def _create_pdf_with_weasyprint(
        self,
        html_content: str,
        css_content: str,
        output_path: str
    ) -> None:
        """
        Create PDF using WeasyPrint.
        
        Args:
            html_content (str): HTML content
            css_content (str): CSS styling
            output_path (str): Output file path
            
        Raises:
            PDFBuildError: If PDF creation fails
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Create HTML and CSS objects
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=css_content)
            
            # Generate PDF (font handling is automatic in WeasyPrint 60+)
            html_doc.write_pdf(
                output_path,
                stylesheets=[css_doc]
            )
            
        except Exception as e:
            raise PDFBuildError(f"WeasyPrint failed: {str(e)}")
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.
        
        Args:
            text (str): Text to escape
            
        Returns:
            str: Escaped text
        """
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def create_comparison_pdf(
        self,
        original_text: str,
        translated_text: str,
        output_path: str,
        title: str = "Translation Comparison",
        source_lang: str = "gu",
        target_lang: str = "en"
    ) -> str:
        """
        Create a side-by-side comparison PDF.
        
        Args:
            original_text (str): Original text
            translated_text (str): Translated text
            output_path (str): Output file path
            title (str): Document title
            source_lang (str): Source language code
            target_lang (str): Target language code
            
        Returns:
            str: Path to generated PDF
        """
        try:
            # Custom CSS for comparison layout
            comparison_css = self.default_css + """
            .comparison-container {
                display: flex;
                margin-bottom: 20px;
            }
            
            .original-column {
                width: 48%;
                margin-right: 4%;
                padding: 10px;
                border: 1px solid #ddd;
                background-color: #f9f9f9;
            }
            
            .translated-column {
                width: 48%;
                padding: 10px;
                border: 1px solid #ddd;
                background-color: #fff;
            }
            
            .column-header {
                font-weight: bold;
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 1px solid #ccc;
            }
            """
            
            # Process both texts
            original_paras = original_text.split('\n\n')
            translated_paras = translated_text.split('\n\n')
            
            # Build comparison HTML
            html_content = self._generate_comparison_html(
                original_paras, translated_paras, title, source_lang, target_lang
            )
            
            return self.build_pdf_from_html(html_content, output_path, comparison_css)
            
        except Exception as e:
            logger.error(f"Comparison PDF generation failed: {str(e)}")
            raise PDFBuildError(f"Failed to generate comparison PDF: {str(e)}")
    
    def _generate_comparison_html(
        self,
        original_paras: List[str],
        translated_paras: List[str],
        title: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Generate HTML for comparison PDF."""
        lang_names = {
            'gu': 'ગુજરાતી (Gujarati)',
            'en': 'English',
            'hi': 'हिन्दी (Hindi)'
        }
        
        html_parts = [
            '<!DOCTYPE html>',
            f'<html lang="{target_lang}">',
            '<head>',
            '    <meta charset="UTF-8">',
            f'    <title>{self._escape_html(title)}</title>',
            '</head>',
            '<body>',
            '    <div class="document-header">',
            f'        <div class="document-title">{self._escape_html(title)}</div>',
            f'        <div class="document-subtitle">Side-by-Side Translation Comparison</div>',
            '    </div>',
            ''
        ]
        
        # Add comparison sections
        max_paras = max(len(original_paras), len(translated_paras))
        
        for i in range(max_paras):
            original = original_paras[i] if i < len(original_paras) else ""
            translated = translated_paras[i] if i < len(translated_paras) else ""
            
            if original.strip() or translated.strip():
                html_parts.extend([
                    '    <div class="comparison-container">',
                    '        <div class="original-column">',
                    f'            <div class="column-header">{lang_names.get(source_lang, source_lang.upper())}</div>',
                    f'            <div class="gujarati">{self._escape_html(original.strip())}</div>',
                    '        </div>',
                    '        <div class="translated-column">',
                    f'            <div class="column-header">{lang_names.get(target_lang, target_lang.upper())}</div>',
                    f'            <div class="english">{self._escape_html(translated.strip())}</div>',
                    '        </div>',
                    '    </div>',
                    ''
                ])
        
        html_parts.extend([
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)

def create_pdf_builder() -> PDFBuilder:
    """
    Factory function to create a PDF builder instance.
    
    Returns:
        PDFBuilder: Configured PDF builder instance
    """
    return PDFBuilder()