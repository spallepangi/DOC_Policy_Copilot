#!/usr/bin/env python3
"""
Final test script for Missouri DOC Policy Copilot with stable embeddings
Tests both text and image (via caption) functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_stable_rag():
    """Test the stable RAG system with SentenceTransformers."""
    
    print("=" * 60)
    print("🧪 Testing Stable RAG System")
    print("=" * 60)
    
    try:
        print("\n1. Testing stable vector store directly...")
        from vector_store_stable import StableVectorStore
        
        vector_store = StableVectorStore()
        print("✅ StableVectorStore initialized successfully")
        
        # Test with sample documents
        sample_docs = [
            {
                'text': 'Missouri DOC disciplinary procedures require a hearing before any major penalty.',
                'type': 'text',
                'filename': 'test.pdf',
                'page_number': 1,
                'source': 'test.pdf Page 1'
            },
            {
                'text': 'Visiting policies allow family members to visit on weekends.',
                'type': 'text',
                'filename': 'test.pdf',
                'page_number': 2,
                'source': 'test.pdf Page 2'
            },
            {
                'caption': 'Chart showing disciplinary process flowchart',
                'type': 'image',
                'filename': 'test.pdf',
                'page_number': 3,
                'source': 'test.pdf Page 3',
                'base64_data': ''  # Empty for this test
            }
        ]
        
        print(f"\n2. Creating index with {len(sample_docs)} sample documents...")
        vector_store.create_index(sample_docs)
        print("✅ Index created successfully")
        
        # Test searches
        test_queries = [
            "disciplinary procedures",
            "visiting policies", 
            "flowchart process"
        ]
        
        print(f"\n3. Testing {len(test_queries)} queries...")
        for query in test_queries:
            results = vector_store.search(query, k=3)
            print(f"   Query: '{query}' -> {len(results)} results")
            if results:
                top_result = results[0]
                doc, score = top_result
                print(f"      Top result: Score {score:.3f} - {doc.get('text', doc.get('caption', 'No content'))[:50]}...")
        
        print("\n4. Testing full RAG pipeline...")
        from main import RAGPipeline
        
        rag = RAGPipeline()
        print("✅ RAG Pipeline initialized")
        
        stats = rag.get_index_stats()
        print(f"   Current stats: {stats}")
        
        if stats['total_documents'] == 0:
            print("   No existing documents, using sample data...")
            # Test with sample documents if no real PDFs
            rag.vector_store.create_index(sample_docs)
            print("   ✅ Sample data indexed")
        
        # Test a query
        print("\n5. Testing query generation...")
        test_query = "What are the disciplinary procedures?"
        result = rag.generate_response(test_query)
        
        print(f"   Query: '{test_query}'")
        print(f"   Answer: {result['answer'][:200]}...")
        print(f"   Sources: {len(result.get('sources', []))}")
        
        print("\n" + "=" * 60)
        print("✅ Stable RAG System Test Completed Successfully!")
        print("🚀 System is ready!")
        print("\nTo run the Streamlit app:")
        print("   streamlit run streamlit_app.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stable_rag()
