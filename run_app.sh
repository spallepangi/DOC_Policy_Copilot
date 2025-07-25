#!/bin/bash

# Missouri DOC Policy Copilot - Startup Script

echo "🏛️  Starting Missouri DOC Policy Copilot..."
echo "================================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
echo "📋 Checking dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p data/policies
mkdir -p index/faiss_index
mkdir -p .streamlit

# Check if API key is set
if [ -f ".env" ]; then
    echo "🔑 Environment file found"
else
    echo "⚠️  Warning: .env file not found. Make sure your API key is configured."
fi

# Launch the application
echo "🚀 Launching Streamlit application..."
echo "📍 Open your browser to: http://localhost:8501"
echo "================================================"

streamlit run app.py --server.port=8501 --server.address=0.0.0.0
