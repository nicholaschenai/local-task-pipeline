"""
This script executes confirmed tasks by:
1. Scanning for confirmed tasks via Kanban API
2. Using the ResearchService to get research results
3. Organizing the results (using ai_overview)
4. Updating the tasks with the results via Kanban API
"""

import logging
from datetime import datetime
from services.research_service import ResearchService
from utils.task_extraction.repositories.kanban import KanbanTaskRepository
from config.local_config import TASK_DB_URL, KANBAN_KEY, JIGSAW_KEY
from .task_extraction import setup_logging

def main():
    """
    Main orchestration function:
    1. Setup logging
    2. Initialize components
    3. Scan for confirmed tasks
    4. Execute research tasks
    5. Update tasks with results
    """
    # Set up logging
    setup_logging()
    
    try:
        # Initialize Kanban repository and ResearchService
        task_repo = KanbanTaskRepository(api_url=TASK_DB_URL, api_key=KANBAN_KEY)
        research_service = ResearchService(api_key=JIGSAW_KEY)
        
        # Scan for confirmed tasks
        # add the bucket_id params if different from default!
        confirmed_tasks = task_repo.get_confirmed_tasks()
        
        for task in confirmed_tasks:
            task_id = task['id']
            description = task['description']
            
            # Execute research task
            research_result = research_service.execute(description)
            
            # Check if the API call was successful
            if not research_result.get('success'):
                raise Exception(f"Research API call failed for task {task_id}")
            
            # Get research overview or fallback to first result description
            overview = research_result.get('ai_overview')
            if not overview:
                # Fallback to first result's description if available
                if research_result.get('results') and len(research_result['results']) > 0:
                    overview = research_result['results'][0].get('content', 'No results found')
                else:
                    overview = 'No results or overview available'
            
            # Update task with results
            # add the done_bucket_id param if different from default!
            task_repo.update_task_with_results(task_id, overview)
            
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
