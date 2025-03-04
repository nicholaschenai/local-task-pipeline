"""Research task parser implementation"""

import json
import logging
import re
from typing import List

from .base import TaskParser
from ....models import TaskData

def extract_blocks(text, identifier='', concat=True):
    """
    Extracts code blocks from the given text using the specified identifier.

    Parameters:
        text (str): The text from which to extract code blocks.
        identifier (str): An optional identifier to specify the type of code blocks to extract.

    Returns:
        str: A string containing all extracted code blocks, concatenated and separated by newlines.
    """
    # Escape the identifier to avoid regex injection issues
    # (note: regex injection is only if identifier is supplied by external users)
    # identifier = re.escape(identifier)

    # Create the regex pattern dynamically
    if identifier:
        pattern = re.compile(rf"```(?:{identifier})(.*?)```", re.DOTALL)
    else:
        pattern = re.compile(r"```(.*?)```", re.DOTALL)

    pattern_list = pattern.findall(text)
    if concat:
        return "\n".join(pattern_list)
    return pattern_list

def clean_json_string(json_str: str) -> str:
    """
    Clean JSON string to handle common formatting issues:
    - Remove trailing commas
    - Fix unquoted property names
    - Remove any extra whitespace
    - Handle Unicode escapes
    """
    # Handle Unicode escapes first
    try:
        # Try to normalize Unicode escapes
        json_str = json_str.encode('utf-8').decode('unicode-escape')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # If that fails, keep original string
        pass
    
    # Remove trailing commas in objects and arrays
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Fix unquoted property names (if any)
    json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
    
    return json_str.strip()


class ResearchTaskParser(TaskParser):
    """Parser for research-focused task format"""
    
    def parse(self, response: str) -> List[TaskData]:
        """
        Parse research task format from LLM response
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            List of parsed TaskData objects
        """
        try:
            # Extract JSON from code block if present
            json_str = extract_blocks(response, identifier="json")
            
            # Parse JSON
            if not json_str:
                logging.info("No JSON code block found, assume no tasks")
                return []
            
            # Log raw JSON with safe encoding
            try:
                log_str = json_str.encode('ascii', 'backslashreplace').decode('ascii')
                logging.debug(f"Raw JSON string (with escaped unicode): {log_str}")
            except Exception as e:
                logging.debug("Could not log raw JSON due to encoding issues")
            
            # Clean the JSON string before parsing
            cleaned_json = clean_json_string(json_str)
            
            # Log cleaned JSON with safe encoding
            try:
                log_str = cleaned_json.encode('ascii', 'backslashreplace').decode('ascii')
                logging.debug(f"Cleaned JSON string (with escaped unicode): {log_str}")
            except Exception as e:
                logging.debug("Could not log cleaned JSON due to encoding issues")
            
            # Parse with explicit encoding handling
            tasks = json.loads(cleaned_json, strict=False)
            if not isinstance(tasks, list):
                logging.error("Research task response is not a list")
                return None
                
            # Validate and add default fields
            validated_tasks = []
            required_fields = ["title", "description"]
            
            for task in tasks:
                if all(field in task for field in required_fields):
                    # Add default fields required by the database schema
                    task["priority"] = ""
                    task["estimated_effort"] = ""
                    validated_tasks.append(task)
                else:
                    # Log invalid task safely
                    try:
                        log_task = str(task).encode('ascii', 'backslashreplace').decode('ascii')
                        logging.warning(f"Skipping invalid research task: {log_task}")
                    except:
                        logging.warning("Skipping invalid research task (could not log details)")
            
            return validated_tasks
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse research task response as JSON: {str(e)}")
            try:
                log_str = json_str.encode('ascii', 'backslashreplace').decode('ascii')
                logging.debug(f"JSON string that failed to parse (with escaped unicode): {log_str}")
            except:
                logging.debug("Could not log failed JSON string due to encoding issues")
            return None
        except Exception as e:
            logging.error(f"Unexpected error parsing research tasks: {str(e)}")
            return None
