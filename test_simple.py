#!/usr/bin/env python3
"""
Simple test for CLIP vector store without full RAG pipeline.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_clip_vector_store():
    """Test just the CLIP vector store functionality."""
    
    print("=" * 60)
    print("🧪 Testing CLIP Vector Store")
    print("=" * 60)
    
    try:
        print("\n1. Importing CLIPVectorStore...")
        from vector_store_clip import CLIPVectorStore
        print("✅ Import successful")
        
        print("\n2. Initializing CLIP Vector Store...")
        vector_store = CLIPVectorStore()
        print("✅ CLIP Vector Store initialized")
        
        print("\n3. Testing text embedding...")
        test_text = "This is a test document about Missouri DOC policies."
        embedding = vector_store.embed_text_chunk(test_text)
        print(f"✅ Text embedding generated with shape: {embedding.shape}")
        
        print("\n4. Testing query embedding...")
        test_query = "What are the policies?"
        query_embedding = vector_store.generate_query_embedding(test_query)
        print(f"✅ Query embedding generated with shape: {query_embedding.shape}")
        
        print("\n5. Testing with sample documents...")
        sample_docs = [
            {
                'text': 'This is about disciplinary procedures.',
                'type': 'text',
                'filename': 'test.pdf',
                'page_number': 1,
                'source': 'test.pdf Page 1'
            },
            {
                'text': 'This covers visiting policies and guidelines.',
                'type': 'text',
                'filename': 'test.pdf',
                'page_number': 2,
                'source': 'test.pdf Page 2'
            }
        ]
        
        print(f"   Creating index with {len(sample_docs)} documents...")
        vector_store.create_index(sample_docs)
        print("✅ Index created successfully")
        
        print("\n6. Testing search...")
        results = vector_store.search("disciplinary procedures", k=2)
        print(f"✅ Search completed, found {len(results)} results")
        
        for i, (doc, score) in enumerate(results):
            print(f"   Result {i+1}: Score {score:.3f} - {doc['text'][:50]}...")
        
        stats = vector_store.get_stats()
        print(f"\n📊 Final Stats: {stats}")
        
        print("\n" + "=" * 60)
        print("✅ CLIP Vector Store Test Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clip_vector_store()
