#!/bin/bash

# Missouri DOC Policy Copilot - Fixed Documents Version

echo "🏛️  Starting Missouri DOC Policy Copilot (Fixed Documents)"
echo "================================================"

# Check if PDF files exist
PDF_DIR="data/policies"
PDF_COUNT=$(find "$PDF_DIR" -name "*.pdf" | wc -l)

echo "📁 Policy Documents Directory: $PDF_DIR"
echo "📄 Found $PDF_COUNT PDF files"

if [ $PDF_COUNT -eq 0 ]; then
    echo "⚠️  WARNING: No PDF files found in $PDF_DIR"
    echo "Please add PDF files to this directory before running the application."
    exit 1
fi

echo "📋 Available PDF files:"
ls -1 "$PDF_DIR"/*.pdf 2>/dev/null | xargs -n1 basename

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if API key is set
if [ -f ".env" ]; then
    echo "🔑 Environment file found"
else
    echo "⚠️  Warning: .env file not found. Make sure your API key is configured."
fi

echo "🤖 Auto-indexing will be performed on startup if needed"
echo "🧠 AI Model: Gemini 1.5 Flash (latest available)"
echo "🚀 Launching Streamlit application..."
echo "📍 Open your browser to: http://localhost:8501"
echo "================================================"

streamlit run app_no_upload.py --server.port=8501 --server.address=0.0.0.0
