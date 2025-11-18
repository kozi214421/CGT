"""
Command-line interface for the congressional trading audit system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .core import run_audit, validate_environment

logger = logging.getLogger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Congressional Trading Audit System - Analyze congressional stock trades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pdf trade_report.pdf
  %(prog)s --pdf report1.pdf report2.pdf --output results/
  %(prog)s --pdf trades.pdf --poppler-path /usr/local/bin --ocr
  %(prog)s --validate
        """
    )
    
    parser.add_argument(
        '--pdf',
        nargs='+',
        metavar='FILE',
        help='PDF file(s) to process'
    )
    
    parser.add_argument(
        '--poppler-path',
        metavar='PATH',
        help='Path to Poppler binaries (overrides POPPLER_BIN env var)'
    )
    
    parser.add_argument(
        '--output',
        metavar='DIR',
        default='congress_trades_output',
        help='Output directory for results (default: congress_trades_output)'
    )
    
    parser.add_argument(
        '--ocr',
        action='store_true',
        help='Use OCR for scanned documents'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate environment and dependencies'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parsed_args = parse_args(args)
    
    try:
        # Handle validation mode
        if parsed_args.validate:
            print("Validating environment...")
            validation = validate_environment()
            
            print("\n" + "=" * 50)
            print("Environment Validation Results")
            print("=" * 50)
            print(f"Python Version: {validation['python_version'].split()[0]}")
            print(f"\nPoppler Available: {'Yes' if validation['poppler_available'] else 'No'}")
            if validation['poppler_path']:
                print(f"Poppler Path: {validation['poppler_path']}")
            
            print("\nDependencies:")
            for dep, status in validation['dependencies'].items():
                status_mark = "✓" if status == "available" else "✗"
                print(f"  {status_mark} {dep}: {status}")
            
            all_deps_available = all(s == "available" for s in validation['dependencies'].values())
            if validation['poppler_available'] and all_deps_available:
                print("\n✓ Environment is properly configured")
                return 0
            else:
                print("\n✗ Some components are missing - install required dependencies")
                return 1
        
        # Validate PDF files if provided
        pdf_paths = None
        if parsed_args.pdf:
            pdf_paths = []
            for pdf_file in parsed_args.pdf:
                path = Path(pdf_file)
                if not path.exists():
                    print(f"Error: PDF file not found: {pdf_file}", file=sys.stderr)
                    return 1
                pdf_paths.append(str(path.absolute()))
        
        # Run the audit
        results = run_audit(
            pdf_paths=pdf_paths,
            poppler_path=parsed_args.poppler_path,
            output_dir=parsed_args.output,
            use_ocr=parsed_args.ocr,
            verbose=parsed_args.verbose
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
