"""
I/O utilities for reading and writing audit data.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def ensure_output_directory(output_dir: str = "congress_trades_output") -> Path:
    """
    Ensure the output directory exists.
    
    Args:
        output_dir: Path to output directory
        
    Returns:
        Path object for the directory
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Output directory ensured: {path}")
    return path


def write_json(data: Any, filename: str, output_dir: str = "congress_trades_output") -> str:
    """
    Write data to a JSON file in the output directory.
    
    Args:
        data: Data to write
        filename: Name of the file
        output_dir: Output directory path
        
    Returns:
        Full path to the written file
    """
    output_path = ensure_output_directory(output_dir)
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Written JSON to: {filepath}")
    return str(filepath)


def write_csv(data: List[Dict[str, Any]], filename: str, output_dir: str = "congress_trades_output") -> str:
    """
    Write data to a CSV file in the output directory.
    
    Args:
        data: List of dictionaries to write
        filename: Name of the file
        output_dir: Output directory path
        
    Returns:
        Full path to the written file
    """
    import csv
    
    output_path = ensure_output_directory(output_dir)
    filepath = output_path / filename
    
    if not data:
        logger.warning(f"No data to write to {filename}")
        return str(filepath)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Written CSV to: {filepath}")
    return str(filepath)


def read_json(filepath: str) -> Any:
    """
    Read data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.debug(f"Read JSON from: {filepath}")
    return data
