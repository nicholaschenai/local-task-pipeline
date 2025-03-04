from config.local_config import TASK_DB_URL, KANBAN_KEY
import requests
import json
from utils.task_extraction.repositories.kanban import KanbanTaskRepository

def test_kanban_api():
    # Setup headers with Bearer token
    headers = {
        'Authorization': f'Bearer {KANBAN_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: List projects
    print("\n=== Testing Projects Endpoint ===")
    projects_url = f"{TASK_DB_URL}/api/v1/projects"
    try:
        response = requests.get(projects_url, headers=headers)
        response.raise_for_status()
        projects = response.json()
        print("Projects response:")
        print(json.dumps(projects, indent=2))

        # List all tasks in project
        print("\n=== Testing Project Tasks ===")
        project_id = 1
        tasks_url = f"{TASK_DB_URL}/api/v1/projects/{project_id}/tasks"
        response = requests.get(tasks_url, headers=headers)
        response.raise_for_status()
        tasks = response.json()
        print(f"\nAll tasks in project {project_id}:")
        print(json.dumps(tasks, indent=2))

        # List tasks in view 4
        print("\n=== Testing View Tasks ===")
        view_id = 4
        view_tasks_url = f"{TASK_DB_URL}/api/v1/projects/{project_id}/views/{view_id}/tasks"
        response = requests.get(view_tasks_url, headers=headers)
        response.raise_for_status()
        view_tasks = response.json()
        print(f"\nTasks in view {view_id}:")
        print(json.dumps(view_tasks, indent=2))

        # List buckets in view
        print("\n=== Testing View Buckets ===")
        view_id = 4
        buckets_url = f"{TASK_DB_URL}/api/v1/projects/{project_id}/views/{view_id}/buckets"
        response = requests.get(buckets_url, headers=headers)
        response.raise_for_status()
        buckets = response.json()
        print(f"\nBuckets in view {view_id}:")
        print(json.dumps(buckets, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error getting projects: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")
        return

    if not projects:
        return

    # project_id = projects[0]['id']
    project_id = 1
    
    # Initialize Kanban repository
    kanban_repo = KanbanTaskRepository(TASK_DB_URL, KANBAN_KEY, project_id)

    # Test 2: Create a test task in bucket 1
    print("\n=== Testing Task Creation ===")
    tasks_url = f"{TASK_DB_URL}/api/v1/projects/{project_id}/tasks"
    
    test_task = {
        'title': 'Test Task for Execution',
        'description': 'This is a test task that needs to be executed',
        'bucket_id': 4,
        'done': False
    }
    
    try:
        response = requests.put(
            tasks_url,
            headers=headers,
            json=test_task
        )
        response.raise_for_status()
        created_task = response.json()
        print("Created task:")
        print(json.dumps(created_task, indent=2))
        
        # Pause for manual verification
        input("\nPress Enter to continue after verifying the task in Kanban board...")
        
        # Test 3: Get confirmed tasks using repository
        print("\n=== Testing Get Confirmed Tasks ===")
        confirmed_tasks = kanban_repo.get_confirmed_tasks()
        print(f"Found {len(confirmed_tasks)} confirmed tasks:")
        print(json.dumps(confirmed_tasks, indent=2))
        
        # Test 4: Update task with results using repository
        if confirmed_tasks:
            print("\n=== Testing Task Update with Results ===")
            task_id = created_task['id']
            
            # Simulate execution results
            execution_results = "Task executed successfully at 2024-03-14 15:30:00\nOutput: All tests passed"
            
            updated_task = kanban_repo.update_task_with_results(task_id, execution_results)
            print("Updated task with results:")
            print(json.dumps(updated_task, indent=2))
            
    except requests.exceptions.RequestException as e:
        print(f"Error in task operations: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    test_kanban_api()
