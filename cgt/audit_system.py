"""
Main audit system orchestration.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .models import Official, Transaction, Filing
from .parsers.pdf_parser import PDFParser
from .parsers.ocr_parser import OCRParser
from .validators.data_validator import DataValidator
from .analyzers.performance_analyzer import PerformanceAnalyzer
from .exporters.json_exporter import JSONExporter

logger = logging.getLogger(__name__)


class FinancialTradeAuditSystem:
    """
    Main system for auditing U.S. federal officials' financial trades
    under the STOCK Act and EIGA.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the audit system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.pdf_parser = PDFParser(
            ocr_enabled=self.config.get('ocr_enabled', False)
        )
        self.ocr_parser = OCRParser()
        self.validator = DataValidator(self.config)
        self.analyzer = PerformanceAnalyzer(self.config)
        self.exporter = JSONExporter(
            output_directory=self.config.get('output_directory', 'output')
        )
        
        # Storage
        self.officials: Dict[str, Official] = {}
        self.filings: List[Filing] = []
        
        logger.info("Financial Trade Audit System initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using defaults.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return {}
    
    def process_filing(self, pdf_path: str, filing_metadata: Dict[str, Any]) -> Filing:
        """
        Process a single filing document.
        
        Args:
            pdf_path: Path to the PDF filing
            filing_metadata: Metadata about the filing
            
        Returns:
            Processed Filing object
        """
        # Create filing object
        filing = Filing(
            document_id=filing_metadata['document_id'],
            official_name=filing_metadata['official_name'],
            filing_date=filing_metadata['filing_date'],
            filing_type=filing_metadata.get('filing_type', 'PTR'),
            document_path=pdf_path
        )
        
        # Parse the PDF
        logger.info(f"Processing filing {filing.document_id} for {filing.official_name}")
        filing = self.pdf_parser.parse_filing(pdf_path, filing)
        
        # Validate and normalize transactions
        validated_transactions = []
        for transaction in filing.transactions:
            # Normalize
            transaction = self.validator.normalize_transaction(transaction)
            
            # Validate
            is_valid, errors = self.validator.validate_transaction(transaction)
            if is_valid:
                # Calculate quality score
                quality_score = self.validator.calculate_data_quality_score(transaction)
                transaction.confidence_score *= quality_score  # Adjust confidence
                validated_transactions.append(transaction)
            else:
                logger.warning(
                    f"Transaction validation failed for {transaction.security_name}: "
                    f"{', '.join(errors)}"
                )
        
        filing.transactions = validated_transactions
        self.filings.append(filing)
        
        # Add transactions to official records
        self._add_to_officials(filing)
        
        return filing
    
    def _add_to_officials(self, filing: Filing):
        """Add filing transactions to official records."""
        official_name = filing.official_name
        
        if official_name not in self.officials:
            self.officials[official_name] = Official(
                name=official_name,
                title="Federal Official",  # Would be extracted from filing
                chamber=None,
                state=None,
                party=None
            )
        
        official = self.officials[official_name]
        for transaction in filing.transactions:
            official.add_transaction(transaction)
    
    def process_multiple_filings(self, filings_data: List[Dict[str, Any]]) -> List[Filing]:
        """
        Process multiple filing documents.
        
        Args:
            filings_data: List of filing metadata dictionaries
            
        Returns:
            List of processed Filing objects
        """
        processed_filings = []
        
        for filing_data in filings_data:
            try:
                filing = self.process_filing(
                    filing_data['pdf_path'],
                    filing_data
                )
                processed_filings.append(filing)
            except Exception as e:
                logger.error(
                    f"Error processing filing {filing_data.get('document_id')}: {e}"
                )
        
        return processed_filings
    
    def calculate_all_metrics(self) -> List[Dict[str, Any]]:
        """
        Calculate performance metrics for all officials.
        
        Returns:
            List of metrics dictionaries
        """
        metrics = []
        
        for official in self.officials.values():
            official_metrics = self.analyzer.calculate_official_metrics(official)
            metrics.append(official_metrics.to_dict())
        
        return metrics
    
    def generate_comprehensive_report(self, output_filename: str = None) -> str:
        """
        Generate and export a comprehensive audit report.
        
        Args:
            output_filename: Optional output filename
            
        Returns:
            Path to the exported report
        """
        logger.info("Generating comprehensive report...")
        
        # Calculate metrics for all officials
        performance_metrics = []
        for official in self.officials.values():
            metrics = self.analyzer.calculate_official_metrics(official)
            performance_metrics.append(metrics)
        
        # Calculate aggregate statistics
        aggregate_stats = self.analyzer.calculate_aggregate_metrics(
            list(self.officials.values())
        )
        
        # Get top traders
        top_traders = self.analyzer.get_top_traders(
            list(self.officials.values()),
            limit=10
        )
        aggregate_stats['top_traders'] = top_traders
        
        # Export comprehensive report
        report_path = self.exporter.export_comprehensive_report(
            officials=list(self.officials.values()),
            metrics=performance_metrics,
            aggregate_stats=aggregate_stats,
            filename=output_filename
        )
        
        logger.info(f"Comprehensive report generated: {report_path}")
        return report_path
    
    def export_results(self, format: str = "json") -> Dict[str, str]:
        """
        Export all results to specified format.
        
        Args:
            format: Export format (currently only "json" supported)
            
        Returns:
            Dictionary of exported file paths
        """
        if format != "json":
            raise ValueError(f"Unsupported export format: {format}")
        
        exported_files = {}
        
        # Export officials
        if self.officials:
            path = self.exporter.export_officials(list(self.officials.values()))
            exported_files['officials'] = path
        
        # Export all transactions
        all_transactions = []
        for official in self.officials.values():
            all_transactions.extend(official.transactions)
        
        if all_transactions:
            path = self.exporter.export_transactions(all_transactions)
            exported_files['transactions'] = path
        
        # Export filings metadata
        if self.filings:
            path = self.exporter.export_filings(self.filings)
            exported_files['filings'] = path
        
        # Export performance metrics
        metrics = []
        for official in self.officials.values():
            metrics.append(self.analyzer.calculate_official_metrics(official))
        
        if metrics:
            path = self.exporter.export_performance_metrics(metrics)
            exported_files['metrics'] = path
        
        logger.info(f"Exported {len(exported_files)} result files")
        return exported_files
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the audit system status.
        
        Returns:
            Summary dictionary
        """
        total_transactions = sum(
            len(o.transactions) for o in self.officials.values()
        )
        
        return {
            "total_officials": len(self.officials),
            "total_filings": len(self.filings),
            "total_transactions": total_transactions,
            "filings_parsed": sum(1 for f in self.filings if f.parsed),
            "filings_with_ocr": sum(1 for f in self.filings if f.ocr_used),
            "average_parse_confidence": (
                sum(f.parse_confidence for f in self.filings) / len(self.filings)
                if self.filings else 0.0
            )
        }
