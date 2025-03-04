"""Utilities for chunking content for LLM processing"""

from typing import List

def chunk_content(content: str, max_size: int = 4000) -> List[str]:
    """
    Split content into smaller chunks for LLM processing.
    Tries to split at paragraph boundaries when possible.
    
    Args:
        content: Text content to split
        max_size: Maximum size of each chunk
        
    Returns:
        List of content chunks
    """
    if len(content) <= max_size:
        return [content]
        
    chunks = []
    paragraphs = content.split('\n\n')
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        if current_size + para_size <= max_size:
            current_chunk.append(para)
            current_size += para_size
        else:
            # If a single paragraph is too large, split it by sentences
            if para_size > max_size:
                sentences = para.split('. ')
                for sent in sentences:
                    if len(sent) > max_size:
                        # If even a sentence is too long, split by character
                        for i in range(0, len(sent), max_size):
                            chunks.append(sent[i:i + max_size])
                    else:
                        if current_size + len(sent) > max_size:
                            chunks.append('\n\n'.join(current_chunk))
                            current_chunk = [sent]
                            current_size = len(sent)
                        else:
                            current_chunk.append(sent)
                            current_size += len(sent)
            else:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks 