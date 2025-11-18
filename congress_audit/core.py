"""
Core orchestration functions for congressional trading audit.
"""
import logging
import zipfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from congress_audit.io_utils import ensure_directory, safe_write_json
from congress_audit.metrics import (
    estimated_value_mid,
    compute_confidence,
    is_within_last_120_days,
    detect_late_filing
)

logger = logging.getLogger(__name__)


def extract_trades(
    source_url: Optional[str] = None,
    pdf_paths: Optional[List[str]] = None,
    poppler_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract congressional trades from various sources.

    Args:
        source_url: Optional URL to fetch disclosure data from
        pdf_paths: Optional list of local PDF files to parse
        poppler_path: Optional path to Poppler binaries for PDF parsing

    Returns:
        List of trade dictionaries with standardized fields
    """
    logger.info("Starting trade extraction")
    all_trades = []

    # Fetch from URL if provided
    if source_url:
        logger.info(f"Fetching trades from URL: {source_url}")
        url_trades = _fetch_trades_from_url(source_url)
        all_trades.extend(url_trades)
        logger.info(f"Extracted {len(url_trades)} trades from URL")

    # Parse PDFs if provided
    if pdf_paths:
        from congress_audit.pdf_utils import parse_pdf, extract_trades_from_text

        for pdf_path in pdf_paths:
            logger.info(f"Parsing PDF: {pdf_path}")
            try:
                result = parse_pdf(pdf_path, poppler_path=poppler_path)
                pdf_trades = extract_trades_from_text(result['text'])
                all_trades.extend(pdf_trades)
                logger.info(f"Extracted {len(pdf_trades)} trades from {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to parse PDF {pdf_path}: {e}")

    # If no sources provided, use placeholder data for demo
    if not source_url and not pdf_paths:
        logger.warning("No data sources provided, generating sample data")
        all_trades = _generate_sample_trades()

    # Enrich trades with computed metrics
    for trade in all_trades:
        _enrich_trade(trade)

    logger.info(f"Total trades extracted: {len(all_trades)}")
    return all_trades


def _fetch_trades_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Fetch trades from a web source.

    Args:
        url: URL to fetch from

    Returns:
        List of trade dictionaries
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        logger.debug("Requesting data from %s", url)
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse HTML - this would need to be customized for specific sites
        _soup = BeautifulSoup(response.content, 'html.parser')

        # Placeholder parsing logic
        trades = []
        logger.debug("Parsed HTML, found %d trades", len(trades))
        return trades

    except Exception as e:
        logger.error(f"Failed to fetch trades from URL: {e}")
        return []


def _generate_sample_trades() -> List[Dict[str, Any]]:
    """Generate sample trade data for testing/demo purposes."""
    today = datetime.now()
    recent_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    old_date = (today - timedelta(days=200)).strftime('%Y-%m-%d')

    return [
        {
            'member_name': 'John Smith',
            'ticker': 'AAPL',
            'asset_description': 'Apple Inc.',
            'transaction_type': 'Purchase',
            'transaction_date': recent_date,
            'disclosure_date': recent_date,
            'amount': '$15,001 - $50,000',
        },
        {
            'member_name': 'Jane Doe',
            'ticker': 'MSFT',
            'asset_description': 'Microsoft Corporation',
            'transaction_type': 'Sale',
            'transaction_date': old_date,
            'disclosure_date': old_date,
            'amount': '$50,001 - $100,000',
        }
    ]


def _enrich_trade(trade: Dict[str, Any]) -> None:
    """
    Enrich a trade dictionary with computed metrics.

    Args:
        trade: Trade dictionary to enrich (modified in place)
    """
    # Compute estimated value midpoint
    if 'amount' in trade:
        trade['estimated_value'] = estimated_value_mid(trade['amount'])

    # Compute confidence score
    trade['confidence'] = compute_confidence(trade)

    # Check if within last 120 days
    if 'transaction_date' in trade:
        trade['recent'] = is_within_last_120_days(trade['transaction_date'])

    # Check for late filing
    if 'transaction_date' in trade and 'disclosure_date' in trade:
        trade['late_filing'] = detect_late_filing(
            trade['transaction_date'],
            trade['disclosure_date']
        )


def save_output(trades: List[Dict[str, Any]], output_dir: str = "congress_trades_output") -> str:
    """
    Save trades to JSON output file.

    Args:
        trades: List of trade dictionaries
        output_dir: Output directory path

    Returns:
        Path to saved file
    """
    ensure_directory(output_dir)

    # Filter recent trades (last 120 days)
    recent_trades = [t for t in trades if t.get('recent', False)]

    output_path = f"{output_dir}/transactions_last_120_days.json"
    safe_write_json(recent_trades, output_path)

    logger.info(f"Saved {len(recent_trades)} recent trades to {output_path}")
    return output_path


def compute_lifetime_metrics(
    trades: List[Dict[str, Any]],
    output_dir: str = "congress_trades_output"
) -> str:
    """
    Compute lifetime performance metrics using yfinance.

    Args:
        trades: List of trade dictionaries
        output_dir: Output directory path

    Returns:
        Path to saved metrics file
    """
    logger.info("Computing lifetime performance metrics")

    if not trades:
        logger.warning("No trades provided for metrics computation")
        return ""

    try:
        import yfinance as yf
        import pandas as pd
    except ImportError as e:
        logger.error(f"Required libraries not available: {e}")
        return ""

    metrics = {}

    # Group trades by ticker
    tickers = {}
    for trade in trades:
        ticker = trade.get('ticker')
        if ticker and ticker not in ['', 'N/A']:
            if ticker not in tickers:
                tickers[ticker] = []
            tickers[ticker].append(trade)

    logger.info(f"Computing metrics for {len(tickers)} unique tickers")

    # Fetch data for each ticker with rate limiting and retry
    for ticker, ticker_trades in tickers.items():
        try:
            logger.debug(f"Fetching data for {ticker}")

            # Simple retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="1y")

                    if hist.empty:
                        logger.warning(f"No historical data for {ticker}")
                        break

                    # Calculate basic metrics
                    current_price = hist['Close'].iloc[-1] if not hist.empty else None
                    year_high = hist['High'].max() if not hist.empty else None
                    year_low = hist['Low'].min() if not hist.empty else None

                    metrics[ticker] = {
                        'current_price': float(current_price) if current_price else None,
                        'year_high': float(year_high) if year_high else None,
                        'year_low': float(year_low) if year_low else None,
                        'trade_count': len(ticker_trades),
                    }

                    logger.debug(f"Computed metrics for {ticker}")
                    break

                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1} for {ticker}: {e}")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        logger.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
                        break

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            continue

    # Save metrics
    ensure_directory(output_dir)
    output_path = f"{output_dir}/official_lifetime_performance.json"
    safe_write_json(metrics, output_path)

    logger.info(f"Saved lifetime metrics to {output_path}")
    return output_path


def save_compliance_summary(
    trades: List[Dict[str, Any]],
    output_dir: str = "congress_trades_output"
) -> str:
    """
    Generate and save compliance summary report.

    Args:
        trades: List of trade dictionaries
        output_dir: Output directory path

    Returns:
        Path to saved summary file
    """
    logger.info("Generating compliance summary")

    total_trades = len(trades)
    late_filings = sum(1 for t in trades if t.get('late_filing', False))
    recent_trades = sum(1 for t in trades if t.get('recent', False))

    # Calculate average confidence
    confidences = [t.get('confidence', 0) for t in trades]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Member statistics
    members = {}
    for trade in trades:
        member = trade.get('member_name', 'Unknown')
        if member not in members:
            members[member] = {'trade_count': 0, 'late_filings': 0}
        members[member]['trade_count'] += 1
        if trade.get('late_filing', False):
            members[member]['late_filings'] += 1

    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_trades': total_trades,
        'recent_trades': recent_trades,
        'late_filings': late_filings,
        'late_filing_rate': late_filings / total_trades if total_trades > 0 else 0,
        'average_confidence': round(avg_confidence, 3),
        'unique_members': len(members),
        'members': members,
    }

    ensure_directory(output_dir)
    output_path = f"{output_dir}/compliance_summary.json"
    safe_write_json(summary, output_path)

    logger.info(f"Saved compliance summary to {output_path}")
    return output_path


def create_zip_bundle(
    output_dir: str = "congress_trades_output",
    zip_name: str = "congress_trading_outputs.zip"
) -> str:
    """
    Create a ZIP bundle of all output files.

    Args:
        output_dir: Directory containing output files
        zip_name: Name of ZIP file to create

    Returns:
        Path to created ZIP file
    """
    logger.info(f"Creating ZIP bundle: {zip_name}")

    zip_path = f"{output_dir}/{zip_name}"

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all JSON files from output directory
            output_path = Path(output_dir)
            for file_path in output_path.glob('*.json'):
                arcname = file_path.name
                zipf.write(file_path, arcname)
                logger.debug(f"Added {arcname} to ZIP")

        logger.info(f"Created ZIP bundle at {zip_path}")
        return zip_path

    except Exception as e:
        logger.error(f"Failed to create ZIP bundle: {e}")
        raise



