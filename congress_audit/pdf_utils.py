"""
PDF utilities for extracting text from congressional trading documents.
Includes Poppler path detection and validation.
"""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def find_poppler_path(custom_path: Optional[str] = None) -> Optional[str]:
    """
    Find the Poppler installation path.
    
    Checks in order:
    1. Custom path provided as argument
    2. POPPLER_BIN environment variable
    3. Common installation paths for the OS
    4. System PATH
    
    Args:
        custom_path: Optional custom path to Poppler binaries
        
    Returns:
        Path to Poppler binaries directory or None if not found
    """
    # Check custom path
    if custom_path:
        if validate_poppler_path(custom_path):
            logger.info(f"Using custom Poppler path: {custom_path}")
            return custom_path
        else:
            logger.warning(f"Custom Poppler path invalid: {custom_path}")
    
    # Check environment variable
    env_path = os.environ.get('POPPLER_BIN')
    if env_path and validate_poppler_path(env_path):
        logger.info(f"Using Poppler path from POPPLER_BIN: {env_path}")
        return env_path
    
    # Check common paths based on OS
    system = platform.system()
    common_paths = []
    
    if system == "Windows":
        common_paths = [
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Program Files (x86)\poppler\Library\bin",
            r"C:\poppler\Library\bin",
        ]
    elif system == "Darwin":  # macOS
        common_paths = [
            "/usr/local/bin",
            "/opt/homebrew/bin",
            "/usr/local/Cellar/poppler",
        ]
    else:  # Linux
        common_paths = [
            "/usr/bin",
            "/usr/local/bin",
        ]
    
    for path in common_paths:
        if validate_poppler_path(path):
            logger.info(f"Found Poppler at common path: {path}")
            return path
    
    # Check if pdfinfo is in system PATH
    try:
        result = subprocess.run(
            ["pdfinfo", "-v"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("Poppler found in system PATH")
            return None  # Available in PATH, no specific path needed
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    logger.warning("Poppler not found in any standard location")
    return None


def validate_poppler_path(path: str) -> bool:
    """
    Validate that a path contains Poppler utilities.
    
    Args:
        path: Path to check
        
    Returns:
        True if path contains Poppler binaries, False otherwise
    """
    if not path or not os.path.exists(path):
        return False
    
    path_obj = Path(path)
    
    # Check for common Poppler utilities
    required_utils = ["pdfinfo", "pdftotext"]
    
    for util in required_utils:
        # Check with and without .exe extension
        if not (path_obj / util).exists() and not (path_obj / f"{util}.exe").exists():
            return False
    
    return True


def extract_text_from_pdf(pdf_path: str, poppler_path: Optional[str] = None) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        poppler_path: Optional path to Poppler binaries (for pdfplumber backend)
        
    Returns:
        Extracted text from the PDF
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If PDF extraction fails
    """
    import pdfplumber
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        text_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_content.append(text)
                    logger.debug(f"Extracted text from page {page_num}")
        
        full_text = "\n\n".join(text_content)
        logger.info(f"Successfully extracted {len(full_text)} characters from {pdf_path}")
        return full_text
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise RuntimeError(f"PDF extraction failed: {e}") from e


def extract_text_with_ocr(pdf_path: str, poppler_path: Optional[str] = None) -> str:
    """
    Extract text from a PDF using OCR (pytesseract).
    Useful for scanned documents.
    
    Args:
        pdf_path: Path to the PDF file
        poppler_path: Optional path to Poppler binaries
        
    Returns:
        Extracted text via OCR
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If OCR extraction fails
    """
    import pytesseract
    from pdf2image import convert_from_path
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        # Convert PDF to images
        kwargs = {}
        if poppler_path:
            kwargs['poppler_path'] = poppler_path
        
        images = convert_from_path(pdf_path, **kwargs)
        logger.info(f"Converted PDF to {len(images)} images")
        
        # Extract text from each image
        text_content = []
        for i, image in enumerate(images, 1):
            text = pytesseract.image_to_string(image)
            if text.strip():
                text_content.append(text)
                logger.debug(f"OCR extracted text from page {i}")
        
        full_text = "\n\n".join(text_content)
        logger.info(f"Successfully extracted {len(full_text)} characters via OCR")
        return full_text
        
    except Exception as e:
        logger.error(f"Failed to extract text via OCR: {e}")
        raise RuntimeError(f"OCR extraction failed: {e}") from e


def parse_trading_document(pdf_path: str, poppler_path: Optional[str] = None, use_ocr: bool = False) -> Dict:
    """
    Parse a congressional trading document and extract relevant information.
    
    Args:
        pdf_path: Path to the PDF file
        poppler_path: Optional path to Poppler binaries
        use_ocr: Whether to use OCR for extraction
        
    Returns:
        Dictionary containing parsed trading information
    """
    logger.info(f"Parsing document: {pdf_path}")
    
    # Extract text
    if use_ocr:
        text = extract_text_with_ocr(pdf_path, poppler_path)
    else:
        text = extract_text_from_pdf(pdf_path, poppler_path)
    
    # Basic parsing (simplified for demonstration)
    result = {
        "file": pdf_path,
        "text_length": len(text),
        "extraction_method": "ocr" if use_ocr else "standard",
        "raw_text": text[:500],  # First 500 chars for preview
    }
    
    logger.info(f"Document parsed: {result['extraction_method']} method, {result['text_length']} chars")
    return result
