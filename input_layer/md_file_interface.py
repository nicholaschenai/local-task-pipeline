import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path
import logging
import yaml

from input_layer.base_input import BaseInput

def parse_md_with_frontmatter(markdown_content):
    """
    Parses a markdown string to separate YAML frontmatter and the markdown content.

    Args:
        markdown_content (str): The markdown content as a string.

    Returns:
        tuple: A tuple containing a dictionary of metadata and the markdown content without frontmatter.
    """
    metadata = {}

    if markdown_content.startswith('---'):
        # Split the content by '---',  ensures that it only splits at the first two occurrences
        parts = markdown_content.split('---', 2)

        if len(parts) >= 3:
            # Extract the frontmatter and the markdown content
            frontmatter = parts[1].strip()
            markdown_content = parts[2].strip()

            # Parse the frontmatter as YAML
            metadata = yaml.safe_load(frontmatter)

    # If no frontmatter is detected, return empty metadata and the original content
    return metadata, markdown_content


class MdFileInterface(BaseInput):
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def scan_markdown_files(self) -> List[Dict]:
        """
        Base method to scan and parse all markdown files in the folder.
        Returns a list of dictionaries containing file metadata, yaml metadata, and content.
        
        Returns:
            List[Dict]: List of dictionaries with keys:
                - file_metadata: Dict containing:
                    - file_path: Full path to the file
                    - root: Root directory
                    - relative_path: Path relative to folder_path
                    - task_id: File name without extension
                    - last_modified: Datetime of last modification
                - yaml_metadata: Dict of frontmatter metadata
                - content: Markdown content
        """
        markdown_files = []
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".md"):
                    file_path = Path(os.path.join(root, file))
                    relative_path = os.path.relpath(file_path, self.folder_path)
                    # Get last modified time
                    last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    try:
                        # Use utf-8-sig to handle BOM if present
                        with open(file_path, "r", encoding="utf-8-sig", errors='replace') as f:
                            content = f.read()
                    except Exception as e:
                        logging.error(f"Error loading {file_path}: {str(e)}")
                        raise
                    
                    yaml_metadata, markdown_content = parse_md_with_frontmatter(content)
                    if yaml_metadata is None:
                        yaml_metadata = {}
                    
                    file_metadata = {
                        'file_path': str(file_path),
                        'root': root,
                        'relative_path': relative_path,
                        'task_id': os.path.splitext(file)[0],
                        'last_modified': last_modified
                    }
                    
                    file_data = {
                        'file_metadata': file_metadata,
                        'yaml_metadata': yaml_metadata,
                        'content': markdown_content
                    }
                    markdown_files.append(file_data)
        
        return markdown_files

    def fetch_tasks(self) -> List[Dict]:
        """
        Original method that filters for tasks marked for sending and not completed.
        Returns only markdown files that match specific metadata criteria.
        Combines metadata and content into a single dictionary.
        """
        all_files = self.scan_markdown_files()
        filtered_files = []
        
        for file_data in all_files:
            yaml_metadata = file_data['yaml_metadata']
            if yaml_metadata.get("send", False) and not yaml_metadata.get("completed", False):
                # Combine metadata and content for backward compatibility
                combined_data = {
                    **file_data['file_metadata'],  # File metadata
                    **file_data['yaml_metadata'],  # Original YAML metadata
                    'content': file_data['content']  # Content
                }
                filtered_files.append(combined_data)
        
        return filtered_files

    def filter_markdown_files(self, filter_func: callable) -> List[Dict]:
        """
        Generic filter method that takes a custom filter function.
        
        Args:
            filter_func: Callable that takes file_data dict and returns boolean
            
        Returns:
            List[Dict]: Filtered list of markdown file data
        """
        all_files = self.scan_markdown_files()
        return [
            file_data for file_data in all_files
            if filter_func(file_data)
        ]
