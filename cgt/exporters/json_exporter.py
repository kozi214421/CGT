"""
JSON export module for verified results.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from ..models import Official, Transaction, Filing, PerformanceMetrics

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export verified data to structured JSON format."""
    
    def __init__(self, output_directory: str = "output"):
        """
        Initialize JSON exporter.
        
        Args:
            output_directory: Directory for output files
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def export_officials(
        self, 
        officials: List[Official],
        filename: str = None
    ) -> str:
        """
        Export officials and their transactions to JSON.
        
        Args:
            officials: List of officials to export
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to the output file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"officials_{timestamp}.json"
        
        output_path = self.output_directory / filename
        
        data = {
            "export_date": datetime.now().isoformat(),
            "total_officials": len(officials),
            "total_transactions": sum(len(o.transactions) for o in officials),
            "officials": [o.to_dict() for o in officials]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(officials)} officials to {output_path}")
        return str(output_path)
    
    def export_transactions(
        self,
        transactions: List[Transaction],
        filename: str = None
    ) -> str:
        """
        Export transactions to JSON.
        
        Args:
            transactions: List of transactions to export
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to the output file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transactions_{timestamp}.json"
        
        output_path = self.output_directory / filename
        
        data = {
            "export_date": datetime.now().isoformat(),
            "total_transactions": len(transactions),
            "transactions": [t.to_dict() for t in transactions]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(transactions)} transactions to {output_path}")
        return str(output_path)
    
    def export_performance_metrics(
        self,
        metrics: List[PerformanceMetrics],
        filename: str = None
    ) -> str:
        """
        Export performance metrics to JSON.
        
        Args:
            metrics: List of performance metrics to export
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to the output file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        output_path = self.output_directory / filename
        
        data = {
            "export_date": datetime.now().isoformat(),
            "total_officials": len(metrics),
            "metrics": [m.to_dict() for m in metrics]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(metrics)} performance metrics to {output_path}")
        return str(output_path)
    
    def export_comprehensive_report(
        self,
        officials: List[Official],
        metrics: List[PerformanceMetrics],
        aggregate_stats: Dict[str, Any],
        filename: str = None
    ) -> str:
        """
        Export a comprehensive report with all data.
        
        Args:
            officials: List of officials
            metrics: List of performance metrics
            aggregate_stats: Aggregate statistics
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to the output file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_report_{timestamp}.json"
        
        output_path = self.output_directory / filename
        
        data = {
            "report_metadata": {
                "export_date": datetime.now().isoformat(),
                "report_type": "comprehensive",
                "data_sources": ["STOCK Act filings", "EIGA disclosures"]
            },
            "aggregate_statistics": aggregate_stats,
            "officials": [o.to_dict() for o in officials],
            "performance_metrics": [m.to_dict() for m in metrics]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported comprehensive report to {output_path}")
        return str(output_path)
    
    def export_filings(
        self,
        filings: List[Filing],
        filename: str = None
    ) -> str:
        """
        Export filing metadata to JSON.
        
        Args:
            filings: List of filings to export
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to the output file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"filings_{timestamp}.json"
        
        output_path = self.output_directory / filename
        
        data = {
            "export_date": datetime.now().isoformat(),
            "total_filings": len(filings),
            "filings": [f.to_dict() for f in filings]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(filings)} filings to {output_path}")
        return str(output_path)
