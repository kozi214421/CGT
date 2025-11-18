#!/usr/bin/env python3
"""
Main entrypoint for congress trading audit tool.

This script serves as the primary entry point for the application.
"""
import sys
from congress_audit.cli import main

if __name__ == '__main__':
    sys.exit(main())
