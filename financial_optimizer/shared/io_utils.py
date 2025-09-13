"""
File I/O utility functions for import/export of various data formats.
"""
from typing import Dict, Any, List, Optional
import json
import csv
import os

def save_json(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data to a JSON file.
    Returns True if successful, False otherwise.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    Returns the data if successful, None otherwise.
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return None