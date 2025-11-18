#!/usr/bin/env python3
"""
Congress Trades Audit - Legacy Entry Point

This is a backwards-compatible shim that calls the refactored congress_audit package.
For new code, use run_audit.py or import from congress_audit directly.
"""

import sys
from congress_audit.cli import main

if __name__ == "__main__":
    sys.exit(main())
