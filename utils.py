import fitz  # PyMuPDF
import os
from typing import List, Dict, Any
import re


def load_pdf_files(folder_path: str) -> List[Dict[str, Any]]:
    """
    Load all PDF files from the specified folder and extract text.
    
    Args:
        folder_path (str): Path to the folder containing PDF files
        
    Returns:
        List[Dict]: List of documents with text content and metadata
    """
    documents = []
    
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return documents
    
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # Only add pages with content
                    documents.append({
                        'text': text,
                        'filename': pdf_file,
                        'page_number': page_num + 1,
                        'source': f"{pdf_file} (Page {page_num + 1})"
                    })
            
            doc.close()
            print(f"Loaded {len(doc)} pages from {pdf_file}")
            
        except Exception as e:
            print(f"Error loading {pdf_file}: {str(e)}")
    
    return documents


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with specified size and overlap.
    
    Args:
        text (str): Text to be chunked
        chunk_size (int): Approximate number of tokens per chunk
        overlap (int): Number of tokens to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Simple tokenization by splitting on whitespace
    words = text.split()
    
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        
        if end >= len(words):
            break
            
        start = end - overlap
    
    return chunks


def chunk_documents(documents: List[Dict[str, Any]], chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunk all documents into smaller pieces while preserving metadata.
    
    Args:
        documents (List[Dict]): List of documents with text and metadata
        chunk_size (int): Approximate number of tokens per chunk
        overlap (int): Number of tokens to overlap between chunks
        
    Returns:
        List[Dict]: List of chunked documents with metadata
    """
    chunked_docs = []
    
    for doc in documents:
        text_chunks = chunk_text(doc['text'], chunk_size, overlap)
        
        for i, chunk in enumerate(text_chunks):
            chunked_doc = {
                'text': chunk,
                'filename': doc['filename'],
                'page_number': doc['page_number'],
                'source': doc['source'],
                'chunk_id': f"{doc['filename']}_page{doc['page_number']}_chunk{i+1}"
            }
            chunked_docs.append(chunked_doc)
    
    return chunked_docs


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text
