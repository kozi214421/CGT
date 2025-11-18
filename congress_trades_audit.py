#!/usr/bin/env python3
"""
Congress Trading Audit - Legacy entry point.

This file maintains backwards compatibility with the original script name.
It's a thin shim that delegates to the new package structure.

For new usage, prefer using: python run_audit.py
"""
import sys
import logging

# Import from new package structure
from congress_audit.cli import main

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Note: This is the legacy entry point for backwards compatibility
    logger.info("Running via legacy script name (congress_trades_audit.py)")
    logger.info("Consider using: python run_audit.py or congress_audit CLI")
    sys.exit(main())
