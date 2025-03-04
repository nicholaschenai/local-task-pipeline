"""Default task parser implementation"""

import json
import logging
from typing import List

from .base import TaskParser
from ....models import TaskData

class DefaultTaskParser(TaskParser):
    """Default parser for standard task format"""
    
    def parse(self, response: str) -> List[TaskData]:
        """
        Parse standard task format from LLM response
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            List of parsed TaskData objects
        """
        try:
            parsed = json.loads(response)
            tasks = parsed.get("tasks", [])
            
            if not isinstance(tasks, list):
                logging.error("LLM response tasks is not a list")
                return []
                
            # Validate each task has required fields
            validated_tasks = []
            required_fields = ["title", "description", "priority", "estimated_effort"]
            
            for task in tasks:
                if all(field in task for field in required_fields):
                    validated_tasks.append(task)
                else:
                    logging.warning(f"Skipping invalid task: {task}")
            
            return validated_tasks
            
        except json.JSONDecodeError:
            logging.error("Failed to parse LLM response as JSON")
            return [] 