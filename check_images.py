#!/usr/bin/env python3
"""
Check what images are currently indexed in the system.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_indexed_images():
    """Check what images are currently in the index."""
    
    print("=" * 60)
    print("🖼️  Checking Indexed Images")
    print("=" * 60)
    
    try:
        from vector_store_stable import StableVectorStore
        
        vector_store = StableVectorStore("index/faiss_index/")
        
        print(f"Total documents: {len(vector_store.documents)}")
        
        # Find all image documents
        image_docs = [doc for doc in vector_store.documents if doc.get('type') == 'image']
        text_docs = [doc for doc in vector_store.documents if doc.get('type') == 'text']
        
        print(f"Image documents: {len(image_docs)}")
        print(f"Text documents: {len(text_docs)}")
        
        print("\n📷 Images currently indexed:")
        for i, img_doc in enumerate(image_docs, 1):
            print(f"{i}. {img_doc.get('source', 'Unknown source')}")
            print(f"   Caption: {img_doc.get('caption', 'No caption')}")
            print(f"   Dimensions: {img_doc.get('dimensions', 'Unknown')}")
            print(f"   Base64 length: {len(img_doc.get('base64_data', ''))}")
            print()
        
        # Check specifically for Family_Friends_Handbook page 11
        print("🔍 Looking for Family_Friends_Handbook page 11 specifically:")
        family_docs = [doc for doc in vector_store.documents 
                      if 'Family_Friends_Handbook' in doc.get('filename', '') 
                      and doc.get('page_number') == 11]
        
        print(f"Found {len(family_docs)} documents from Family_Friends_Handbook page 11:")
        for doc in family_docs:
            doc_type = doc.get('type', 'unknown')
            print(f"  - Type: {doc_type}, Source: {doc.get('source', 'Unknown')}")
            if doc_type == 'text':
                print(f"    Text preview: {doc.get('text', 'No text')[:100]}...")
            elif doc_type == 'image':
                print(f"    Caption: {doc.get('caption', 'No caption')}")
            print()
        
        # Test a search for "map"
        print("🗺️  Testing search for 'map':")
        search_results = vector_store.search("map of correctional facilities", k=10)
        print(f"Found {len(search_results)} results for 'map of correctional facilities':")
        
        for i, (doc, score) in enumerate(search_results, 1):
            doc_type = doc.get('type', 'unknown')
            content = doc.get('text', doc.get('caption', 'No content'))[:80] + "..."
            print(f"{i}. Score: {score:.3f}, Type: {doc_type}")
            print(f"   Source: {doc.get('source', 'Unknown')}")
            print(f"   Content: {content}")
            print()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_indexed_images()
