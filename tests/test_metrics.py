"""
Unit tests for congress_audit.metrics module.
"""
from datetime import datetime, timedelta
from congress_audit.metrics import (
    estimated_value_mid,
    compute_confidence,
    compute_accuracy,
    detect_late_filing,
    is_within_last_120_days
)


class TestEstimatedValueMid:
    """Tests for estimated_value_mid function."""

    def test_standard_range(self):
        """Test standard dollar range parsing."""
        assert estimated_value_mid("$1,001 - $15,000") == 8000.5
        assert estimated_value_mid("$15,001 - $50,000") == 32500.5
        assert estimated_value_mid("$50,001 - $100,000") == 75000.5

    def test_large_range(self):
        """Test parsing of large value ranges."""
        assert estimated_value_mid("$1,000,001 - $5,000,000") == 3000000.5

    def test_no_commas(self):
        """Test parsing ranges without comma separators."""
        assert estimated_value_mid("$1000 - $5000") == 3000.0

    def test_extra_spaces(self):
        """Test parsing with extra whitespace."""
        assert estimated_value_mid("$1,001  -  $15,000") == 8000.5
        assert estimated_value_mid("  $1,001 - $15,000  ") == 8000.5

    def test_invalid_input_none(self):
        """Test handling of None input."""
        assert estimated_value_mid(None) is None

    def test_invalid_input_empty(self):
        """Test handling of empty string."""
        assert estimated_value_mid("") is None

    def test_invalid_input_no_dash(self):
        """Test handling of input without dash separator."""
        assert estimated_value_mid("$15000") is None

    def test_invalid_input_non_numeric(self):
        """Test handling of non-numeric values."""
        assert estimated_value_mid("$abc - $def") is None

    def test_invalid_input_wrong_type(self):
        """Test handling of non-string input."""
        assert estimated_value_mid(12345) is None


class TestComputeConfidence:
    """Tests for compute_confidence function."""

    def test_all_fields_present(self):
        """Test confidence with all required fields present."""
        trade = {
            'ticker': 'AAPL',
            'transaction_date': '2024-01-15',
            'amount': '$15,001 - $50,000',
            'asset_description': 'Apple Inc.',
            'member_name': 'John Doe'
        }
        confidence = compute_confidence(trade)
        assert confidence == 1.0

    def test_missing_fields(self):
        """Test confidence with missing fields."""
        trade = {
            'ticker': 'AAPL',
            'transaction_date': '2024-01-15',
            # Missing other fields
        }
        confidence = compute_confidence(trade)
        assert 0.0 < confidence < 1.0

    def test_empty_fields(self):
        """Test confidence with empty field values."""
        trade = {
            'ticker': '',
            'transaction_date': '2024-01-15',
            'amount': 'N/A',
            'asset_description': 'Apple Inc.',
            'member_name': 'none'
        }
        confidence = compute_confidence(trade)
        assert confidence < 1.0

    def test_no_fields(self):
        """Test confidence with empty dictionary."""
        confidence = compute_confidence({})
        assert confidence == 0.0

    def test_invalid_input(self):
        """Test confidence with non-dict input."""
        confidence = compute_confidence(None)
        assert confidence == 0.0
        confidence = compute_confidence("not a dict")
        assert confidence == 0.0

    def test_confidence_bounds(self):
        """Test that confidence is always between 0 and 1."""
        test_cases = [
            {'ticker': 'AAPL'},
            {'ticker': 'AAPL', 'transaction_date': '2024-01-15'},
            {},
            {'ticker': '', 'transaction_date': '', 'amount': ''}
        ]
        for trade in test_cases:
            confidence = compute_confidence(trade)
            assert 0.0 <= confidence <= 1.0


class TestComputeAccuracy:
    """Tests for compute_accuracy function."""

    def test_exact_match(self):
        """Test accuracy when estimated equals actual."""
        accuracy = compute_accuracy(100.0, 100.0)
        assert accuracy == 1.0

    def test_close_values(self):
        """Test accuracy with close values."""
        accuracy = compute_accuracy(100.0, 105.0)
        assert 0.9 < accuracy < 1.0

    def test_different_values(self):
        """Test accuracy with different values."""
        accuracy = compute_accuracy(100.0, 150.0)
        assert 0.0 < accuracy < 1.0

    def test_none_inputs(self):
        """Test handling of None inputs."""
        assert compute_accuracy(None, 100.0) is None
        assert compute_accuracy(100.0, None) is None
        assert compute_accuracy(None, None) is None

    def test_zero_actual_price(self):
        """Test handling of zero actual price."""
        accuracy = compute_accuracy(100.0, 0.0)
        assert accuracy is None

    def test_accuracy_bounds(self):
        """Test that accuracy is clamped to [0, 1]."""
        test_cases = [
            (100.0, 100.0),
            (100.0, 99.0),
            (100.0, 200.0),
            (50.0, 100.0)
        ]
        for est, actual in test_cases:
            accuracy = compute_accuracy(est, actual)
            if accuracy is not None:
                assert 0.0 <= accuracy <= 1.0


class TestDetectLateFiling:
    """Tests for detect_late_filing function."""

    def test_on_time_filing(self):
        """Test filing within threshold."""
        trans_date = "2024-01-01"
        disc_date = "2024-01-30"
        assert detect_late_filing(trans_date, disc_date, threshold_days=45) is False

    def test_late_filing(self):
        """Test filing beyond threshold."""
        trans_date = "2024-01-01"
        disc_date = "2024-03-01"  # 60 days later
        assert detect_late_filing(trans_date, disc_date, threshold_days=45) is True

    def test_exact_threshold(self):
        """Test filing exactly at threshold."""
        trans_date = "2024-01-01"
        disc_date = "2024-02-15"  # 45 days later
        assert detect_late_filing(trans_date, disc_date, threshold_days=45) is False

    def test_different_date_formats(self):
        """Test with various date formats."""
        # ISO format
        assert detect_late_filing("2024-01-01", "2024-03-01", 45) is True
        # US format
        assert detect_late_filing("01/01/2024", "03/01/2024", 45) is True

    def test_invalid_dates(self):
        """Test handling of invalid date strings."""
        assert detect_late_filing("invalid", "2024-01-01") is False
        assert detect_late_filing("2024-01-01", "invalid") is False
        assert detect_late_filing("", "") is False


class TestIsWithinLast120Days:
    """Tests for is_within_last_120_days function."""

    def test_today(self):
        """Test with today's date."""
        today = datetime.now().strftime('%Y-%m-%d')
        assert is_within_last_120_days(today) is True

    def test_60_days_ago(self):
        """Test with date 60 days ago."""
        date_60_days_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        assert is_within_last_120_days(date_60_days_ago) is True

    def test_exactly_120_days_ago(self):
        """Test with date exactly 120 days ago."""
        date_120_days_ago = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
        assert is_within_last_120_days(date_120_days_ago) is True

    def test_121_days_ago(self):
        """Test with date beyond 120 days."""
        date_121_days_ago = (datetime.now() - timedelta(days=121)).strftime('%Y-%m-%d')
        assert is_within_last_120_days(date_121_days_ago) is False

    def test_200_days_ago(self):
        """Test with date well beyond 120 days."""
        date_200_days_ago = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')
        assert is_within_last_120_days(date_200_days_ago) is False

    def test_future_date(self):
        """Test with future date."""
        future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        # Future dates are not within last 120 days
        assert is_within_last_120_days(future_date) is False

    def test_custom_reference_date(self):
        """Test with custom reference date."""
        reference = datetime(2024, 6, 1)
        check_date = "2024-03-01"  # 92 days before reference
        assert is_within_last_120_days(check_date, reference) is True

        check_date = "2023-12-01"  # More than 120 days
        assert is_within_last_120_days(check_date, reference) is False

    def test_different_date_formats(self):
        """Test with various date formats."""
        recent_date = (datetime.now() - timedelta(days=30))

        # ISO format
        assert is_within_last_120_days(recent_date.strftime('%Y-%m-%d')) is True
        # US format
        assert is_within_last_120_days(recent_date.strftime('%m/%d/%Y')) is True

    def test_invalid_date(self):
        """Test handling of invalid date string."""
        assert is_within_last_120_days("invalid") is False
        assert is_within_last_120_days("") is False

    def test_edge_case_day_0(self):
        """Test with date 0 days ago (today)."""
        today = datetime.now().strftime('%Y-%m-%d')
        assert is_within_last_120_days(today) is True
