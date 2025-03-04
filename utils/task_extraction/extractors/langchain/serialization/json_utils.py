"""Utilities for JSON serialization"""

import json
import logging
from typing import Any
from datetime import datetime, date
from pathlib import Path

def is_json_serializable(obj: Any) -> bool:
    """Check if an object is JSON serializable"""
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False

def clean_for_serialization(obj: Any) -> Any:
    """
    Recursively clean an object for JSON serialization.
    Handles common types and skips non-serializable fields.
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, date, Path)):
        return str(obj)
    elif isinstance(obj, dict):
        cleaned_dict = {}
        for k, v in obj.items():
            if is_json_serializable(v) or isinstance(v, (dict, list, datetime, date, Path)):
                cleaned_dict[k] = clean_for_serialization(v)
            else:
                logging.debug(f"Skipping non-serializable value in dict key '{k}' of type: {type(v).__name__}")
        return cleaned_dict
    elif isinstance(obj, (list, tuple)):
        cleaned_list = []
        for i, item in enumerate(obj):
            if is_json_serializable(item) or isinstance(item, (dict, list, datetime, date, Path)):
                cleaned_list.append(clean_for_serialization(item))
            else:
                logging.debug(f"Skipping non-serializable value at index {i} of type: {type(item).__name__}")
        return cleaned_list
    else:
        # Log the type of non-serializable object
        logging.debug(f"Skipping non-serializable object of type: {type(obj).__name__}")
        return None
