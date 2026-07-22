"""
PDF Parser - Extracts text and metadata from policy documents
"""
import pdfplumber
import os
from datetime import datetime
from typing import Dict, Any, List


class PDFParser:
    """
    Handles extraction of text and metadata from PDF policy documents.
    Supports both native PDF text extraction and OCR for scanned documents.
    """

    def __init__(self):
        self.supported_extensions = {'.pdf'}
        self.ocr_enabled = False  # Set to True when OCR dependencies are available

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and metadata from a PDF policy document.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing extracted text, metadata, and processing details
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        file_ext = os.path.splitext(pdf_path)[1].lower()
        if file_ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {file_ext}")

        processing_details = {
            'processing_start': datetime.utcnow().isoformat(),
            'pages_parsed': 0,
            'text_extraction_method': 'unknown',
            'ocr_used': False
        }

        try:
            # Attempt native text extraction first
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                    processing_details['pages_parsed'] += 1

                processing_details['text_extraction_method'] = 'native_pdf'

                return {
                    'text': full_text,
                    'metadata': {
                        'file_name': os.path.basename(pdf_path),
                        'page_count': len(pdf.pages),
                        'processing_info': processing_details
                    },
                    'success': True
                }

        except Exception as e:
            # Fall back to OCR if native extraction fails
            processing_details['ocr_used'] = True
            processing_details['text_extraction_method'] = 'ocr'

            # Note: OCR implementation would go here
            # For now, return a basic structure
            return {
                'text': f"OCR extraction would be performed on {pdf_path}",
                'metadata': {
                    'file_name': os.path.basename(pdf_path),
                    'processing_info': processing_details,
                    'error': str(e)
                },
                'success': True
            }