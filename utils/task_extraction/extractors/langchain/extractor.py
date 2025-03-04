"""Langchain-based task extractor implementation"""

import logging
from typing import Dict, List, Optional

from langchain.text_splitter import MarkdownTextSplitter

from ...models import TaskData
from ..base import TaskExtractor
from .parsers.default_parser import DefaultTaskParser
from .parsers.research_parser import ResearchTaskParser
from .serialization.context import serialize_context
from prompts.task_extraction_prompts import (
    DEFAULT_TASK_EXTRACTION_PROMPT, 
    DEFAULT_RESPONSE_FORMAT,
    RESEARCH_TASK_EXTRACTION_PROMPT,
    RESEARCH_RESPONSE_FORMAT,
    RESEARCH_HUMAN_PROMPT
)

class LangchainTaskExtractor(TaskExtractor):
    """Task extractor using any Langchain model"""
    
    def __init__(
        self, 
        llm,
        prompt_template: str = DEFAULT_TASK_EXTRACTION_PROMPT,
        response_format: str = DEFAULT_RESPONSE_FORMAT,
        human_template: str = '',
        parser: Optional[DefaultTaskParser] = None,
        max_retries: int = 3,
        chunk_size: int = 4000,
        chunk_overlap: int = 200
    ):
        """
        Initialize with any Langchain model
        
        Args:
            llm: Any Langchain model (e.g., Ollama, OpenAI, etc.)
            prompt_template: Custom prompt template with {content}, {context}, and {response_format} placeholders
            response_format: Format specification for the LLM response
            parser: Custom parser to parse LLM response into tasks
            max_retries: Maximum number of chunk splitting attempts
            chunk_size: Size of text chunks for markdown splitting
            chunk_overlap: Overlap between chunks to maintain context
        """
        self.llm = llm
        self.prompt_template = prompt_template
        self.response_format = response_format
        self.human_template = human_template
        self.parser = parser or DefaultTaskParser()
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def _try_extract_with_chunk(self, content: str, context_str: str) -> List[TaskData]:
        """Attempt to extract tasks from a chunk of content"""
        try:
            system_msg = self.prompt_template.format(
                response_format=self.response_format
            )
            human_msg = self.human_template.format(
                content=content,
                context=context_str
            )
            msg_thread = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": human_msg}
            ]
            response = self.llm.invoke(msg_thread)
            
            # Safely encode response for logging
            try:
                # Encode as ASCII with unicode escapes for logging
                log_response = str(response).encode('ascii', 'backslashreplace').decode('ascii')
                logging.debug(f"Response (with escaped unicode): {log_response}")
            except Exception as e:
                logging.debug(f"Could not log full response due to encoding issues: {str(e)}")
            
            return self.parser.parse(response.content)

        except Exception as e:
            logging.error(f"Error processing content: {str(e)}")
            return None
            
    def extract_tasks(self, content: str, context: Dict = None) -> List[TaskData]:
        """
        Extract tasks from content using Langchain model.
        Uses Markdown-aware text splitting for better chunk boundaries.
        
        Args:
            content: Text content to extract tasks from
            context: Optional metadata/context about the content
            
        Returns:
            List of extracted tasks
        """
        # Prepare context with safe serialization
        context_str = serialize_context(context)
        
        try:
            # Initialize Markdown splitter
            text_splitter = MarkdownTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            # Split content into markdown-aware chunks
            chunks = text_splitter.split_text(content)
            logging.info(f"Split content into {len(chunks)} markdown chunks")
            
            all_tasks = []
            for i, chunk in enumerate(chunks, 1):
                logging.debug(f"Processing chunk {i}/{len(chunks)}")
                chunk_tasks = self._try_extract_with_chunk(chunk, context_str)
                
                if chunk_tasks is not None:
                    all_tasks.extend(chunk_tasks)
                else:
                    logging.error(f"Failed to process chunk {i}")
                    raise
            
            return all_tasks
            
        except Exception as e:
            logging.error(f"Error extracting tasks: {str(e)}")
            return None
            
    def extract_tasks_hierarchical(self, content: str, context: Dict = None) -> List[TaskData]:
        """
        Extract tasks from content using Langchain model.
        Uses progressive chunking on failure.
        
        Args:
            content: Text content to extract tasks from
            context: Optional metadata/context about the content
            
        Returns:
            List of extracted tasks
        """
        # Prepare context with safe serialization
        context_str = serialize_context(context)
        
        try:
            # First try with full content
            tasks = self._try_extract_with_chunk(content, context_str)
            if tasks is not None:
                return tasks
                
            # If failed, try progressively smaller chunks
            current_chunks = [content]
            for attempt in range(self.max_retries):
                logging.info(f"Retry {attempt + 1}: Splitting content into {len(current_chunks) * 2} chunks")
                
                all_tasks = []
                new_chunks = []
                
                # Split each chunk in half
                for chunk in current_chunks:
                    mid = len(chunk) // 2
                    new_chunks.extend([chunk[:mid], chunk[mid:]])
                
                # Try processing new chunks
                for chunk in new_chunks:
                    chunk_tasks = self._try_extract_with_chunk(chunk, context_str)
                    if chunk_tasks is not None:
                        all_tasks.extend(chunk_tasks)
                    else:
                        break
                else:
                    # All chunks processed successfully
                    return all_tasks
                    
                # Prepare for next iteration
                current_chunks = new_chunks
            
            logging.error(f"Failed to process content after {self.max_retries} retries")
            return None
            
        except Exception as e:
            logging.error(f"Error extracting tasks: {str(e)}")
            return None

    @classmethod
    def create_research_extractor(cls, llm, max_retries: int = 3) -> 'LangchainTaskExtractor':
        """Factory method to create a research-focused task extractor"""
        return cls(
            llm=llm,
            prompt_template=RESEARCH_TASK_EXTRACTION_PROMPT,
            response_format=RESEARCH_RESPONSE_FORMAT,
            human_template=RESEARCH_HUMAN_PROMPT,
            parser=ResearchTaskParser(),
            max_retries=max_retries
        ) 