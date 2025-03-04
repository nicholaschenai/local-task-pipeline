"""Base interface for task parsers"""

from abc import ABC, abstractmethod
from typing import List
from ....models import TaskData

class TaskParser(ABC):
    """Base interface for parsing LLM responses into tasks"""
    
    @abstractmethod
    def parse(self, response: str) -> List[TaskData]:
        """
        Parse LLM response into a list of tasks
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            List of parsed TaskData objects
        """
        pass 