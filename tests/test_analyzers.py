"""
Tests for performance analyzers.
"""
import unittest
from datetime import datetime, timedelta

from cgt.models import Transaction, Official, TransactionType
from cgt.analyzers.performance_analyzer import PerformanceAnalyzer


class TestPerformanceAnalyzer(unittest.TestCase):
    """Test PerformanceAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'performance_metrics': {
                'calculate_returns': True,
                'time_periods': ['1M', '3M', '6M', '1Y', 'lifetime']
            }
        }
        self.analyzer = PerformanceAnalyzer(self.config)
    
    def test_calculate_official_metrics(self):
        """Test calculating metrics for an official."""
        official = Official(
            name="John Smith",
            title="Representative",
            chamber="House",
            state="CA",
            party="Democrat"
        )
        
        # Add some transactions
        for i in range(10):
            transaction = Transaction(
                official_name="John Smith",
                transaction_date=datetime(2023, 1, 15 + i),
                security_name=f"Company {i}",
                ticker_symbol=f"SYM{i}",
                transaction_type=TransactionType.PURCHASE if i % 2 == 0 else TransactionType.SALE,
                amount_range="$15,001 - $50,000",
                filing_date=datetime(2023, 2, 1 + i),
                document_id=f"DOC-{i:03d}",
                confidence_score=0.9
            )
            official.add_transaction(transaction)
        
        metrics = self.analyzer.calculate_official_metrics(official)
        
        self.assertEqual(metrics.official_name, "John Smith")
        self.assertEqual(metrics.total_transactions, 10)
        self.assertEqual(metrics.purchase_count, 5)
        self.assertEqual(metrics.sale_count, 5)
        self.assertGreater(metrics.total_estimated_value, 0)
    
    def test_filter_by_time_period(self):
        """Test filtering transactions by time period."""
        now = datetime.now()
        transactions = [
            Transaction(
                official_name="John Smith",
                transaction_date=now - timedelta(days=15),
                security_name="Apple Inc.",
                ticker_symbol="AAPL",
                transaction_type=TransactionType.PURCHASE,
                amount_range="$15,001 - $50,000",
                filing_date=now,
                document_id="DOC-001"
            ),
            Transaction(
                official_name="John Smith",
                transaction_date=now - timedelta(days=60),
                security_name="Microsoft Corp.",
                ticker_symbol="MSFT",
                transaction_type=TransactionType.SALE,
                amount_range="$15,001 - $50,000",
                filing_date=now,
                document_id="DOC-002"
            ),
            Transaction(
                official_name="John Smith",
                transaction_date=now - timedelta(days=200),
                security_name="Tesla Inc.",
                ticker_symbol="TSLA",
                transaction_type=TransactionType.PURCHASE,
                amount_range="$15,001 - $50,000",
                filing_date=now,
                document_id="DOC-003"
            )
        ]
        
        # Test 1M filter
        filtered_1m = self.analyzer._filter_by_time_period(transactions, "1M")
        self.assertEqual(len(filtered_1m), 1)
        
        # Test 3M filter
        filtered_3m = self.analyzer._filter_by_time_period(transactions, "3M")
        self.assertEqual(len(filtered_3m), 2)
        
        # Test lifetime filter
        filtered_lifetime = self.analyzer._filter_by_time_period(transactions, "lifetime")
        self.assertEqual(len(filtered_lifetime), 3)
    
    def test_estimate_total_value(self):
        """Test estimating total transaction value."""
        transactions = [
            Transaction(
                official_name="John Smith",
                transaction_date=datetime(2023, 1, 15),
                security_name="Apple Inc.",
                ticker_symbol="AAPL",
                transaction_type=TransactionType.PURCHASE,
                amount_range="$15,001 - $50,000",
                filing_date=datetime(2023, 2, 1),
                document_id="DOC-001"
            ),
            Transaction(
                official_name="John Smith",
                transaction_date=datetime(2023, 1, 20),
                security_name="Microsoft Corp.",
                ticker_symbol="MSFT",
                transaction_type=TransactionType.SALE,
                amount_range="$50,001 - $100,000",
                filing_date=datetime(2023, 2, 5),
                document_id="DOC-002"
            )
        ]
        
        total_value = self.analyzer._estimate_total_value(transactions)
        
        # Should be midpoint of ranges: (32,500.50 + 75,000.50) = ~107,501
        self.assertGreater(total_value, 100000)
        self.assertLess(total_value, 120000)
    
    def test_calculate_compliance_rate(self):
        """Test calculating filing compliance rate."""
        compliant = Transaction(
            official_name="John Smith",
            transaction_date=datetime(2023, 1, 15),
            security_name="Apple Inc.",
            ticker_symbol="AAPL",
            transaction_type=TransactionType.PURCHASE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 1, 30),  # 15 days - compliant
            document_id="DOC-001"
        )
        
        non_compliant = Transaction(
            official_name="John Smith",
            transaction_date=datetime(2023, 1, 15),
            security_name="Microsoft Corp.",
            ticker_symbol="MSFT",
            transaction_type=TransactionType.SALE,
            amount_range="$15,001 - $50,000",
            filing_date=datetime(2023, 4, 1),  # 76 days - non-compliant
            document_id="DOC-002"
        )
        
        rate = self.analyzer._calculate_compliance_rate([compliant, non_compliant])
        self.assertEqual(rate, 0.5)  # 50% compliance
    
    def test_calculate_aggregate_metrics(self):
        """Test calculating aggregate metrics across officials."""
        officials = []
        
        for i in range(5):
            official = Official(
                name=f"Official {i}",
                title="Representative",
                chamber="House",
                state="CA",
                party="Democrat"
            )
            
            for j in range(3):
                transaction = Transaction(
                    official_name=official.name,
                    transaction_date=datetime(2023, 1, 15),
                    security_name=f"Company {j}",
                    ticker_symbol=f"SYM{j}",
                    transaction_type=TransactionType.PURCHASE,
                    amount_range="$15,001 - $50,000",
                    filing_date=datetime(2023, 2, 1),
                    document_id=f"DOC-{i}-{j}",
                    confidence_score=0.9
                )
                official.add_transaction(transaction)
            
            officials.append(official)
        
        aggregate = self.analyzer.calculate_aggregate_metrics(officials)
        
        self.assertEqual(aggregate['total_officials'], 5)
        self.assertEqual(aggregate['total_transactions'], 15)
        self.assertAlmostEqual(aggregate['average_transactions_per_official'], 3.0)


if __name__ == '__main__':
    unittest.main()
