"""
IO utilities for safe file operations and JSON handling.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def ensure_directory(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")


def safe_write_json(data: Any, filepath: str) -> None:
    """
    Safely write data to a JSON file with proper error handling.

    Args:
        data: Data to write (must be JSON serializable)
        filepath: Path to output JSON file

    Raises:
        IOError: If file cannot be written
        TypeError: If data is not JSON serializable
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            ensure_directory(parent_dir)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully wrote JSON to {filepath}")

    except TypeError as e:
        logger.error(f"Data is not JSON serializable: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to write file {filepath}: {e}")
        raise


def safe_read_json(filepath: str) -> Any:
    """
    Safely read JSON data from a file.

    Args:
        filepath: Path to JSON file to read

    Returns:
        Parsed JSON data

    Raises:
        IOError: If file cannot be read
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully read JSON from {filepath}")
        return data
    except IOError as e:
        logger.error(f"Failed to read file {filepath}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise


def file_exists(filepath: str) -> bool:
    """
    Check if a file exists and is a file (not a directory).

    Args:
        filepath: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return os.path.isfile(filepath)
