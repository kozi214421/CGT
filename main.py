#!/usr/bin/env python3
"""
Main entry point for the CGT Financial Trade Audit System.

This system audits U.S. federal officials' financial trades under the STOCK Act
and EIGA, extracting and validating securities transactions from official
government filings.
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from cgt.audit_system import FinancialTradeAuditSystem


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('audit_system.log')
    ]
)

logger = logging.getLogger(__name__)


def create_example_data():
    """Create example filing data for demonstration."""
    return [
        {
            "document_id": "DOC-2023-001",
            "official_name": "John Smith",
            "filing_date": datetime(2023, 2, 15),
            "filing_type": "PTR",
            "pdf_path": "data/sample_filing_001.pdf"
        },
        {
            "document_id": "DOC-2023-002",
            "official_name": "Jane Doe",
            "filing_date": datetime(2023, 3, 10),
            "filing_type": "PTR",
            "pdf_path": "data/sample_filing_002.pdf"
        }
    ]


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="CGT Financial Trade Audit System - Audit federal officials' trades"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Path to input filings (PDF or directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory for results'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode with example data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 70)
    logger.info("CGT Financial Trade Audit System")
    logger.info("Auditing U.S. Federal Officials' Trades under STOCK Act & EIGA")
    logger.info("=" * 70)
    
    try:
        # Initialize the audit system
        system = FinancialTradeAuditSystem(config_path=args.config)
        
        if args.demo:
            logger.info("\n[DEMO MODE] Running with example data\n")
            
            # Create example filings data
            filings_data = create_example_data()
            
            logger.info("Note: In demo mode, actual PDF parsing is simulated.")
            logger.info("For real usage, provide actual PDF filings via --input\n")
            
            # Process example filings (would fail without actual PDFs, but structure is shown)
            # In real usage, these would be actual PDF files
            # system.process_multiple_filings(filings_data)
            
            # Show what the system can do
            logger.info("System Capabilities:")
            logger.info("  ✓ PDF parsing (PyPDF2, pdfplumber)")
            logger.info("  ✓ OCR for scanned documents (Tesseract)")
            logger.info("  ✓ Data normalization and validation")
            logger.info("  ✓ Confidence/accuracy scoring")
            logger.info("  ✓ Lifetime performance metrics calculation")
            logger.info("  ✓ Structured JSON export")
            
            logger.info("\nExample workflow:")
            logger.info("  1. Process filing PDFs -> Extract transactions")
            logger.info("  2. Validate and normalize data")
            logger.info("  3. Calculate performance metrics")
            logger.info("  4. Export verified results as JSON")
            
        elif args.input:
            logger.info(f"Processing filings from: {args.input}")
            
            input_path = Path(args.input)
            
            if not input_path.exists():
                logger.error(f"Input path does not exist: {args.input}")
                return 1
            
            # Process filings
            if input_path.is_file() and input_path.suffix.lower() == '.pdf':
                # Single PDF file
                filing_data = {
                    "document_id": input_path.stem,
                    "official_name": "Unknown Official",
                    "filing_date": datetime.now(),
                    "filing_type": "PTR",
                    "pdf_path": str(input_path)
                }
                system.process_filing(str(input_path), filing_data)
            
            elif input_path.is_dir():
                # Directory of PDF files
                pdf_files = list(input_path.glob("*.pdf"))
                logger.info(f"Found {len(pdf_files)} PDF files")
                
                filings_data = []
                for pdf_file in pdf_files:
                    filings_data.append({
                        "document_id": pdf_file.stem,
                        "official_name": "Unknown Official",
                        "filing_date": datetime.now(),
                        "filing_type": "PTR",
                        "pdf_path": str(pdf_file)
                    })
                
                system.process_multiple_filings(filings_data)
            
            # Generate report
            summary = system.get_summary()
            logger.info("\n" + "=" * 70)
            logger.info("Processing Summary")
            logger.info("=" * 70)
            logger.info(f"Total Officials: {summary['total_officials']}")
            logger.info(f"Total Filings: {summary['total_filings']}")
            logger.info(f"Total Transactions: {summary['total_transactions']}")
            logger.info(f"Filings Parsed: {summary['filings_parsed']}")
            logger.info(f"Filings with OCR: {summary['filings_with_ocr']}")
            logger.info(f"Average Parse Confidence: {summary['average_parse_confidence']:.2%}")
            
            # Export results
            logger.info("\nExporting results...")
            exported = system.export_results(format='json')
            
            logger.info("\nExported files:")
            for name, path in exported.items():
                logger.info(f"  {name}: {path}")
            
            # Generate comprehensive report
            report_path = system.generate_comprehensive_report()
            logger.info(f"\nComprehensive report: {report_path}")
        
        else:
            logger.info("\nNo input specified. Use --demo for demonstration or --input for actual data")
            logger.info("\nUsage examples:")
            logger.info("  python main.py --demo")
            logger.info("  python main.py --input data/filings/")
            logger.info("  python main.py --input data/filing.pdf")
            return 1
        
        logger.info("\n" + "=" * 70)
        logger.info("Audit process completed successfully")
        logger.info("=" * 70)
        return 0
        
    except Exception as e:
        logger.error(f"Error during audit process: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
