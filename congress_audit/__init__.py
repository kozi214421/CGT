"""
Congress Audit Package

A robust, testable package for auditing congressional trading activities.
Processes PDF documents, extracts trading data, and calculates performance metrics.
"""

__version__ = "1.0.0"

from .core import run_audit
from .cli import main as cli_main

__all__ = ["run_audit", "cli_main"]
