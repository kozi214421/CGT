"""
Unit tests for congress_audit.metrics module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from congress_audit.metrics import (
    fetch_stock_price,
    calculate_trade_value,
    calculate_portfolio_performance,
    calculate_return_on_investment,
    analyze_trading_patterns,
)


class TestFetchStockPrice:
    """Tests for fetch_stock_price function."""
    
    @patch('yfinance.Ticker')
    def test_fetch_current_price_success(self, mock_ticker_class):
        """Test fetching current stock price successfully."""
        mock_ticker = Mock()
        mock_ticker.info = {'currentPrice': 150.50}
        mock_ticker_class.return_value = mock_ticker
        
        price = fetch_stock_price('AAPL')
        
        assert price == 150.50
        mock_ticker_class.assert_called_once_with('AAPL')
    
    @patch('yfinance.Ticker')
    def test_fetch_historical_price_success(self, mock_ticker_class):
        """Test fetching historical stock price successfully."""
        import pandas as pd
        
        mock_ticker = Mock()
        # Create mock historical data
        dates = pd.date_range(start='2023-01-01', periods=5)
        mock_hist = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0]
        }, index=dates)
        mock_ticker.history.return_value = mock_hist
        mock_ticker_class.return_value = mock_ticker
        
        test_date = datetime(2023, 1, 3)
        price = fetch_stock_price('AAPL', date=test_date)
        
        assert price is not None
        assert isinstance(price, float)
        mock_ticker.history.assert_called_once()
    
    @patch('yfinance.Ticker')
    def test_fetch_price_failure(self, mock_ticker_class):
        """Test handling of fetch failure."""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker
        
        price = fetch_stock_price('INVALID')
        
        assert price is None
    
    @patch('yfinance.Ticker')
    def test_fetch_price_with_retry(self, mock_ticker_class):
        """Test retry logic on failure."""
        mock_ticker_class.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            Mock(info={'currentPrice': 200.0})
        ]
        
        price = fetch_stock_price('TSLA', max_retries=3)
        
        assert price == 200.0
        assert mock_ticker_class.call_count == 3


class TestCalculateTradeValue:
    """Tests for calculate_trade_value function."""
    
    @patch('congress_audit.metrics.fetch_stock_price')
    def test_calculate_buy_value(self, mock_fetch):
        """Test calculating trade value for a buy."""
        mock_fetch.return_value = 150.0
        
        result = calculate_trade_value('AAPL', 100, transaction_type='buy')
        
        assert result['symbol'] == 'AAPL'
        assert result['shares'] == 100
        assert result['price'] == 150.0
        assert result['value'] == 15000.0
        assert result['transaction_type'] == 'buy'
    
    @patch('congress_audit.metrics.fetch_stock_price')
    def test_calculate_value_with_date(self, mock_fetch):
        """Test calculating trade value with a specific date."""
        mock_fetch.return_value = 200.0
        test_date = datetime(2023, 6, 15)
        
        result = calculate_trade_value('MSFT', 50, date=test_date, transaction_type='sell')
        
        assert result['value'] == 10000.0
        assert result['date'] == test_date.isoformat()
        mock_fetch.assert_called_once_with('MSFT', test_date)
    
    @patch('congress_audit.metrics.fetch_stock_price')
    def test_calculate_value_price_unavailable(self, mock_fetch):
        """Test handling when price is unavailable."""
        mock_fetch.return_value = None
        
        result = calculate_trade_value('UNKNOWN', 100)
        
        assert result['value'] is None
        assert result['price'] is None
        assert 'error' in result


class TestCalculatePortfolioPerformance:
    """Tests for calculate_portfolio_performance function."""
    
    def test_empty_trades_list(self):
        """Test with empty trades list."""
        metrics = calculate_portfolio_performance([])
        
        assert metrics['total_trades'] == 0
        assert metrics['buy_count'] == 0
        assert metrics['sell_count'] == 0
        assert metrics['total_value'] == 0.0
    
    def test_multiple_trades(self):
        """Test with multiple trades."""
        trades = [
            {'symbol': 'AAPL', 'value': 10000, 'transaction_type': 'buy'},
            {'symbol': 'MSFT', 'value': 15000, 'transaction_type': 'buy'},
            {'symbol': 'AAPL', 'value': 12000, 'transaction_type': 'sell'},
        ]
        
        metrics = calculate_portfolio_performance(trades)
        
        assert metrics['total_trades'] == 3
        assert metrics['buy_count'] == 2
        assert metrics['sell_count'] == 1
        assert metrics['total_value'] == 37000.0
        assert metrics['average_trade_value'] == pytest.approx(12333.33, rel=0.01)
        assert set(metrics['symbols_traded']) == {'AAPL', 'MSFT'}
    
    def test_trades_with_none_values(self):
        """Test handling trades with None values."""
        trades = [
            {'symbol': 'AAPL', 'value': 10000, 'transaction_type': 'buy'},
            {'symbol': 'UNKNOWN', 'value': None, 'transaction_type': 'buy'},
        ]
        
        metrics = calculate_portfolio_performance(trades)
        
        assert metrics['total_trades'] == 2
        assert metrics['total_value'] == 10000.0


class TestCalculateReturnOnInvestment:
    """Tests for calculate_return_on_investment function."""
    
    def test_profitable_trade(self):
        """Test ROI calculation for profitable trade."""
        result = calculate_return_on_investment(100.0, 120.0, 50)
        
        assert result['cost_basis'] == 5000.0
        assert result['proceeds'] == 6000.0
        assert result['profit'] == 1000.0
        assert result['roi_percent'] == 20.0
    
    def test_losing_trade(self):
        """Test ROI calculation for losing trade."""
        result = calculate_return_on_investment(100.0, 80.0, 50)
        
        assert result['cost_basis'] == 5000.0
        assert result['proceeds'] == 4000.0
        assert result['profit'] == -1000.0
        assert result['roi_percent'] == -20.0
    
    def test_zero_cost_basis(self):
        """Test ROI with zero cost basis."""
        result = calculate_return_on_investment(0.0, 100.0, 50)
        
        assert result['roi_percent'] == 0.0


class TestAnalyzeTradingPatterns:
    """Tests for analyze_trading_patterns function."""
    
    def test_empty_trades(self):
        """Test with empty trades list."""
        result = analyze_trading_patterns([])
        
        assert 'error' in result
    
    def test_pattern_analysis(self):
        """Test trading pattern analysis."""
        trades = [
            {'symbol': 'AAPL', 'date': '2023-01-01'},
            {'symbol': 'AAPL', 'date': '2023-01-15'},
            {'symbol': 'MSFT', 'date': '2023-02-01'},
            {'symbol': 'TSLA', 'date': '2023-03-01'},
            {'symbol': 'AAPL', 'date': '2023-03-15'},
        ]
        
        result = analyze_trading_patterns(trades)
        
        assert result['unique_symbols'] == 3
        assert len(result['most_traded_symbols']) <= 5
        # AAPL should be most traded with 3 occurrences
        assert result['most_traded_symbols'][0]['symbol'] == 'AAPL'
        assert result['most_traded_symbols'][0]['count'] == 3
    
    def test_pattern_with_date_range(self):
        """Test pattern analysis includes date range."""
        trades = [
            {'symbol': 'AAPL', 'date': '2023-01-01'},
            {'symbol': 'MSFT', 'date': '2023-06-01'},
        ]
        
        result = analyze_trading_patterns(trades)
        
        assert result['date_range'] is not None
        assert result['date_range']['earliest'] == '2023-01-01'
        assert result['date_range']['latest'] == '2023-06-01'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
