"""
This is a one-off script that:

1. Scans a folder of markdown files
2. Extracts research tasks using LLM
3. Saves tasks to a database

Uses components from utils.task_extraction for reusability

structure in a way so that
- these tasks can then be read, implemented by a service, and updated back to the db
"""

# Standard library imports
from pathlib import Path
import logging
from datetime import datetime
import os
import argparse

# Third-party imports
from config import LOG_DIR

# Local imports
from input_layer.md_file_interface import MdFileInterface
from utils.task_extraction.extractors.langchain import LangchainTaskExtractor
from utils.task_extraction.repositories.kanban import KanbanTaskRepository
from utils.task_extraction.models import TaskRepository

from config.local_config import TASK_DB_URL, MARKDOWN_DIR, LC_MODEL_NAME, KANBAN_KEY, GROQ_API_KEY

def truncate_str(s, max_length=300):
    """
    Truncate a string to a maximum length, appending '...' if truncated.

    Parameters:
    s (str): The string to be truncated.
    max_length (int, optional): The maximum length of the truncated string including the ellipsis. Defaults to 300.

    Returns:
    str: The truncated string with '...' appended if it exceeds the maximum length.
    """
    if len(s) > max_length:
        return s[:max_length - 3] + '...'
    return s

def setup_argparse():
    """Configure command line arguments"""
    parser = argparse.ArgumentParser(description="Extract tasks from markdown files")
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='Run without writing to database (for testing/debugging)'
    )
    parser.add_argument(
        '--repository',
        choices=['kanban', 'sql'],
        default='kanban',
        help='Choose repository type (default: kanban)'
    )
    parser.add_argument(
        '--llm',
        choices=['groq', 'ollama'],
        default='groq',
        help='Choose LLM provider (default: groq)'
    )
    return parser

def setup_logging():
    """Configure logging for the script with file output"""
    # Create log directory if it doesn't exist
    LOG_DIR.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file = LOG_DIR / f"task_extraction_{timestamp}.log"
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # File handler with DEBUG level
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler with INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add both handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Logging to {log_file}")
    logging.debug("Debug logging enabled for file output")

def scan_files(directory: Path):
    """Scan directory for markdown files"""
    md_interface = MdFileInterface(directory)
    return md_interface.scan_markdown_files()

def log_extracted_tasks(tasks: list, file_path: str):
    """
    Log task preview with safe Unicode handling
    """
    try:
        logging.info(f"\nExtracted {len(tasks)} research tasks from {file_path}:")
        
        for i, task in enumerate(tasks, 1):
            logging.info(f"\nTask {i}:")
            # Safely encode each field for logging
            title_preview = truncate_str(task['title'], 100)
            desc_preview = truncate_str(task['description'], 100)
            queries_preview = truncate_str(task.get('web_search_queries', ''), 100)
            
            # Convert to ASCII with escaped Unicode
            log_title = title_preview.encode('ascii', 'backslashreplace').decode('ascii')
            log_desc = desc_preview.encode('ascii', 'backslashreplace').decode('ascii')
            log_queries = queries_preview.encode('ascii', 'backslashreplace').decode('ascii')
            
            logging.info(f"Original Quote: {log_title}")
            logging.info(f"Research Question: {log_desc}")
            logging.info(f"Web Search Queries: {log_queries}\n")
    except Exception as e:
        logging.error(f"Error logging task preview: {str(e)}")

def handle_success(tasks: list, file_path: str, task_repo: TaskRepository, last_modified: datetime):
    # Log task preview with safe Unicode handling
    log_extracted_tasks(tasks, file_path)

    # Save tasks and update processing time
    task_repo.save_tasks(tasks, file_path, last_modified)

def handle_no_tasks(file_path: str, task_repo: TaskRepository, last_modified: datetime):
    logging.info(f"No research tasks found in {file_path}")
    # Record that we processed this file even though no tasks were found
    task_repo.update_file_processing_time(file_path, last_modified)

def process_markdown_files(files: list, task_extractor: LangchainTaskExtractor, task_repo: TaskRepository):
    """Process markdown files and extract research tasks"""
    for file_data in files:
        file_metadata = file_data['file_metadata']
        file_path = file_metadata['file_path']
        
        # Check if file needs processing
        last_processed_time = task_repo.get_last_processed_time(file_path)
        last_modified = file_metadata['last_modified']
        if last_processed_time and last_processed_time >= last_modified:
            logging.info(f"Skipping {file_path} - no changes since last processing")
            continue

        yaml_metadata = file_data['yaml_metadata']
        # Combine metadata for context
        context = {
            **file_metadata,  # File-related metadata
            **yaml_metadata,  # Original YAML frontmatter
        }

        content = file_data['content']
        tasks = task_extractor.extract_tasks(content, context=context)
        
        if tasks:
            handle_success(tasks, file_path, task_repo, last_modified)
        elif tasks is not None:
            handle_no_tasks(file_path, task_repo, last_modified)
        else:
            logging.error(f"Encounted error somewhere in {file_path}")

def create_repository(repo_type: str, session=None, dry_run: bool = False) -> TaskRepository:
    """Factory function to create the appropriate repository"""
    if repo_type == 'sql':
        if session is None:
            raise ValueError("Session is required for SQL repository")
        return SQLTaskRepository(session, dry_run=dry_run)
    else:  # kanban
        return KanbanTaskRepository(
            api_url=TASK_DB_URL,
            api_key=KANBAN_KEY,
            dry_run=dry_run
        )

def create_llm(llm_type: str):
    """Factory function to create the appropriate LLM"""
    if llm_type == 'ollama':
        logging.info(f"Using Ollama model: {LC_MODEL_NAME}")
        from langchain_ollama.chat_models import ChatOllama
        return ChatOllama(
            model=LC_MODEL_NAME,
            temperature=0.0,
        )
    else:  # groq
        from langchain_groq import ChatGroq
        logging.info(f"Using Groq model: {LC_MODEL_NAME}")
        return ChatGroq(
            temperature=0.0,
            api_key=GROQ_API_KEY,
            model_name=LC_MODEL_NAME
        )

def main():
    """
    Main orchestration function:
    1. Setup logging
    2. Initialize components
    3. Scan for markdown files
    4. Process each file:
        - Check if file needs processing
        - Extract research tasks if needed
        - Save to database
    5. Handle errors and cleanup
    """
    # Parse command line arguments
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Log dry run mode if enabled
    if args.dry_run:
        logging.info("Running in DRY RUN mode - no database changes will be made")
    
    try:        
        # Initialize LLM based on selected provider
        llm = create_llm(args.llm)
        task_extractor = LangchainTaskExtractor.create_research_extractor(llm)
        
        # Initialize repository based on type
        if args.repository == 'sql':
            # Initialize database
            from sqlalchemy import create_engine
            from sqlalchemy.orm import Session
            engine = create_engine(TASK_DB_URL)
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                task_repo = create_repository('sql', session=session, dry_run=args.dry_run)
                # Scan and process files
                files = scan_files(MARKDOWN_DIR)
                process_markdown_files(files, task_extractor, task_repo)
        else:  # kanban
            task_repo = create_repository('kanban', dry_run=args.dry_run)
            # Scan and process files
            files = scan_files(MARKDOWN_DIR)
            process_markdown_files(files, task_extractor, task_repo)
            
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
