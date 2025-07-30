import fitz  # PyMuPDF
import os
from typing import List, Dict, Any
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

import config


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


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into chunks using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        text (str): Text to be chunked
        chunk_size (int): Approximate number of characters per chunk (defaults to config)
        overlap (int): Number of characters to overlap between chunks (defaults to config)
        
    Returns:
        List[str]: List of text chunks
    """
    # Use config defaults if not provided
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE * 4  # Approximate chars per token
    if overlap is None:
        overlap = config.CHUNK_OVERLAP * 4  # Approximate chars per token
    
    # Initialize the text splitter with semantic separators
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=[
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            "! ",    # Exclamatory sentences
            "? ",    # Questions
            "; ",    # Semicolons
            ", ",    # Commas
            " ",     # Words
            "",      # Characters
        ]
    )
    
    chunks = text_splitter.split_text(text)
    return chunks


def chunk_documents(documents: List[Dict[str, Any]], chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
    """
    Chunk all documents into smaller pieces while preserving metadata using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        documents (List[Dict]): List of documents with text and metadata
        chunk_size (int): Approximate number of tokens per chunk (defaults to config)
        overlap (int): Number of tokens to overlap between chunks (defaults to config)
        
    Returns:
        List[Dict]: List of chunked documents with metadata
    """
    # Use config defaults if not provided
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE
    if overlap is None:
        overlap = config.CHUNK_OVERLAP
    
    chunked_docs = []
    
    for doc in documents:
        # Convert token-based sizes to character-based for the text splitter
        char_chunk_size = chunk_size * 4  # Approximate chars per token
        char_overlap = overlap * 4  # Approximate chars per token
        
        text_chunks = chunk_text(doc['text'], char_chunk_size, char_overlap)
        
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
