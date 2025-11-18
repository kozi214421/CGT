"""
Data validation and normalization module.
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging

from ..models import Transaction, TransactionType

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate and normalize transaction data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data validator.
        
        Args:
            config: Configuration dictionary with validation rules
        """
        self.config = config
        self.required_fields = config.get('validation_rules', {}).get(
            'required_fields', []
        )
    
    def validate_transaction(self, transaction: Transaction) -> Tuple[bool, List[str]]:
        """
        Validate a transaction record.
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        if not transaction.official_name or not transaction.official_name.strip():
            errors.append("Missing official name")
        
        if not transaction.security_name or not transaction.security_name.strip():
            errors.append("Missing security name")
        
        # Validate dates
        if not isinstance(transaction.transaction_date, datetime):
            errors.append("Invalid transaction date")
        
        if not isinstance(transaction.filing_date, datetime):
            errors.append("Invalid filing date")
        
        # Check if filing date is after transaction date (must be)
        if (isinstance(transaction.transaction_date, datetime) and 
            isinstance(transaction.filing_date, datetime)):
            if transaction.filing_date < transaction.transaction_date:
                errors.append("Filing date cannot be before transaction date")
        
        # Validate transaction type
        if not isinstance(transaction.transaction_type, TransactionType):
            errors.append("Invalid transaction type")
        
        # Validate amount range format
        if not self._is_valid_amount_range(transaction.amount_range):
            errors.append(f"Invalid amount range format: {transaction.amount_range}")
        
        # Validate confidence score
        if not (0.0 <= transaction.confidence_score <= 1.0):
            errors.append(f"Confidence score must be between 0 and 1: {transaction.confidence_score}")
        
        # Validate ticker symbol format if present
        if transaction.ticker_symbol:
            if not self._is_valid_ticker(transaction.ticker_symbol):
                errors.append(f"Invalid ticker symbol format: {transaction.ticker_symbol}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def normalize_transaction(self, transaction: Transaction) -> Transaction:
        """
        Normalize transaction data to standard formats.
        
        Args:
            transaction: Transaction to normalize
            
        Returns:
            Normalized transaction
        """
        # Normalize official name
        transaction.official_name = self._normalize_name(transaction.official_name)
        
        # Normalize security name
        transaction.security_name = self._normalize_security_name(
            transaction.security_name
        )
        
        # Normalize ticker symbol
        if transaction.ticker_symbol:
            transaction.ticker_symbol = transaction.ticker_symbol.upper().strip()
        
        # Normalize amount range
        transaction.amount_range = self._normalize_amount_range(
            transaction.amount_range
        )
        
        return transaction
    
    def calculate_data_quality_score(self, transaction: Transaction) -> float:
        """
        Calculate a data quality score for the transaction.
        
        Args:
            transaction: Transaction to score
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        score = 0.0
        total_checks = 0
        
        # Check for ticker symbol
        total_checks += 1
        if transaction.ticker_symbol:
            score += 1.0
        
        # Check name quality
        total_checks += 1
        if transaction.official_name and len(transaction.official_name.split()) >= 2:
            score += 1.0
        
        # Check security name quality
        total_checks += 1
        if transaction.security_name and len(transaction.security_name) >= 3:
            score += 1.0
        
        # Check if dates are reasonable
        total_checks += 1
        if self._dates_are_reasonable(transaction):
            score += 1.0
        
        # Check confidence score
        total_checks += 1
        if transaction.confidence_score >= 0.8:
            score += 1.0
        elif transaction.confidence_score >= 0.6:
            score += 0.5
        
        # Check for raw data
        total_checks += 1
        if transaction.raw_data:
            score += 1.0
        
        return score / total_checks if total_checks > 0 else 0.0
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a person's name."""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Title case
        name = name.title()
        
        # Handle suffixes
        name = re.sub(r'\s+(Jr|Sr|Ii|Iii|Iv)\.?$', r' \1.', name, flags=re.IGNORECASE)
        
        return name
    
    def _normalize_security_name(self, name: str) -> str:
        """Normalize a security name."""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Standardize common abbreviations
        name = re.sub(r'\bInc\.?\b', 'Inc.', name, flags=re.IGNORECASE)
        name = re.sub(r'\bCorp\.?\b', 'Corp.', name, flags=re.IGNORECASE)
        name = re.sub(r'\bLtd\.?\b', 'Ltd.', name, flags=re.IGNORECASE)
        name = re.sub(r'\bLlc\.?\b', 'LLC', name, flags=re.IGNORECASE)
        
        return name
    
    def _normalize_amount_range(self, amount_range: str) -> str:
        """Normalize amount range to standard format."""
        if not amount_range:
            return ""
        
        # Remove extra whitespace
        amount_range = ' '.join(amount_range.split())
        
        # Ensure proper formatting
        amount_range = re.sub(r'(\d),(\d)', r'\1,\2', amount_range)
        
        return amount_range
    
    def _is_valid_amount_range(self, amount_range: str) -> bool:
        """Check if amount range is in valid format."""
        if not amount_range:
            return False
        
        # Pattern: $X,XXX - $X,XXX or $X,XXX+
        pattern = r'^\$[\d,]+(\s*-\s*\$[\d,]+|\+)$'
        return bool(re.match(pattern, amount_range))
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """Check if ticker symbol is in valid format."""
        if not ticker:
            return False
        
        # 1-5 uppercase letters
        pattern = r'^[A-Z]{1,5}$'
        return bool(re.match(pattern, ticker))
    
    def _dates_are_reasonable(self, transaction: Transaction) -> bool:
        """Check if transaction dates are reasonable."""
        try:
            now = datetime.now()
            
            # Transaction date should be in the past
            if transaction.transaction_date > now:
                return False
            
            # Filing date should be in the past
            if transaction.filing_date > now:
                return False
            
            # Filing should be after transaction (allowing same day)
            if transaction.filing_date < transaction.transaction_date:
                return False
            
            # Transaction shouldn't be too old (e.g., before STOCK Act 2012)
            min_date = datetime(2012, 1, 1)
            if transaction.transaction_date < min_date:
                return False
            
            return True
        except Exception:
            return False
