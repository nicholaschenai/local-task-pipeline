"""
new task repository that sends to kanban
"""

import logging
from datetime import datetime
from typing import Optional, List
import requests
from ..models import TaskRepository, TaskData

class KanbanTaskRepository(TaskRepository):
    """Kanban API implementation of task repository"""
    
    def __init__(self, api_url: str, api_key: str, project_id: int = 1, dry_run: bool = False):
        """
        Initialize repository
        
        Args:
            api_url: Base URL for the Kanban API
            api_key: JWT API key for authentication
            project_id: ID of the project to add tasks to
            dry_run: If True, no API calls will be made
        """
        self.api_url = api_url
        self.project_id = project_id
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.dry_run = dry_run
        
    def get_last_processed_time(self, file_path: str) -> Optional[datetime]:
        """
        Get the last modification time of file when it was last processed.
        For Kanban implementation, we don't track this so return None.
        """
        return None
        
    def update_file_processing_time(self, file_path: str, modified_time: datetime):
        """
        Update the processing time for a file.
        For Kanban implementation, this is a no-op since we don't track file processing.
        """
        pass
        
    def save_tasks(self, tasks: List[TaskData], source_file: str, modified_time: datetime):
        """Send tasks to Kanban API"""
        if self.dry_run:
            logging.info(f"[DRY RUN] Would send {len(tasks)} tasks to Kanban API from: {source_file}")
            return
            
        endpoint = f"{self.api_url}/api/v1/projects/{self.project_id}/tasks"
        
        try:
            for task_data in tasks:
                # Convert task data to Kanban API format
                kanban_task = {
                    'title': task_data['title'],
                    'description': task_data['description'],
                    # Set basic required fields, leaving optional ones empty
                    # 'project_id': self.project_id,
                    'done': False
                }
                
                # Send to Kanban API
                response = requests.put(
                    endpoint,
                    headers=self.headers,
                    json=kanban_task
                )
                response.raise_for_status()
                
                logging.info(f"Successfully created Kanban task: {task_data['title']}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending tasks to Kanban API: {str(e)}")
            raise

    def get_confirmed_tasks(self, view_id: int = 4, bucket_id: int = 4) -> List[dict]:
        """
        Get tasks from a specific view (default: view 4 for confirmed tasks)
        Returns list of tasks that need to be executed
        """
        endpoint = f"{self.api_url}/api/v1/projects/{self.project_id}/views/{view_id}/tasks"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers
            )
            response.raise_for_status()
            buckets = response.json()
            
            # Filter for tasks in bucket
            for bucket in buckets:
                if bucket.get('id') == bucket_id:
                    return bucket.get('tasks', [])
            return []
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting confirmed tasks: {str(e)}")
            raise

    def update_task_with_results(self, task_id: int, results: str, done_bucket_id: int = 5) -> dict:
        """
        Update task with execution results and mark as done
        Moves to the done bucket and appends results to description
        
        Returns:
            dict: The updated task data
        """
        endpoint = f"{self.api_url}/api/v1/tasks/{task_id}"
        
        try:
            # First get existing task to preserve its current description
            response = requests.get(
                endpoint,
                headers=self.headers
            )
            response.raise_for_status()
            current_task = response.json()
            
            # Prepare updated task data
            updated_task = {
                'description': f"{current_task['description']}\n\nExecution Results:\n{results}",
                'bucket_id': done_bucket_id,
                'done': True
            }
            
            # Update the task
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=updated_task
            )
            response.raise_for_status()
            updated_task_data = response.json()
            logging.info(f"Successfully updated task {task_id} with results")
            
            return updated_task_data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error updating task with results: {str(e)}")
            raise
