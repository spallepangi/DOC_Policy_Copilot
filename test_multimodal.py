#!/usr/bin/env python3

"""
Test script for the multimodal RAG implementation with Cohere embeddings.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import RAGPipeline

def test_multimodal_rag():
    """Test the multimodal RAG pipeline."""
    
    print("🚀 Testing Multimodal RAG Pipeline with Cohere Embeddings")
    print("=" * 60)
    
    try:
        # Initialize the RAG pipeline
        print("1. Initializing RAG Pipeline...")
        rag = RAGPipeline()
        
        # Get initial stats
        stats = rag.get_index_stats()
        print(f"   📊 Initial stats: {stats['total_documents']} documents, {stats['total_chunks']} chunks")
        
        # If no documents, index them
        if stats['total_documents'] == 0:
            print("2. No existing index found. Creating new index...")
            rag.index_documents()
            stats = rag.get_index_stats()
            print(f"   ✅ Indexing complete: {stats['total_documents']} documents, {stats['total_chunks']} chunks")
        else:
            print("2. Using existing index...")
        
        # Test a simple query
        print("3. Testing query processing...")
        test_query = "What are the visiting hours?"
        print(f"   🔍 Query: '{test_query}'")
        
        result = rag.generate_response(test_query)
        
        if result:
            print(f"   ✅ Answer: {result['answer'][:200]}...")
            print(f"   📚 Sources found: {len(result.get('sources', []))}")
            
            # Display source types
            text_sources = sum(1 for s in result.get('sources', []) if s.get('type') == 'text')
            image_sources = sum(1 for s in result.get('sources', []) if s.get('type') == 'image')
            print(f"   📝 Text sources: {text_sources}")
            print(f"   🖼️  Image sources: {image_sources}")
        else:
            print("   ❌ No result generated")
            
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multimodal_rag()
    sys.exit(0 if success else 1)
