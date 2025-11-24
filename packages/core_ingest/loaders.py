import io
from pypdf import PdfReader
from typing import List, Dict, Any


def pdf_to_chunks(content: bytes, maxlen: int = 900) -> List[Dict[str, Any]]:
    """Extract chunks from PDF file"""
    reader = PdfReader(io.BytesIO(content))
    chunks = []
    for pi, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text:
            continue
        text = " ".join(text.split())
        for i in range(0, len(text), maxlen):
            chunk = text[i:i+maxlen]
            chunks.append({"text": chunk, "page_from": pi, "page_to": pi})
    return chunks


def text_to_chunks(content: bytes, maxlen: int = 900) -> List[Dict[str, Any]]:
    """Extract chunks from plain text file (.txt, .md)"""
    text = content.decode('utf-8', errors='ignore')
    text = " ".join(text.split())  # Normalize whitespace
    
    chunks = []
    for i in range(0, len(text), maxlen):
        chunk = text[i:i+maxlen]
        chunks.append({"text": chunk, "page_from": 1, "page_to": 1})
    
    return chunks


def markdown_to_chunks(content: bytes, maxlen: int = 900) -> List[Dict[str, Any]]:
    """
    Extract chunks from Markdown file with section awareness.
    Tries to split by headers when possible for better context.
    """
    text = content.decode('utf-8', errors='ignore')
    lines = text.split('\n')
    
    chunks = []
    current_chunk = ""
    current_section = ""
    
    for line in lines:
        # Detect headers
        if line.startswith('#'):
            current_section = line.strip()
        
        # Add line to current chunk
        current_chunk += line + " "
        
        # Split if chunk is too large
        if len(current_chunk) >= maxlen:
            chunks.append({
                "text": current_chunk.strip(),
                "page_from": 1,
                "page_to": 1,
                "section": current_section
            })
            current_chunk = ""
    
    # Add remaining chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "page_from": 1,
            "page_to": 1,
            "section": current_section
        })
    
    return chunks


def load_document(content: bytes, filename: str, maxlen: int = 900) -> List[Dict[str, Any]]:
    """
    Load document and extract chunks based on file type.
    
    Supported formats:
    - .pdf: PDF documents
    - .txt: Plain text files
    - .md: Markdown files
    
    Args:
        content: File content as bytes
        filename: Original filename (used to detect file type)
        maxlen: Maximum chunk length
    
    Returns:
        List of chunks with text and metadata
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return pdf_to_chunks(content, maxlen)
    elif filename_lower.endswith('.md'):
        return markdown_to_chunks(content, maxlen)
    elif filename_lower.endswith('.txt'):
        return text_to_chunks(content, maxlen)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Supported: .pdf, .md, .txt")

