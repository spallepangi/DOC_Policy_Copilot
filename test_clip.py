#!/usr/bin/env python3
"""
Test script for CLIP-based Missouri DOC Policy Copilot
Tests both text and image embedding and retrieval functionality.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from main import RAGPipeline

def test_clip_multimodal_rag():
    """Test the CLIP-based multimodal RAG system."""
    
    print("=" * 60)
    print("🧪 Testing CLIP-based Multimodal RAG System")
    print("=" * 60)
    
    try:
        # Initialize RAG pipeline
        print("\n1. Initializing RAG Pipeline with CLIP...")
        rag = RAGPipeline()
        
        # Get stats
        stats = rag.get_index_stats()
        print(f"   📊 Index Stats: {stats}")
        
        if stats['total_documents'] == 0:
            print("   ⚠️  No documents found. Let's index some documents...")
            
            # Check if we have PDF files
            data_folder = "data/policies/"
            if os.path.exists(data_folder):
                pdf_files = [f for f in os.listdir(data_folder) if f.lower().endswith('.pdf')]
                if pdf_files:
                    print(f"   📁 Found {len(pdf_files)} PDF files. Indexing...")
                    rag.index_documents()
                    stats = rag.get_index_stats()
                    print(f"   ✅ Indexed {stats['total_documents']} documents")
                else:
                    print(f"   ❌ No PDF files found in {data_folder}")
                    print("   📝 Please add some PDF files to test the system")
                    return
            else:
                print(f"   ❌ Data folder {data_folder} not found")
                return
        
        # Test queries
        test_queries = [
            "What are the disciplinary procedures?",
            "What are the visiting policies?",
            "What are the medical care guidelines?",
            "How are grievances handled?",
            "What security measures are in place?"
        ]
        
        print(f"\n2. Testing {len(test_queries)} sample queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: '{query}'")
            
            try:
                result = rag.generate_response(query, top_k=5)
                
                # Display results
                print(f"   📝 Answer: {result['answer'][:200]}...")
                print(f"   📚 Sources found: {len(result.get('sources', []))}")
                
                # Show source types
                if result.get('sources'):
                    text_sources = sum(1 for s in result['sources'] if s.get('type') == 'text')
                    image_sources = sum(1 for s in result['sources'] if s.get('type') == 'image')
                    print(f"      📄 Text sources: {text_sources}")
                    print(f"      🖼️  Image sources: {image_sources}")
                    
                    # Show top similarity scores
                    top_score = max(s.get('similarity_score', 0) for s in result['sources'])
                    print(f"      🎯 Top similarity: {top_score:.3f}")
                
            except Exception as e:
                print(f"   ❌ Query failed: {str(e)}")
        
        print(f"\n3. Testing multimodal capabilities...")
        
        # Test with image-related queries
        image_queries = [
            "Show me diagrams or charts",
            "What visual information is available?",
            "Are there any forms or documents shown?",
            "What images are in the policies?"
        ]
        
        for query in image_queries[:2]:  # Test first 2 to save time
            print(f"\n   Image Query: '{query}'")
            
            try:
                result = rag.generate_response(query, top_k=10)
                
                if result.get('sources'):
                    image_sources = [s for s in result['sources'] if s.get('type') == 'image']
                    if image_sources:
                        print(f"   🖼️  Found {len(image_sources)} image sources!")
                        for img_src in image_sources[:2]:  # Show first 2
                            print(f"      - {img_src.get('filename')} Page {img_src.get('page_number')}")
                            print(f"        Caption: {img_src.get('caption', 'No caption')}")
                    else:
                        print("   📝 No image sources found, but got text results")
                else:
                    print("   ⚠️  No relevant sources found")
                    
            except Exception as e:
                print(f"   ❌ Image query failed: {str(e)}")
        
        print(f"\n4. System Performance Summary")
        final_stats = rag.get_index_stats()
        print(f"   📊 Total documents indexed: {final_stats['total_documents']}")
        print(f"   🔍 Vector dimensions: {final_stats.get('dimension', 'Unknown')}")
        print(f"   💾 Index path: {final_stats.get('index_path', 'Unknown')}")
        
        print("\n" + "=" * 60)
        print("✅ CLIP Multimodal RAG Test Completed Successfully!")
        print("🚀 Ready to use with Streamlit: streamlit run streamlit_app.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clip_multimodal_rag()
