"""
Congress Trading Audit Package

A package for analyzing congressional trading data, parsing disclosure PDFs,
and computing performance metrics with compliance checks.
"""

__version__ = "1.0.0"
__author__ = "Congress Audit Team"
__description__ = "Congress trading data analysis and audit tool"

# Expose main CLI entry point
from congress_audit.cli import main

__all__ = ["main", "__version__"]
