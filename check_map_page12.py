#!/usr/bin/env python3
"""
Check page 12 where we found an image - might be the map.
"""

import os
import sys
import fitz  # PyMuPDF
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_page12():
    """Check page 12 for the map."""
    
    pdf_path = "data/policies/Family_Friends_Handbook.pdf"
    
    try:
        doc = fitz.open(pdf_path)
        page_num = 11  # 0-indexed, so page 12 is index 11
        
        page = doc[page_num]
        print(f"📄 Examining page {page_num + 1} of {pdf_path}")
        
        # Get page text
        page_text = page.get_text()
        print(f"📝 Page text:")
        print(page_text)
        print("-" * 80)
        
        # Get image list
        image_list = page.get_images()
        print(f"🖼️  Found {len(image_list)} images on page {page_num + 1}")
        
        # Also check the indexed data
        from vector_store_stable import StableVectorStore
        vector_store = StableVectorStore("index/faiss_index/")
        
        page12_docs = [doc for doc in vector_store.documents 
                      if 'Family_Friends_Handbook' in doc.get('filename', '') 
                      and doc.get('page_number') == 12]
        
        print(f"\n📊 Indexed documents from page 12: {len(page12_docs)}")
        for doc_data in page12_docs:
            doc_type = doc_data.get('type')
            content = doc_data.get('text', doc_data.get('caption', 'No content'))
            print(f"Type: {doc_type}")
            print(f"Content: {content}")
            print("-" * 40)
        
        doc.close()
        
        # Check if the image content mentions map or facilities
        if page12_docs:
            image_docs = [d for d in page12_docs if d.get('type') == 'image']
            if image_docs:
                caption = image_docs[0].get('caption', '')
                if 'map' in caption.lower() or 'facilities' in caption.lower():
                    print("🗺️  Found map-related content in image caption!")
                else:
                    print("📝 Image caption doesn't mention map, but content is:")
                    print(f"   '{caption}'")
                    
                    # Check if the text mentions facilities in a way that suggests a map
                    facility_indicators = ['ACC', 'JCCC', 'BCC', 'CCC', 'CTCC', 'FRDC', 'facility']
                    found_indicators = [ind for ind in facility_indicators if ind in caption]
                    if found_indicators:
                        print(f"   Found facility indicators: {found_indicators}")
                        print("   This might be the map showing facility locations!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_page12()
