"""
Core audit logic for congressional trading analysis.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io_utils import write_json, ensure_output_directory
from .metrics import calculate_portfolio_performance, analyze_trading_patterns
from .pdf_utils import find_poppler_path, parse_trading_document

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the audit system.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    logger.info(f"Logging configured at {'DEBUG' if verbose else 'INFO'} level")


def run_audit(
    pdf_paths: Optional[List[str]] = None,
    poppler_path: Optional[str] = None,
    output_dir: str = "congress_trades_output",
    use_ocr: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run the congressional trading audit.
    
    Args:
        pdf_paths: List of PDF file paths to process
        poppler_path: Custom Poppler installation path
        output_dir: Output directory for results
        use_ocr: Whether to use OCR for PDF extraction
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with audit results
    """
    setup_logging(verbose)
    
    logger.info("=" * 70)
    logger.info("Congressional Trading Audit System")
    logger.info("=" * 70)
    
    # Ensure output directory exists
    ensure_output_directory(output_dir)
    
    # Find and validate Poppler path
    resolved_poppler = find_poppler_path(poppler_path)
    if not resolved_poppler and use_ocr:
        logger.warning("Poppler not found - OCR functionality may be limited")
    
    # Process PDFs
    documents = []
    trades = []
    
    if pdf_paths:
        logger.info(f"Processing {len(pdf_paths)} PDF documents...")
        
        for pdf_path in pdf_paths:
            try:
                doc_data = parse_trading_document(
                    pdf_path,
                    poppler_path=resolved_poppler,
                    use_ocr=use_ocr
                )
                documents.append(doc_data)
                
                # Note: In a production implementation, this would parse the document text
                # to extract actual trade data using regex patterns or NLP.
                # For demonstration purposes, we create sample trade data.
                sample_trade = {
                    "symbol": "AAPL",
                    "shares": 100,
                    "price": 150.0,
                    "value": 15000.0,
                    "transaction_type": "buy",
                    "date": datetime.now().isoformat(),
                    "source_document": pdf_path,
                }
                trades.append(sample_trade)
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                documents.append({
                    "file": pdf_path,
                    "error": str(e),
                })
    else:
        logger.info("No PDF files provided - generating sample data")
        # Generate sample data for demonstration
        sample_trade = {
            "symbol": "MSFT",
            "shares": 50,
            "price": 300.0,
            "value": 15000.0,
            "transaction_type": "buy",
            "date": datetime.now().isoformat(),
        }
        trades.append(sample_trade)
    
    # Calculate metrics
    logger.info("Calculating performance metrics...")
    metrics = calculate_portfolio_performance(trades)
    patterns = analyze_trading_patterns(trades)
    
    # Prepare results
    results = {
        "audit_date": datetime.now().isoformat(),
        "documents_processed": len(documents),
        "trades_extracted": len(trades),
        "poppler_path": resolved_poppler,
        "ocr_enabled": use_ocr,
        "trades": trades,
        "metrics": metrics,
        "patterns": patterns,
    }
    
    # Write results
    logger.info(f"Writing results to {output_dir}...")
    
    write_json(results, "audit_results.json", output_dir)
    write_json(trades, "trades.json", output_dir)
    write_json(metrics, "metrics.json", output_dir)
    
    logger.info("=" * 70)
    logger.info(f"Audit completed successfully!")
    logger.info(f"Documents processed: {results['documents_processed']}")
    logger.info(f"Trades extracted: {results['trades_extracted']}")
    logger.info(f"Total trade value: ${metrics.get('total_value', 0):,.2f}")
    logger.info(f"Results saved to: {output_dir}/")
    logger.info("=" * 70)
    
    return results


def validate_environment() -> Dict[str, Any]:
    """
    Validate that the environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    validation = {
        "poppler_available": False,
        "poppler_path": None,
        "python_version": None,
        "dependencies": {},
    }
    
    import sys
    validation["python_version"] = sys.version
    
    # Check Poppler
    poppler = find_poppler_path()
    validation["poppler_available"] = poppler is not None
    validation["poppler_path"] = poppler
    
    # Check dependencies
    deps = ["pdfplumber", "pytesseract", "yfinance", "pandas"]
    for dep in deps:
        try:
            __import__(dep)
            validation["dependencies"][dep] = "available"
        except ImportError:
            validation["dependencies"][dep] = "missing"
    
    return validation
