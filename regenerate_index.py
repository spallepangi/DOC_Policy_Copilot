#!/usr/bin/env python3
"""
Regenerate the index with improved caption generation.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def regenerate_index():
    """Regenerate the index with improved captions."""
    
    print("=" * 60)
    print("🔄 Regenerating Index with Improved Captions")
    print("=" * 60)
    
    try:
        from main import RAGPipeline
        
        # Create RAG pipeline - this will auto-initialize and index documents
        print("Initializing RAG Pipeline...")
        rag = RAGPipeline()
        
        # Get final stats
        stats = rag.get_index_stats()
        print(f"\n✅ Index regenerated successfully!")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Text documents: {stats.get('text_documents', 0)}")
        print(f"   Image documents: {stats.get('image_documents', 0)}")
        print(f"   Files indexed: {stats.get('unique_files', 0)}")
        
        # Test the map query
        print(f"\n🗺️  Testing map query...")
        result = rag.generate_response("Where is the map of correctional facilities?")
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Sources: {len(result.get('sources', []))}")
        
        # Show any image sources
        if result.get('sources'):
            for source in result['sources']:
                if source.get('type') == 'image':
                    print(f"   📷 Image: {source.get('source')}")
                    print(f"      Caption: {source.get('caption', 'No caption')}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_index()
