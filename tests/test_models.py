"""
Tests for data models.
"""
import unittest
from datetime import datetime

from cgt.models import (
    Transaction, Official, PerformanceMetrics, Filing,
    TransactionType, AmountRange
)


class TestTransaction(unittest.TestCase):
    """Test Transaction model."""
    
    def test_transaction_creation(self):
        """Test creating a transaction."""
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
        
        self.assertEqual(transaction.official_name, "John Smith")
        self.assertEqual(transaction.ticker_symbol, "AAPL")
        self.assertEqual(transaction.transaction_type, TransactionType.PURCHASE)
    
    def test_transaction_to_dict(self):
        """Test converting transaction to dictionary."""
        transaction = Transaction(
            official_name="Jane Doe",
            transaction_date=datetime(2023, 1, 15),
            security_name="Microsoft Corp.",
            ticker_symbol="MSFT",
            transaction_type=TransactionType.SALE,
            amount_range="$50,001 - $100,000",
            filing_date=datetime(2023, 2, 1),
            document_id="DOC-002"
        )
        
        data = transaction.to_dict()
        
        self.assertEqual(data['official_name'], "Jane Doe")
        self.assertEqual(data['ticker_symbol'], "MSFT")
        self.assertEqual(data['transaction_type'], "sale")
        self.assertIn('transaction_date', data)


class TestOfficial(unittest.TestCase):
    """Test Official model."""
    
    def test_official_creation(self):
        """Test creating an official."""
        official = Official(
            name="John Smith",
            title="Representative",
            chamber="House",
            state="CA",
            party="Democrat"
        )
        
        self.assertEqual(official.name, "John Smith")
        self.assertEqual(official.chamber, "House")
        self.assertEqual(len(official.transactions), 0)
    
    def test_add_transaction(self):
        """Test adding transactions to official."""
        official = Official(
            name="Jane Doe",
            title="Senator",
            chamber="Senate",
            state="NY",
            party="Republican"
        )
        
        transaction = Transaction(
            official_name="Jane Doe",
            transaction_date=datetime(2023, 1, 15),
            security_name="Tesla Inc.",
            ticker_symbol="TSLA",
            transaction_type=TransactionType.PURCHASE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 2, 1),
            document_id="DOC-003"
        )
        
        official.add_transaction(transaction)
        self.assertEqual(len(official.transactions), 1)


class TestPerformanceMetrics(unittest.TestCase):
    """Test PerformanceMetrics model."""
    
    def test_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            official_name="John Smith",
            total_transactions=25,
            purchase_count=15,
            sale_count=10,
            total_estimated_value=500000.0,
            average_confidence_score=0.85,
            filing_compliance_rate=0.92,
            data_quality_score=0.88
        )
        
        self.assertEqual(metrics.total_transactions, 25)
        self.assertEqual(metrics.purchase_count, 15)
        self.assertEqual(metrics.sale_count, 10)
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = PerformanceMetrics(
            official_name="Jane Doe",
            total_transactions=10,
            purchase_count=6,
            sale_count=4,
            total_estimated_value=200000.0,
            average_confidence_score=0.75,
            filing_compliance_rate=0.80,
            data_quality_score=0.70
        )
        
        data = metrics.to_dict()
        
        self.assertEqual(data['official_name'], "Jane Doe")
        self.assertEqual(data['total_transactions'], 10)
        self.assertIn('average_confidence_score', data)


class TestFiling(unittest.TestCase):
    """Test Filing model."""
    
    def test_filing_creation(self):
        """Test creating a filing."""
        filing = Filing(
            document_id="DOC-001",
            official_name="John Smith",
            filing_date=datetime(2023, 2, 1),
            filing_type="PTR",
            document_path=None
        )
        
        self.assertEqual(filing.document_id, "DOC-001")
        self.assertEqual(filing.filing_type, "PTR")
        self.assertFalse(filing.parsed)
        self.assertFalse(filing.ocr_used)


if __name__ == '__main__':
    unittest.main()
