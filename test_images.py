#!/usr/bin/env python3
"""
Test script to debug image handling in RAG system.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_image_queries():
    """Test queries that should return image information."""
    
    print("=" * 60)
    print("🖼️  Testing Image Query Handling")
    print("=" * 60)
    
    try:
        from main import RAGPipeline
        
        rag = RAGPipeline()
        stats = rag.get_index_stats()
        
        print(f"Index stats: {stats}")
        
        # Test queries that might return images
        image_queries = [
            "Show me a diagram",
            "Are there any charts or images?", 
            "What does the organizational chart look like?",
            "Can you describe any visual content?",
            "What images are available in the employee handbook?"
        ]
        
        for query in image_queries:
            print(f"\n🔍 Query: '{query}'")
            
            # First check what the vector search returns
            search_results = rag.vector_store.search(query, k=5)
            print(f"   Vector search found {len(search_results)} results:")
            
            for i, (doc, score) in enumerate(search_results):
                doc_type = doc.get('type', 'unknown')
                content_preview = doc.get('text', doc.get('caption', 'No content'))[:50] + "..."
                print(f"      {i+1}. Type: {doc_type}, Score: {score:.3f}")
                print(f"         Source: {doc.get('source', 'Unknown')}")
                print(f"         Content: {content_preview}")
            
            # Now test the full response
            print("\n   🤖 Full Response:")
            result = rag.generate_response(query)
            print(f"      Answer: {result['answer'][:200]}...")
            print(f"      Sources: {len(result.get('sources', []))}")
            
            # Show source details
            if result.get('sources'):
                for source in result['sources']:
                    if source.get('type') == 'image':
                        print(f"         📷 Image source: {source.get('source')}")
                        print(f"             Caption: {source.get('caption', 'No caption')}")
            
            print("-" * 40)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_queries()
