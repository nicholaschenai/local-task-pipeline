"""Base interface for task extractors"""

from abc import ABC, abstractmethod
from typing import Dict, List

from ..models import TaskData

class TaskExtractor(ABC):
    """Abstract base class for task extractors"""
    
    @abstractmethod
    def extract_tasks(self, content: str, context: Dict = None) -> List[TaskData]:
        """
        Extract tasks from content
        
        Args:
            content: Text content to extract tasks from
            context: Optional metadata/context about the content
            
        Returns:
            List of extracted tasks
        """
        pass 