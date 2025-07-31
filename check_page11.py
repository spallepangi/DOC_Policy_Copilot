#!/usr/bin/env python3
"""
Check page 11 content specifically.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_page11():
    """Check page 11 content."""
    
    try:
        from vector_store_stable import StableVectorStore
        
        vector_store = StableVectorStore("index/faiss_index/")
        
        # Find page 11 documents
        page11_docs = [doc for doc in vector_store.documents 
                      if 'Family_Friends_Handbook' in doc.get('filename', '') 
                      and doc.get('page_number') == 11]
        
        print(f"Found {len(page11_docs)} documents from page 11:")
        for doc in page11_docs:
            print(f"Type: {doc.get('type')}")
            print(f"Source: {doc.get('source')}")
            content = doc.get('text', doc.get('caption', 'No content'))
            print(f"Content ({len(content)} chars):")
            print(content)
            print("-" * 80)
        
        # Also check pages around it
        print("\nChecking pages 10-12 for context:")
        nearby_docs = [doc for doc in vector_store.documents 
                      if 'Family_Friends_Handbook' in doc.get('filename', '') 
                      and doc.get('page_number') in [10, 11, 12]]
        
        for doc in sorted(nearby_docs, key=lambda x: (x.get('page_number', 0), x.get('type', ''))):
            page = doc.get('page_number')
            doc_type = doc.get('type')
            content = doc.get('text', doc.get('caption', 'No content'))[:200]
            print(f"Page {page} ({doc_type}): {content}...")
            print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_page11()
