#!/usr/bin/env python3

"""
Test script for Cohere image embedding functionality.
"""

import os
import sys
import base64
import io
from PIL import Image

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_store import VectorStore
from utils import extract_images_from_pdf

def test_image_embedding():
    """Test the image embedding functionality."""
    
    print("🖼️ Testing Cohere Image Embedding Functionality")
    print("=" * 50)
    
    try:
        # Initialize vector store
        print("1. Initializing VectorStore...")
        vs = VectorStore()
        
        # Extract just one image from PDFs for testing
        print("2. Extracting one image from PDFs...")
        images = extract_images_from_pdf("data/policies/")
        
        if not images:
            print("❌ No images found in PDFs")
            return False
        
        # Take just the first image for testing
        test_image = images[0]
        print(f"   📸 Testing with: {test_image['source']}")
        print(f"   📝 Caption: {test_image['caption'][:50]}...")
        
        # Test the image embedding function
        print("3. Testing image embedding...")
        base64_data = test_image['base64_data']
        caption = test_image['caption']
        
        print(f"   🔍 Base64 data length: {len(base64_data)}")
        print(f"   🔍 Image dimensions: {test_image['dimensions']}")
        
        # Try to embed the image
        embedding = vs.embed_image_chunk(base64_data, caption)
        
        if embedding is not None and len(embedding) > 0:
            print(f"   ✅ Image embedding successful!")
            print(f"   📊 Embedding dimension: {len(embedding)}")
            print(f"   📈 Sample values: {embedding[:5]}")
            
            # Test creating a small index with this image
            print("4. Testing index creation with image...")
            test_docs = [test_image]
            vs.create_index(test_docs)
            
            print("5. Testing search...")
            results = vs.search("image", k=1)
            if results:
                print(f"   ✅ Search successful! Found {len(results)} results")
                doc, score = results[0]
                print(f"   📊 Score: {score:.3f}")
                print(f"   📄 Source: {doc['source']}")
            else:
                print("   ❌ Search returned no results")
            
            return True
        else:
            print("   ❌ Image embedding failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_embedding()
    sys.exit(0 if success else 1)
