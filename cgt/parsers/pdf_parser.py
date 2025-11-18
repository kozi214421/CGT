"""
PDF parsing module for extracting transaction data from official filings.
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

from ..models import Transaction, Filing, TransactionType

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF documents to extract transaction data."""
    
    def __init__(self, ocr_enabled: bool = False):
        """
        Initialize PDF parser.
        
        Args:
            ocr_enabled: Whether to use OCR for scanned documents
        """
        self.ocr_enabled = ocr_enabled
        
        if not pdfplumber:
            logger.warning("pdfplumber not installed. PDF parsing will be limited.")
    
    def parse_filing(self, pdf_path: str, filing: Filing) -> Filing:
        """
        Parse a PDF filing document.
        
        Args:
            pdf_path: Path to the PDF file
            filing: Filing object to populate
            
        Returns:
            Updated Filing object with extracted transactions
        """
        try:
            if pdfplumber:
                text = self._extract_text_pdfplumber(pdf_path)
            else:
                text = self._extract_text_pypdf2(pdf_path)
            
            if not text or len(text.strip()) < 50:
                logger.warning(f"Minimal text extracted from {pdf_path}. May need OCR.")
                if self.ocr_enabled:
                    filing.ocr_used = True
                    # OCR would be triggered here
                    logger.info("OCR processing would be applied here")
            
            # Extract transactions from text
            transactions = self._extract_transactions(text, filing)
            filing.transactions = transactions
            filing.parsed = True
            filing.parse_confidence = self._calculate_parse_confidence(text, transactions)
            
            logger.info(f"Parsed {len(transactions)} transactions from {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            filing.parsed = False
            filing.parse_confidence = 0.0
        
        return filing
    
    def _extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber."""
        if not pdfplumber:
            return ""
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"pdfplumber extraction error: {e}")
        
        return text
    
    def _extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (fallback)."""
        if not PyPDF2:
            return ""
        
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"PyPDF2 extraction error: {e}")
        
        return text
    
    def _extract_transactions(self, text: str, filing: Filing) -> List[Transaction]:
        """
        Extract transaction data from text.
        
        This is a simplified implementation. Real-world usage would need
        more sophisticated parsing based on actual filing formats.
        """
        transactions = []
        
        # Pattern matching for common transaction formats
        # Example: "01/15/2023 | Apple Inc. (AAPL) | Purchase | $15,001 - $50,000"
        pattern = r'(\d{1,2}/\d{1,2}/\d{4})\s*[\|\-]\s*([^|\-]+?)\s*(?:\(([A-Z]+)\))?\s*[\|\-]\s*(Purchase|Sale|Exchange)\s*[\|\-]\s*(\$[\d,]+\s*-\s*\$[\d,]+|\$[\d,]+\+)'
        
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            try:
                date_str, security, ticker, trans_type, amount = match.groups()
                
                transaction = Transaction(
                    official_name=filing.official_name,
                    transaction_date=datetime.strptime(date_str, "%m/%d/%Y"),
                    security_name=security.strip(),
                    ticker_symbol=ticker.strip() if ticker else None,
                    transaction_type=self._parse_transaction_type(trans_type),
                    amount_range=amount.strip(),
                    filing_date=filing.filing_date,
                    document_id=filing.document_id,
                    confidence_score=0.9,  # High confidence for regex match
                    raw_data={"matched_text": match.group(0)}
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Error parsing transaction match: {e}")
                continue
        
        return transactions
    
    def _parse_transaction_type(self, type_str: str) -> TransactionType:
        """Parse transaction type from string."""
        type_str = type_str.lower().strip()
        if "purchase" in type_str or "buy" in type_str:
            return TransactionType.PURCHASE
        elif "sale" in type_str or "sell" in type_str:
            return TransactionType.SALE
        else:
            return TransactionType.EXCHANGE
    
    def _calculate_parse_confidence(self, text: str, transactions: List[Transaction]) -> float:
        """
        Calculate confidence score for the parsing operation.
        
        Based on factors like:
        - Amount of text extracted
        - Number of transactions found
        - Presence of expected keywords
        """
        confidence = 0.5  # Base confidence
        
        # Text quality indicators
        if len(text) > 500:
            confidence += 0.1
        if len(text) > 1000:
            confidence += 0.1
        
        # Transaction extraction success
        if transactions:
            confidence += 0.2
        if len(transactions) > 5:
            confidence += 0.1
        
        # Presence of expected keywords
        keywords = ["transaction", "disclosure", "filing", "security", "purchase", "sale"]
        keyword_count = sum(1 for kw in keywords if kw.lower() in text.lower())
        confidence += min(keyword_count * 0.02, 0.1)
        
        return min(confidence, 1.0)
