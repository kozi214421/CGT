#!/usr/bin/env python3
"""
Congressional Trading Audit System - Main Entry Point

This is the recommended entry point for running the audit system.
"""

import sys
from congress_audit.cli import main

if __name__ == "__main__":
    sys.exit(main())
