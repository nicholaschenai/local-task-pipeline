"""Context serialization utilities"""

import json
import logging
from typing import Dict

from .json_utils import clean_for_serialization

def serialize_context(context: Dict) -> str:
    """
    Safely serialize context dictionary to JSON string,
    skipping non-serializable fields while keeping serializable ones
    
    Args:
        context: Dictionary of context information
        
    Returns:
        JSON string representation of serializable context
    """
    if not context:
        return "No additional context provided"
        
    try:
        # Clean the context dictionary
        clean_context = clean_for_serialization(context)
        if not clean_context:
            return "No serializable context available"
            
        # Log any skipped keys
        skipped_keys = set(context.keys()) - set(clean_context.keys())
        if skipped_keys:
            logging.warning(f"Skipped non-serializable context keys: {skipped_keys}")
            
        return json.dumps(clean_context, indent=4)
        
    except Exception as e:
        logging.error(f"Unexpected error during context serialization: {str(e)}")
        return "Error processing context" 