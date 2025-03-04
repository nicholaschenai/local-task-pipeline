"""Task extraction models and types"""

from typing import Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

# Type definitions
TaskData = Dict[str, any]

class TaskRepository(ABC):
    """Abstract base class for task storage"""
    
    @abstractmethod
    def get_last_processed_time(self, file_path: str) -> Optional[datetime]:
        """Get the last time a file was processed for tasks"""
        pass
        
    @abstractmethod
    def save_tasks(self, tasks: List[TaskData], source_file: str, modified_time: datetime):
        """Save tasks to storage"""
        pass 