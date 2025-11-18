"""
Metrics computation functions for trade analysis.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def estimated_value_mid(amount_range: str) -> Optional[float]:
    """
    Calculate the midpoint of a disclosed transaction amount range.

    Args:
        amount_range: String like "$1,001 - $15,000" or "$15,001 - $50,000"

    Returns:
        Midpoint value as float, or None if parsing fails

    Examples:
        >>> estimated_value_mid("$1,001 - $15,000")
        8000.5
        >>> estimated_value_mid("$15,001 - $50,000")
        32500.5
    """
    if not amount_range or not isinstance(amount_range, str):
        logger.warning(f"Invalid amount_range: {amount_range}")
        return None

    try:
        # Remove dollar signs and spaces, split on dash
        cleaned = amount_range.replace('$', '').replace(',', '').strip()
        if '-' not in cleaned:
            logger.warning(f"No range separator found in: {amount_range}")
            return None

        parts = cleaned.split('-')
        if len(parts) != 2:
            logger.warning(f"Expected 2 parts in range, got {len(parts)}: {amount_range}")
            return None

        low = float(parts[0].strip())
        high = float(parts[1].strip())

        midpoint = (low + high) / 2.0
        logger.debug(f"Estimated midpoint for '{amount_range}': {midpoint}")
        return midpoint

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse amount range '{amount_range}': {e}")
        return None


def compute_confidence(trade_data: Dict[str, Any]) -> float:
    """
    Compute a confidence score for a trade record based on data completeness.

    Args:
        trade_data: Dictionary containing trade information

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not isinstance(trade_data, dict):
        return 0.0

    score = 0.0
    total_fields = 0

    # Check key fields
    key_fields = ['ticker', 'transaction_date', 'amount', 'asset_description', 'member_name']

    for field in key_fields:
        total_fields += 1
        value = trade_data.get(field)
        if value and str(value).strip() and str(value).lower() not in ['n/a', 'none', 'unknown']:
            score += 1

    confidence = score / total_fields if total_fields > 0 else 0.0
    logger.debug(f"Computed confidence {confidence:.2f} for trade: {trade_data.get('ticker', 'unknown')}")
    return confidence


def compute_accuracy(estimated_value: Optional[float], actual_price: Optional[float]) -> Optional[float]:
    """
    Compute accuracy metric comparing estimated value to actual price.

    Args:
        estimated_value: Estimated trade value midpoint
        actual_price: Actual market price at transaction time

    Returns:
        Accuracy score (0-1) or None if cannot be computed
    """
    if estimated_value is None or actual_price is None:
        return None

    if actual_price == 0:
        return None

    try:
        # Calculate percentage difference
        diff = abs(estimated_value - actual_price)
        accuracy = 1.0 - min(diff / abs(actual_price), 1.0)
        return max(0.0, min(1.0, accuracy))  # Clamp to [0, 1]
    except (ValueError, ZeroDivisionError) as e:
        logger.warning(f"Failed to compute accuracy: {e}")
        return None


def detect_late_filing(transaction_date: str, disclosure_date: str, threshold_days: int = 45) -> bool:
    """
    Detect if a trade was filed late based on STOCK Act requirements.

    Args:
        transaction_date: Date of transaction (ISO format or various formats)
        disclosure_date: Date of disclosure filing
        threshold_days: Maximum allowed days for filing (default 45)

    Returns:
        True if filing was late, False otherwise
    """
    try:
        # Parse dates - try multiple formats
        trans_dt = _parse_date_flexible(transaction_date)
        disc_dt = _parse_date_flexible(disclosure_date)

        if trans_dt is None or disc_dt is None:
            logger.warning(f"Could not parse dates: trans={transaction_date}, disc={disclosure_date}")
            return False

        days_diff = (disc_dt - trans_dt).days
        is_late = days_diff > threshold_days

        if is_late:
            logger.info(f"Late filing detected: {days_diff} days (threshold: {threshold_days})")

        return is_late

    except Exception as e:
        logger.warning(f"Error detecting late filing: {e}")
        return False


def is_within_last_120_days(date_str: str, reference_date: Optional[datetime] = None) -> bool:
    """
    Check if a date is within the last 120 days from reference date.

    Args:
        date_str: Date string to check
        reference_date: Reference date (defaults to today)

    Returns:
        True if within last 120 days, False otherwise
    """
    if reference_date is None:
        reference_date = datetime.now()

    try:
        check_date = _parse_date_flexible(date_str)
        if check_date is None:
            return False

        days_ago = (reference_date - check_date).days
        within_range = 0 <= days_ago <= 120

        logger.debug(f"Date {date_str} is {days_ago} days ago, within 120 days: {within_range}")
        return within_range

    except Exception as e:
        logger.warning(f"Error checking date range: {e}")
        return False


def _parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Parse date string with flexible format support.

    Args:
        date_str: Date string in various formats

    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None

    # Try multiple date formats
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    logger.debug(f"Could not parse date: {date_str}")
    return None
