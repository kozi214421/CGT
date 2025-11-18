"""
Tests for data validators.
"""
import unittest
from datetime import datetime, timedelta

from cgt.models import Transaction, TransactionType
from cgt.validators.data_validator import DataValidator


class TestDataValidator(unittest.TestCase):
    """Test DataValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'validation_rules': {
                'required_fields': [
                    'official_name',
                    'transaction_date',
                    'security_name',
                    'transaction_type',
                    'amount_range'
                ]
            }
        }
        self.validator = DataValidator(self.config)
    
    def test_validate_valid_transaction(self):
        """Test validating a valid transaction."""
        transaction = Transaction(
            official_name="John Smith",
            transaction_date=datetime(2023, 1, 15),
            security_name="Apple Inc.",
            ticker_symbol="AAPL",
            transaction_type=TransactionType.PURCHASE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 2, 1),
            document_id="DOC-001",
            confidence_score=0.9
        )
        
        is_valid, errors = self.validator.validate_transaction(transaction)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_filing_date(self):
        """Test validating transaction with invalid filing date."""
        transaction = Transaction(
            official_name="John Smith",
            transaction_date=datetime(2023, 2, 1),
            security_name="Apple Inc.",
            ticker_symbol="AAPL",
            transaction_type=TransactionType.PURCHASE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 1, 15),  # Before transaction date
            document_id="DOC-001"
        )
        
        is_valid, errors = self.validator.validate_transaction(transaction)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("filing date" in e.lower() for e in errors))
    
    def test_normalize_name(self):
        """Test name normalization."""
        names = [
            ("john smith", "John Smith"),
            ("JANE  DOE", "Jane Doe"),
            ("robert jones jr.", "Robert Jones Jr."),
        ]
        
        for input_name, expected in names:
            normalized = self.validator._normalize_name(input_name)
            self.assertEqual(normalized, expected)
    
    def test_normalize_security_name(self):
        """Test security name normalization."""
        names = [
            ("apple inc", "Apple Inc."),
            ("Microsoft Corp", "Microsoft Corp."),
            ("Tesla LLC", "Tesla LLC"),
        ]
        
        for input_name, expected in names:
            normalized = self.validator._normalize_security_name(input_name)
            self.assertIn("Inc." if "Inc" in expected else "Corp." if "Corp" in expected else "LLC", normalized)
    
    def test_is_valid_amount_range(self):
        """Test amount range validation."""
        valid_ranges = [
            "$15,001 - $50,000",
            "$1,001 - $15,000",
            "$50,000+",
        ]
        
        for amount_range in valid_ranges:
            self.assertTrue(self.validator._is_valid_amount_range(amount_range))
        
        invalid_ranges = [
            "15000-50000",
            "$15,001 to $50,000",
            "invalid",
        ]
        
        for amount_range in invalid_ranges:
            self.assertFalse(self.validator._is_valid_amount_range(amount_range))
    
    def test_is_valid_ticker(self):
        """Test ticker symbol validation."""
        valid_tickers = ["AAPL", "MSFT", "TSLA", "GOOG", "FB"]
        
        for ticker in valid_tickers:
            self.assertTrue(self.validator._is_valid_ticker(ticker))
        
        invalid_tickers = ["aapl", "123", "TOOLONG", ""]
        
        for ticker in invalid_tickers:
            self.assertFalse(self.validator._is_valid_ticker(ticker))
    
    def test_calculate_data_quality_score(self):
        """Test data quality score calculation."""
        high_quality = Transaction(
            official_name="John Smith",
            transaction_date=datetime(2023, 1, 15),
            security_name="Apple Inc.",
            ticker_symbol="AAPL",
            transaction_type=TransactionType.PURCHASE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 2, 1),
            document_id="DOC-001",
            confidence_score=0.95,
            raw_data={"source": "parsed"}
        )
        
        score = self.validator.calculate_data_quality_score(high_quality)
        self.assertGreater(score, 0.7)
        
        low_quality = Transaction(
            official_name="J",
            transaction_date=datetime(2023, 1, 15),
            security_name="X",
            ticker_symbol=None,
            transaction_type=TransactionType.PURCHASE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 2, 1),
            document_id="DOC-001",
            confidence_score=0.3,
            raw_data={}
        )
        
        score = self.validator.calculate_data_quality_score(low_quality)
        self.assertLess(score, 0.5)


if __name__ == '__main__':
    unittest.main()
