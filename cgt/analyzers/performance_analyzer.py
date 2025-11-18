"""
Performance metrics and analysis module.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict
import logging

from ..models import Transaction, Official, PerformanceMetrics, TransactionType

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyze trading performance and calculate metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize performance analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.performance_config = config.get('performance_metrics', {})
    
    def calculate_official_metrics(
        self, 
        official: Official,
        time_period: str = "lifetime"
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics for an official.
        
        Args:
            official: Official to analyze
            time_period: Time period for analysis (e.g., "1M", "lifetime")
            
        Returns:
            PerformanceMetrics object
        """
        # Filter transactions by time period
        transactions = self._filter_by_time_period(
            official.transactions, 
            time_period
        )
        
        if not transactions:
            return PerformanceMetrics(
                official_name=official.name,
                total_transactions=0,
                purchase_count=0,
                sale_count=0,
                total_estimated_value=0.0,
                average_confidence_score=0.0,
                filing_compliance_rate=0.0,
                data_quality_score=0.0,
                time_period=time_period
            )
        
        # Count transaction types
        purchase_count = sum(
            1 for t in transactions 
            if t.transaction_type == TransactionType.PURCHASE
        )
        sale_count = sum(
            1 for t in transactions 
            if t.transaction_type == TransactionType.SALE
        )
        
        # Calculate estimated value
        total_value = self._estimate_total_value(transactions)
        
        # Calculate average confidence
        avg_confidence = sum(t.confidence_score for t in transactions) / len(transactions)
        
        # Calculate compliance rate (filing within 45 days)
        compliance_rate = self._calculate_compliance_rate(transactions)
        
        # Calculate data quality score
        quality_score = self._calculate_aggregate_quality_score(transactions)
        
        return PerformanceMetrics(
            official_name=official.name,
            total_transactions=len(transactions),
            purchase_count=purchase_count,
            sale_count=sale_count,
            total_estimated_value=total_value,
            average_confidence_score=avg_confidence,
            filing_compliance_rate=compliance_rate,
            data_quality_score=quality_score,
            time_period=time_period
        )
    
    def calculate_aggregate_metrics(
        self, 
        officials: List[Official]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across all officials.
        
        Args:
            officials: List of officials to analyze
            
        Returns:
            Dictionary of aggregate metrics
        """
        all_transactions = []
        for official in officials:
            all_transactions.extend(official.transactions)
        
        if not all_transactions:
            return {
                "total_officials": len(officials),
                "total_transactions": 0,
                "average_transactions_per_official": 0.0,
                "total_estimated_value": 0.0,
                "overall_confidence_score": 0.0,
                "overall_compliance_rate": 0.0
            }
        
        return {
            "total_officials": len(officials),
            "total_transactions": len(all_transactions),
            "average_transactions_per_official": len(all_transactions) / len(officials) if officials else 0,
            "total_estimated_value": self._estimate_total_value(all_transactions),
            "overall_confidence_score": sum(t.confidence_score for t in all_transactions) / len(all_transactions),
            "overall_compliance_rate": self._calculate_compliance_rate(all_transactions)
        }
    
    def get_top_traders(
        self, 
        officials: List[Official], 
        limit: int = 10,
        by: str = "transaction_count"
    ) -> List[Dict[str, Any]]:
        """
        Get top traders by various metrics.
        
        Args:
            officials: List of officials
            limit: Number of top traders to return
            by: Metric to sort by ("transaction_count", "estimated_value")
            
        Returns:
            List of top traders with their metrics
        """
        trader_data = []
        
        for official in officials:
            if not official.transactions:
                continue
            
            metrics = self.calculate_official_metrics(official)
            
            trader_data.append({
                "name": official.name,
                "title": official.title,
                "chamber": official.chamber,
                "transaction_count": metrics.total_transactions,
                "estimated_value": metrics.total_estimated_value,
                "confidence_score": metrics.average_confidence_score
            })
        
        # Sort by specified metric
        if by == "transaction_count":
            trader_data.sort(key=lambda x: x["transaction_count"], reverse=True)
        elif by == "estimated_value":
            trader_data.sort(key=lambda x: x["estimated_value"], reverse=True)
        
        return trader_data[:limit]
    
    def _filter_by_time_period(
        self, 
        transactions: List[Transaction],
        time_period: str
    ) -> List[Transaction]:
        """Filter transactions by time period."""
        if time_period == "lifetime":
            return transactions
        
        now = datetime.now()
        cutoff_date = now
        
        # Parse time period
        if time_period == "1M":
            cutoff_date = now - timedelta(days=30)
        elif time_period == "3M":
            cutoff_date = now - timedelta(days=90)
        elif time_period == "6M":
            cutoff_date = now - timedelta(days=180)
        elif time_period == "1Y":
            cutoff_date = now - timedelta(days=365)
        
        return [
            t for t in transactions 
            if t.transaction_date >= cutoff_date
        ]
    
    def _estimate_total_value(self, transactions: List[Transaction]) -> float:
        """
        Estimate total value of transactions using midpoint of ranges.
        """
        total = 0.0
        
        for transaction in transactions:
            amount_str = transaction.amount_range
            
            # Extract numeric values from range
            numbers = []
            for match in re.finditer(r'\$?([\d,]+)', amount_str):
                num_str = match.group(1).replace(',', '')
                try:
                    numbers.append(float(num_str))
                except ValueError:
                    continue
            
            # Use midpoint of range or single value
            if len(numbers) >= 2:
                midpoint = (numbers[0] + numbers[1]) / 2
                total += midpoint
            elif len(numbers) == 1:
                # For "$X,XXX+" format, use the value as minimum estimate
                total += numbers[0]
        
        return total
    
    def _calculate_compliance_rate(self, transactions: List[Transaction]) -> float:
        """
        Calculate filing compliance rate.
        
        STOCK Act requires reporting within 45 days.
        """
        if not transactions:
            return 0.0
        
        compliant_count = 0
        
        for transaction in transactions:
            days_to_file = (transaction.filing_date - transaction.transaction_date).days
            if 0 <= days_to_file <= 45:
                compliant_count += 1
        
        return compliant_count / len(transactions)
    
    def _calculate_aggregate_quality_score(
        self, 
        transactions: List[Transaction]
    ) -> float:
        """Calculate aggregate data quality score."""
        if not transactions:
            return 0.0
        
        scores = []
        for transaction in transactions:
            score = 0.0
            checks = 0
            
            # Has ticker symbol
            checks += 1
            if transaction.ticker_symbol:
                score += 1.0
            
            # Has reasonable confidence
            checks += 1
            if transaction.confidence_score >= 0.7:
                score += 1.0
            
            # Has raw data
            checks += 1
            if transaction.raw_data:
                score += 1.0
            
            scores.append(score / checks if checks > 0 else 0.0)
        
        return sum(scores) / len(scores)


import re  # Import at module level
