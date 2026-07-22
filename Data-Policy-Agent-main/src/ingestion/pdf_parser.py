"""
PDF Parser Module - Extracts text and metadata from PDF policy documents.
Supports OCR for scanned documents.
"""
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
from loguru import logger

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class PDFParser:
    """
    Parse PDF documents to extract text content and metadata.
    Supports both native PDF text and OCR for scanned documents.
    """
    
    def __init__(self, ocr_enabled: bool = True, ocr_language: str = 'eng'):
        """
        Initialize PDF parser.
        
        Args:
            ocr_enabled: Whether to use OCR for scanned documents
            ocr_language: Tesseract language code for OCR
        """
        self.ocr_enabled = ocr_enabled and OCR_AVAILABLE
        self.ocr_language = ocr_language
        
        if ocr_enabled and not OCR_AVAILABLE:
            logger.warning("OCR requested but pytesseract/pdf2image not available")
    
    async def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a PDF document and extract text content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing text, metadata, and hash
        """
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        logger.info(f"Parsing PDF: {path.name}")
        
        # Calculate file hash for deduplication
        file_hash = await self._calculate_hash(path)
        
        # Try native text extraction first
        text, page_texts = await self._extract_native_text(path)
        
        # If little text found and OCR is enabled, try OCR
        if len(text.strip()) < 100 and self.ocr_enabled:
            logger.info("Low text content detected, attempting OCR...")
            text, page_texts = await self._extract_ocr_text(path)
        
        # Extract metadata
        metadata = await self._extract_metadata(path)
        
        return {
            "text": text,
            "page_texts": page_texts,
            "page_count": len(page_texts),
            "metadata": metadata,
            "hash": file_hash,
            "source_path": str(path.absolute()),
            "file_size": path.stat().st_size
        }
    
    async def _calculate_hash(self, path: Path) -> str:
        """Calculate SHA-256 hash of the file."""
        def _hash():
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        
        return await asyncio.get_event_loop().run_in_executor(None, _hash)
    
    async def _extract_native_text(self, path: Path) -> tuple[str, List[str]]:
        """Extract text using pdfplumber or PyPDF."""
        def _extract():
            page_texts = []
            
            # Try pdfplumber first (better extraction)
            if pdfplumber:
                try:
                    with pdfplumber.open(path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text() or ""
                            page_texts.append(page_text)
                    return "\n\n".join(page_texts), page_texts
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
            
            # Fallback to PyPDF
            if PdfReader:
                try:
                    reader = PdfReader(str(path))
                    for page in reader.pages:
                        page_text = page.extract_text() or ""
                        page_texts.append(page_text)
                    return "\n\n".join(page_texts), page_texts
                except Exception as e:
                    logger.warning(f"PyPDF extraction failed: {e}")
            
            return "", []
        
        return await asyncio.get_event_loop().run_in_executor(None, _extract)
    
    async def _extract_ocr_text(self, path: Path) -> tuple[str, List[str]]:
        """Extract text using OCR for scanned documents."""
        if not OCR_AVAILABLE:
            return "", []
        
        def _ocr():
            page_texts = []
            try:
                # Convert PDF pages to images
                images = convert_from_path(str(path), dpi=300)
                
                for i, image in enumerate(images):
                    logger.debug(f"OCR processing page {i + 1}/{len(images)}")
                    text = pytesseract.image_to_string(image, lang=self.ocr_language)
                    page_texts.append(text)
                
                return "\n\n".join(page_texts), page_texts
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
                return "", []
        
        return await asyncio.get_event_loop().run_in_executor(None, _ocr)
    
    async def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract PDF metadata."""
        def _metadata():
            metadata = {
                "filename": path.name,
                "file_size_bytes": path.stat().st_size
            }
            
            if PdfReader:
                try:
                    reader = PdfReader(str(path))
                    if reader.metadata:
                        metadata.update({
                            "title": reader.metadata.get("/Title", ""),
                            "author": reader.metadata.get("/Author", ""),
                            "subject": reader.metadata.get("/Subject", ""),
                            "creator": reader.metadata.get("/Creator", ""),
                            "producer": reader.metadata.get("/Producer", ""),
                            "creation_date": str(reader.metadata.get("/CreationDate", "")),
                            "modification_date": str(reader.metadata.get("/ModDate", ""))
                        })
                except Exception as e:
                    logger.warning(f"Metadata extraction failed: {e}")
            
            return metadata
        
        return await asyncio.get_event_loop().run_in_executor(None, _metadata)
    
    async def parse_multiple(self, pdf_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Parse multiple PDF documents.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            List of parsed document dictionaries
        """
        tasks = [self.parse(path) for path in pdf_paths]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Attempt to extract logical sections from policy text.
        Uses common policy document patterns.
        
        Args:
            text: Full document text
            
        Returns:
            Dictionary mapping section names to content
        """
        import re
        
        sections = {}
        
        # Common section headers in policy documents
        section_patterns = [
            r'^(?:SECTION\s+)?(\d+\.?\s*[A-Z][A-Za-z\s]+)',
            r'^([A-Z][A-Z\s]+)(?:\n|:)',
            r'^(\d+\.\d*\s+[A-Z][A-Za-z\s]+)',
            r'^([IVXLCDM]+\.\s+[A-Z][A-Za-z\s]+)'
        ]
        
        # Try to identify sections
        lines = text.split('\n')
        current_section = "PREAMBLE"
        current_content = []
        
        for line in lines:
            is_header = False
            for pattern in section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_section = match.group(1).strip()
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
