#!/usr/bin/env python3

import os
import sys

def test_imports():
    """Test that all required modules can be imported."""
    try:
        print("🧪 Testing imports...")
        
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
        
        import faiss
        print("✅ FAISS imported successfully")
        
        import fitz  # PyMuPDF
        print("✅ PyMuPDF imported successfully")
        
        from main import RAGPipeline
        print("✅ RAG Pipeline imported successfully")
        
        from vector_store import VectorStore
        print("✅ Vector Store imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_environment():
    """Test environment setup."""
    print("\n🔧 Testing environment...")
    
    # Check API key
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found")
    
    # Check directories
    dirs_to_check = ['data/policies', 'index/faiss_index', '.streamlit']
    for directory in dirs_to_check:
        if os.path.exists(directory):
            print(f"✅ Directory {directory} exists")
        else:
            print(f"📁 Creating directory {directory}")
            os.makedirs(directory, exist_ok=True)
    
    return True

def test_rag_pipeline():
    """Test RAG pipeline initialization."""
    print("\n🤖 Testing RAG Pipeline...")
    
    try:
        from main import RAGPipeline
        rag = RAGPipeline()
        stats = rag.get_index_stats()
        print(f"✅ RAG Pipeline initialized successfully")
        print(f"📊 Stats: {stats}")
        return True
    except Exception as e:
        print(f"❌ RAG Pipeline error: {e}")
        return False

def main():
    """Run all tests."""
    print("🏛️  Missouri DOC Policy Copilot - Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test environment
    if not test_environment():
        all_passed = False
    
    # Test RAG pipeline
    if not test_rag_pipeline():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Your application is ready to run.")
        print("\n🚀 To start the application, run:")
        print("   streamlit run app.py")
        print("\n📍 Then open your browser to: http://localhost:8501")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
