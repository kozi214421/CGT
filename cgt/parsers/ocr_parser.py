"""
OCR module for processing scanned documents.
"""
import logging
from typing import Optional
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

logger = logging.getLogger(__name__)


class OCRParser:
    """Handle OCR operations for scanned documents."""
    
    def __init__(self, language: str = 'eng'):
        """
        Initialize OCR parser.
        
        Args:
            language: Language code for OCR (default: 'eng')
        """
        self.language = language
        
        if not pytesseract:
            logger.warning("pytesseract not installed. OCR functionality disabled.")
    
    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image file using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text or None if extraction failed
        """
        if not pytesseract or not Image:
            logger.error("OCR dependencies not available")
            return None
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.language)
            logger.info(f"Extracted {len(text)} characters from {image_path}")
            return text
        except Exception as e:
            logger.error(f"OCR extraction error for {image_path}: {e}")
            return None
    
    def extract_text_from_pdf_images(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from a scanned PDF by converting pages to images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text or None if extraction failed
        """
        # This would require pdf2image library for production use
        logger.info(f"PDF to image OCR would be performed on {pdf_path}")
        logger.info("For production, use pdf2image library to convert PDF pages to images")
        return None
    
    def get_confidence_score(self, image_path: str) -> float:
        """
        Get OCR confidence score for an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not pytesseract or not Image:
            return 0.0
        
        try:
            image = Image.open(image_path)
            # Get detailed OCR data including confidence
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence from word-level confidences
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                return avg_confidence / 100.0  # Convert to 0-1 scale
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating OCR confidence: {e}")
            return 0.0
