#!/usr/bin/env python3
"""
Test script to analyze why irrelevant images are being returned in citations.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_image_relevance():
    """Test which images are being returned for different queries."""
    
    print("=" * 60)
    print("🔍 Testing Image Relevance in Citations")
    print("=" * 60)
    
    try:
        from main import RAGPipeline
        
        rag = RAGPipeline()
        
        # Test queries that should NOT return images
        text_only_queries = [
            "What are the visiting hours?",
            "How are disciplinary actions handled?",
            "What are the phone call policies?",
            "What is the grievance process?"
        ]
        
        # Test queries that SHOULD return images
        image_relevant_queries = [
            "Show me the map of correctional facilities",
            "What does the organizational chart look like?",
            "Are there any diagrams or charts?"
        ]
        
        print("\n📝 Testing text-only queries (should have minimal/no irrelevant images):")
        for query in text_only_queries:
            print(f"\n🔍 Query: '{query}'")
            result = rag.generate_response(query)
            
            sources = result.get('sources', [])
            image_sources = [s for s in sources if s.get('type') == 'image']
            text_sources = [s for s in sources if s.get('type') == 'text']
            
            print(f"   📊 Results: {len(text_sources)} text, {len(image_sources)} images")
            
            if image_sources:
                print("   🖼️  Image sources found:")
                for img_src in image_sources:
                    caption = img_src.get('caption', 'No caption')
                    score = img_src.get('similarity_score', 0)
                    print(f"      - Score: {score:.3f} | {img_src.get('source')}")
                    print(f"        Caption: {caption[:80]}...")
        
        print(f"\n🖼️  Testing image-relevant queries (should return relevant images):")
        for query in image_relevant_queries:
            print(f"\n🔍 Query: '{query}'")
            result = rag.generate_response(query)
            
            sources = result.get('sources', [])
            image_sources = [s for s in sources if s.get('type') == 'image']
            text_sources = [s for s in sources if s.get('type') == 'text']
            
            print(f"   📊 Results: {len(text_sources)} text, {len(image_sources)} images")
            
            if image_sources:
                print("   🖼️  Image sources found:")
                for img_src in image_sources:
                    caption = img_src.get('caption', 'No caption')
                    score = img_src.get('similarity_score', 0)
                    print(f"      - Score: {score:.3f} | {img_src.get('source')}")
                    print(f"        Caption: {caption[:80]}...")
        
        # Check what the similarity thresholds look like
        print(f"\n📈 Analyzing similarity score distribution:")
        
        # Get all vector search results for a sample query
        vector_store = rag.vector_store
        sample_results = vector_store.search("visiting policies", k=20)
        
        print("   Top 20 results for 'visiting policies':")
        for i, (doc, score) in enumerate(sample_results, 1):
            doc_type = doc.get('type', 'unknown')
            content = doc.get('text', doc.get('caption', 'No content'))[:50] + "..."
            print(f"   {i:2d}. {doc_type:5s} | Score: {score:.3f} | {content}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_relevance()
