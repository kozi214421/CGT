"""
PDF parsing utilities with primary and fallback methods.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


def discover_poppler_path(
    cli_arg: Optional[str] = None,
    env_var_name: str = "POPLER_BIN"
) -> Optional[str]:
    """
    Discover Poppler binaries path using multiple methods.

    Priority order:
    1. CLI argument (if provided)
    2. POPLER_BIN environment variable
    3. Common system locations

    Args:
        cli_arg: Path provided via CLI argument
        env_var_name: Environment variable name to check

    Returns:
        Valid Poppler path or None if not found
    """
    # 1. Check CLI argument
    if cli_arg:
        if _validate_poppler_path(cli_arg):
            logger.info(f"Using Poppler path from CLI argument: {cli_arg}")
            return cli_arg
        else:
            logger.warning(f"CLI-provided Poppler path not valid: {cli_arg}")

    # 2. Check environment variable
    env_path = os.environ.get(env_var_name)
    if env_path:
        if _validate_poppler_path(env_path):
            logger.info(f"Using Poppler path from {env_var_name}: {env_path}")
            return env_path
        else:
            logger.warning(f"Environment variable {env_var_name} path not valid: {env_path}")

    # 3. Check common locations
    common_locations = [
        "/usr/bin",
        "/usr/local/bin",
        "/opt/homebrew/bin",  # macOS Homebrew
        "C:\\Program Files\\poppler\\bin",  # Windows
        "C:\\Program Files (x86)\\poppler\\bin",
        os.path.expanduser("~/bin"),
    ]

    for location in common_locations:
        if _validate_poppler_path(location):
            logger.info(f"Found Poppler at common location: {location}")
            return location

    # Not found
    logger.warning("Poppler path not found. PDF fallback parsing may not work.")
    return None


def _validate_poppler_path(path: str) -> bool:
    """
    Validate that a path contains Poppler utilities.

    Args:
        path: Directory path to validate

    Returns:
        True if path contains Poppler binaries, False otherwise
    """
    if not path or not os.path.isdir(path):
        return False

    # Check for key Poppler utilities
    key_utils = ['pdfinfo', 'pdftoppm', 'pdftotext']

    # On Windows, add .exe extension
    if os.name == 'nt':
        key_utils = [f"{util}.exe" for util in key_utils]

    # Check if at least one utility exists
    for util in key_utils:
        util_path = os.path.join(path, util)
        if os.path.isfile(util_path):
            logger.debug(f"Found Poppler utility: {util_path}")
            return True

    return False


def parse_pdf(
    pdf_path: str,
    poppler_path: Optional[str] = None,
    use_fallback: bool = True
) -> Dict[str, Any]:
    """
    Parse a PDF file and extract text content.

    Uses pdfplumber as primary method, with pytesseract/pdf2image as fallback.

    Args:
        pdf_path: Path to PDF file
        poppler_path: Optional path to Poppler binaries
        use_fallback: Whether to use OCR fallback if primary method fails

    Returns:
        Dictionary with keys:
            - 'text': Extracted text content
            - 'method': Parsing method used ('pdfplumber' or 'ocr')
            - 'pages': Number of pages processed
            - 'success': Boolean indicating success

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF cannot be parsed by any method
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    logger.info(f"Parsing PDF: {pdf_path}")

    # Try primary method: pdfplumber
    try:
        result = _parse_with_pdfplumber(pdf_path)
        if result['success'] and result['text'].strip():
            logger.info(f"Successfully parsed PDF with pdfplumber: {len(result['text'])} chars")
            return result
    except Exception as e:
        logger.warning(f"pdfplumber parsing failed: {e}")

    # Try fallback method: OCR with pytesseract
    if use_fallback:
        try:
            result = _parse_with_ocr(pdf_path, poppler_path)
            if result['success'] and result['text'].strip():
                logger.info(f"Successfully parsed PDF with OCR: {len(result['text'])} chars")
                return result
        except Exception as e:
            logger.warning(f"OCR fallback parsing failed: {e}")

    # All methods failed
    error_msg = f"Failed to parse PDF with all available methods: {pdf_path}"
    logger.error(error_msg)
    raise ValueError(error_msg)


def _parse_with_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """
    Parse PDF using pdfplumber library.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with parsing results
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed")
        return {'success': False, 'text': '', 'method': 'pdfplumber', 'pages': 0}

    text_parts = []
    page_count = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                page_count += 1

        full_text = '\n'.join(text_parts)

        return {
            'success': True,
            'text': full_text,
            'method': 'pdfplumber',
            'pages': page_count
        }

    except Exception as e:
        logger.error(f"Error in pdfplumber parsing: {e}")
        return {'success': False, 'text': '', 'method': 'pdfplumber', 'pages': 0}


def _parse_with_ocr(pdf_path: str, poppler_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse PDF using OCR (pytesseract + pdf2image).

    Args:
        pdf_path: Path to PDF file
        poppler_path: Optional path to Poppler binaries

    Returns:
        Dictionary with parsing results
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        logger.error(f"OCR dependencies not installed: {e}")
        return {'success': False, 'text': '', 'method': 'ocr', 'pages': 0}

    text_parts = []

    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, poppler_path=poppler_path)

        # OCR each page
        for i, image in enumerate(images):
            logger.debug(f"OCR processing page {i+1}/{len(images)}")
            page_text = pytesseract.image_to_string(image)
            if page_text:
                text_parts.append(page_text)

        full_text = '\n'.join(text_parts)

        return {
            'success': True,
            'text': full_text,
            'method': 'ocr',
            'pages': len(images)
        }

    except Exception as e:
        logger.error(f"Error in OCR parsing: {e}")
        return {'success': False, 'text': '', 'method': 'ocr', 'pages': 0}


def extract_trades_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract trade information from parsed PDF text.

    This is a placeholder implementation. In a real system, this would
    use pattern matching, NLP, or other techniques to extract structured
    trade data from the text.

    Args:
        text: Extracted text from PDF

    Returns:
        List of trade dictionaries
    """
    logger.info(f"Extracting trades from {len(text)} characters of text")

    # Placeholder: In production, implement actual extraction logic
    # This would parse the specific format of congressional disclosure PDFs
    trades = []

    # Example structure - would be populated by real parsing logic
    if text:
        logger.debug("Text extraction would happen here - placeholder implementation")

    return trades
