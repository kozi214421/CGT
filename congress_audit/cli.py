"""
Command-line interface for congress trading audit tool.
"""
import argparse
import logging
import sys
import os
from typing import Optional

from congress_audit.core import (
    extract_trades,
    save_output,
    compute_lifetime_metrics,
    save_compliance_summary,
    create_zip_bundle
)
from congress_audit.pdf_utils import parse_pdf, discover_poppler_path
from congress_audit.io_utils import ensure_directory


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def cmd_run(args: argparse.Namespace) -> int:
    """
    Execute the full audit workflow.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting congress trading audit")

    try:
        # Discover Poppler path
        poppler_path = discover_poppler_path(
            cli_arg=args.poppler_path,
            env_var_name="POPLER_BIN"
        )

        if poppler_path:
            logger.info(f"Using Poppler path: {poppler_path}")
        else:
            logger.warning("Poppler not found - PDF OCR fallback may not work")

        # Create output directory
        output_dir = args.output_dir or "congress_trades_output"
        ensure_directory(output_dir)
        logger.info(f"Output directory: {output_dir}")

        # Extract trades
        trades = extract_trades(
            source_url=args.source_url,
            pdf_paths=args.pdf_files,
            poppler_path=poppler_path
        )

        if not trades:
            logger.warning("No trades extracted")
        else:
            logger.info(f"Extracted {len(trades)} trades")

        # Save outputs
        save_output(trades, output_dir)
        compute_lifetime_metrics(trades, output_dir)
        save_compliance_summary(trades, output_dir)

        # Create ZIP bundle
        zip_path = create_zip_bundle(output_dir)
        logger.info(f"All outputs saved to {output_dir}")
        logger.info(f"ZIP bundle created: {zip_path}")

        logger.info("Audit completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Audit failed: {e}", exc_info=True)
        return 1


def cmd_parse_pdf(args: argparse.Namespace) -> int:
    """
    Parse a single PDF file and display results.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = logging.getLogger(__name__)

    try:
        # Discover Poppler path
        poppler_path = discover_poppler_path(
            cli_arg=args.poppler_path,
            env_var_name="POPLER_BIN"
        )

        # Parse PDF
        logger.info(f"Parsing PDF: {args.pdf_path}")
        result = parse_pdf(args.pdf_path, poppler_path=poppler_path)

        # Display results
        print(f"\n{'='*60}")
        print(f"PDF Parsing Results")
        print(f"{'='*60}")
        print(f"File: {args.pdf_path}")
        print(f"Method: {result['method']}")
        print(f"Pages: {result['pages']}")
        print(f"Success: {result['success']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"{'='*60}")

        if args.show_text:
            print(f"\nExtracted Text:\n{result['text'][:1000]}")
            if len(result['text']) > 1000:
                print(f"\n... (truncated, {len(result['text']) - 1000} more characters)")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}", exc_info=True)
        return 1


def cmd_print_summary(args: argparse.Namespace) -> int:
    """
    Print summary of existing output files.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = logging.getLogger(__name__)

    try:
        from congress_audit.io_utils import safe_read_json, file_exists

        output_dir = args.output_dir or "congress_trades_output"

        # Check for output files
        files = {
            'transactions': f"{output_dir}/transactions_last_120_days.json",
            'performance': f"{output_dir}/official_lifetime_performance.json",
            'compliance': f"{output_dir}/compliance_summary.json",
        }

        print(f"\n{'='*60}")
        print(f"Congress Trading Audit Summary")
        print(f"{'='*60}")
        print(f"Output directory: {output_dir}")
        print(f"{'='*60}\n")

        for name, filepath in files.items():
            if file_exists(filepath):
                try:
                    data = safe_read_json(filepath)
                    print(f"{name.upper()}: {filepath}")

                    if name == 'transactions':
                        print(f"  - Total transactions: {len(data)}")
                    elif name == 'performance':
                        print(f"  - Tickers tracked: {len(data)}")
                    elif name == 'compliance':
                        print(f"  - Total trades: {data.get('total_trades', 0)}")
                        print(f"  - Late filings: {data.get('late_filings', 0)}")
                        print(f"  - Average confidence: {data.get('average_confidence', 0):.2f}")

                    print()
                except Exception as e:
                    logger.warning(f"Could not read {filepath}: {e}")
            else:
                print(f"{name.upper()}: NOT FOUND")
                print(f"  Expected at: {filepath}\n")

        return 0

    except Exception as e:
        logger.error(f"Failed to print summary: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Congress Trading Audit Tool - Analyze congressional trading disclosures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full audit with sample data
  %(prog)s run

  # Run audit with custom Poppler path
  %(prog)s run --poppler-path /usr/local/bin

  # Parse a single PDF
  %(prog)s parse-pdf path/to/disclosure.pdf

  # Print summary of existing results
  %(prog)s print-summary
        """
    )

    # Global arguments
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )

    parser.add_argument(
        '--poppler-path',
        type=str,
        help='Path to Poppler binaries directory (overrides POPLER_BIN env var)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run command
    run_parser = subparsers.add_parser(
        'run',
        help='Run the full audit workflow'
    )
    run_parser.add_argument(
        '--source-url',
        type=str,
        help='URL to fetch congressional trading data from'
    )
    run_parser.add_argument(
        '--pdf-files',
        nargs='+',
        type=str,
        help='List of PDF files to parse'
    )
    run_parser.add_argument(
        '--output-dir',
        type=str,
        default='congress_trades_output',
        help='Output directory (default: congress_trades_output)'
    )

    # Parse PDF command
    parse_parser = subparsers.add_parser(
        'parse-pdf',
        help='Parse a single PDF file'
    )
    parse_parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to PDF file to parse'
    )
    parse_parser.add_argument(
        '--show-text',
        action='store_true',
        help='Display extracted text (first 1000 chars)'
    )

    # Print summary command
    summary_parser = subparsers.add_parser(
        'print-summary',
        help='Print summary of existing output files'
    )
    summary_parser.add_argument(
        '--output-dir',
        type=str,
        default='congress_trades_output',
        help='Output directory to read from (default: congress_trades_output)'
    )

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Execute command
    if args.command == 'run':
        return cmd_run(args)
    elif args.command == 'parse-pdf':
        return cmd_parse_pdf(args)
    elif args.command == 'print-summary':
        return cmd_print_summary(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
