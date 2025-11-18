"""
Financial metrics calculations for congressional trading analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import time

logger = logging.getLogger(__name__)


def fetch_stock_price(symbol: str, date: Optional[datetime] = None, max_retries: int = 3) -> Optional[float]:
    """
    Fetch stock price for a symbol with retry logic.
    
    Args:
        symbol: Stock ticker symbol
        date: Optional date for historical price (defaults to today)
        max_retries: Maximum number of retry attempts
        
    Returns:
        Stock price or None if unavailable
    """
    import yfinance as yf
    
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            
            if date:
                # Get historical data
                start_date = date - timedelta(days=5)  # Look back 5 days to handle weekends
                end_date = date + timedelta(days=1)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # Get the closest date
                    indexer = hist.index.get_indexer([date], method='nearest')
                    if len(indexer) > 0 and indexer[0] >= 0:
                        closest_idx = indexer[0]
                        price = hist.iloc[closest_idx]['Close']
                        logger.debug(f"Fetched historical price for {symbol} on {date}: ${price:.2f}")
                        return float(price)
            else:
                # Get current price
                info = ticker.info
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                if price:
                    logger.debug(f"Fetched current price for {symbol}: ${price:.2f}")
                    return float(price)
            
            logger.warning(f"No price data available for {symbol}")
            return None
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Failed to fetch price for {symbol} after {max_retries} attempts")
                return None


def calculate_trade_value(
    symbol: str,
    shares: float,
    date: Optional[datetime] = None,
    transaction_type: str = "buy"
) -> Dict[str, Any]:
    """
    Calculate the value of a trade.
    
    Args:
        symbol: Stock ticker symbol
        shares: Number of shares
        date: Trade date
        transaction_type: Type of transaction (buy/sell)
        
    Returns:
        Dictionary with trade value information
    """
    price = fetch_stock_price(symbol, date)
    
    if price:
        value = price * shares
        result = {
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "value": value,
            "transaction_type": transaction_type,
            "date": date.isoformat() if date else None,
        }
    else:
        result = {
            "symbol": symbol,
            "shares": shares,
            "price": None,
            "value": None,
            "transaction_type": transaction_type,
            "date": date.isoformat() if date else None,
            "error": "Price unavailable",
        }
    
    return result


def calculate_portfolio_performance(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate portfolio performance metrics from a list of trades.
    
    Args:
        trades: List of trade dictionaries with keys: symbol, shares, price, transaction_type, date
        
    Returns:
        Dictionary with performance metrics
    """
    if not trades:
        return {
            "total_trades": 0,
            "buy_count": 0,
            "sell_count": 0,
            "total_value": 0.0,
            "average_trade_value": 0.0,
        }
    
    buy_count = sum(1 for t in trades if t.get("transaction_type") == "buy")
    sell_count = sum(1 for t in trades if t.get("transaction_type") == "sell")
    
    total_value = sum(t.get("value", 0) or 0 for t in trades)
    average_value = total_value / len(trades) if trades else 0
    
    metrics = {
        "total_trades": len(trades),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "total_value": round(total_value, 2),
        "average_trade_value": round(average_value, 2),
        "symbols_traded": list(set(t.get("symbol") for t in trades if t.get("symbol"))),
    }
    
    logger.info(f"Calculated metrics: {metrics['total_trades']} trades, ${metrics['total_value']:,.2f} total value")
    return metrics


def calculate_return_on_investment(
    buy_price: float,
    sell_price: float,
    shares: float
) -> Dict[str, float]:
    """
    Calculate return on investment for a trade pair.
    
    Args:
        buy_price: Purchase price per share
        sell_price: Sale price per share
        shares: Number of shares
        
    Returns:
        Dictionary with ROI metrics
    """
    cost_basis = buy_price * shares
    proceeds = sell_price * shares
    profit = proceeds - cost_basis
    roi_percent = (profit / cost_basis * 100) if cost_basis > 0 else 0
    
    return {
        "cost_basis": round(cost_basis, 2),
        "proceeds": round(proceeds, 2),
        "profit": round(profit, 2),
        "roi_percent": round(roi_percent, 2),
    }


def analyze_trading_patterns(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze trading patterns from a list of trades.
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with pattern analysis
    """
    if not trades:
        return {"error": "No trades to analyze"}
    
    # Group by symbol
    by_symbol = {}
    for trade in trades:
        symbol = trade.get("symbol")
        if symbol:
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(trade)
    
    # Most traded symbols
    most_traded = sorted(
        by_symbol.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:5]
    
    analysis = {
        "unique_symbols": len(by_symbol),
        "most_traded_symbols": [{"symbol": s, "count": len(t)} for s, t in most_traded],
        "date_range": {
            "earliest": min(t.get("date") for t in trades if t.get("date")),
            "latest": max(t.get("date") for t in trades if t.get("date")),
        } if any(t.get("date") for t in trades) else None,
    }
    
    logger.info(f"Trading patterns: {analysis['unique_symbols']} unique symbols")
    return analysis
