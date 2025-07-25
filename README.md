# Missouri DOC Policy Copilot

A Retrieval Augmented Generation (RAG) chatbot that answers questions about Missouri Department of Corrections policy documents using the Gemini API for both embeddings and large language model responses.

## Features

- **Document Processing**: Automatically loads and processes PDF files from Missouri DOC policies
- **Intelligent Chunking**: Splits documents into semantically meaningful chunks with configurable overlap
- **Vector Search**: Uses FAISS for efficient similarity search with Gemini embeddings
- **Grounded Responses**: Generates answers using Gemini Pro with proper document citations
- **Web Interface**: User-friendly Streamlit interface for document upload and querying
- **Persistent Storage**: Saves vector index locally for fast subsequent queries

## Project Structure

```
Users/santhosh/Documents/Projects/RAG/
├── data/policies/           # Folder containing DOC PDF files
├── index/faiss_index/       # Folder to store FAISS vector database
├── main.py                  # Core RAG pipeline script
├── utils.py                 # Utility functions for PDF loading and chunking
├── vector_store.py          # FAISS setup and retrieval logic
├── streamlit_app.py         # Streamlit web interface
├── .env                     # Contains API keys
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/DOC_Policy_Copilot.git
cd DOC_Policy_Copilot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit the `.env` file and add your Gemini API key:
```bash
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

⚠️ **IMPORTANT**: Never commit your `.env` file to Git. It's already excluded in `.gitignore`.

### 4. Add Policy Documents

Place your Missouri DOC policy PDF files in the `data/policies/` folder. The system will automatically index them on startup.

Currently loaded documents:
- EmployeeHandbook.pdf
- Family_Friends_Handbook.pdf
- offender-rulebook.pdf
- RulesofReleases.pdf

### 4. Run the Application

#### Option A: Streamlit Web Interface (Recommended)
```bash
# For automatic document loading from fixed folder
streamlit run app_no_upload.py

# Or use the startup script
./run_fixed_docs.sh
```

Then open your browser to `http://localhost:8501`

#### Option B: Command Line Interface
```bash
python main.py
```

## Usage

### Web Interface

1. **Upload Documents**: Use the sidebar to upload PDF files
2. **Ask Questions**: Type your policy-related questions in the main interface
3. **Review Answers**: Get comprehensive answers with source citations
4. **Manage Index**: View statistics and reindex documents as needed

### Command Line

1. Place PDF files in `data/policies/`
2. Run `python main.py` to start the interactive session
3. Type your questions when prompted
4. Type 'quit' to exit

## Key Components

### Document Processing (`utils.py`)
- **PDF Loading**: Extracts text from PDF files using PyMuPDF
- **Text Chunking**: Splits documents into overlapping chunks for better retrieval
- **Metadata Preservation**: Maintains file names, page numbers, and source information

### Vector Storage (`vector_store.py`)
- **Embedding Generation**: Uses Gemini's embedding-001 model
- **FAISS Index**: Efficient vector similarity search
- **Persistent Storage**: Saves and loads indexes from disk
- **Incremental Updates**: Add new documents without full reindexing

### RAG Pipeline (`main.py`)
- **Query Processing**: Converts user questions to embeddings
- **Document Retrieval**: Finds most relevant document chunks
- **Response Generation**: Uses Gemini Pro to generate grounded answers
- **Citation Management**: Tracks and displays document sources

### Web Interface (`streamlit_app.py`)
- **File Upload**: Drag-and-drop PDF upload
- **Chat Interface**: Conversational Q&A experience
- **Source Display**: Shows document citations with similarity scores
- **Index Management**: Real-time statistics and maintenance options

## Configuration Options

### Chunking Parameters
- `chunk_size`: Number of tokens per chunk (default: 500)
- `overlap`: Token overlap between chunks (default: 50)

### Retrieval Parameters
- `top_k`: Number of relevant chunks to retrieve (default: 5)

### Model Configuration
- **Embedding Model**: `models/embedding-001`
- **Generation Model**: `gemini-pro`

## Sample Questions

- "What are the visiting hours and procedures?"
- "How are disciplinary actions handled?"
- "What are the requirements for inmate work programs?"
- "What is the policy on medical care for inmates?"
- "How are grievances processed?"
- "What are the security classification procedures?"

## Technical Details

### Dependencies
- **langchain**: Document processing and text manipulation
- **faiss-cpu**: Vector similarity search
- **streamlit**: Web interface
- **python-dotenv**: Environment variable management
- **PyMuPDF**: PDF text extraction
- **google-generativeai**: Gemini API integration

### Vector Store
- **Index Type**: FAISS IndexFlatIP (Inner Product for cosine similarity)
- **Embedding Dimension**: 768 (Gemini embedding-001)
- **Normalization**: L2 normalization for cosine similarity
- **Storage**: Local filesystem (`index/faiss_index/`)

### Security Considerations
- API keys stored in environment variables
- Local file processing (no external data transmission beyond API calls)
- Input validation for uploaded files
- Error handling for API failures

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Gemini API key is correctly set in `.env`
2. **PDF Processing Error**: Check that PDF files are not password-protected
3. **Memory Issues**: For large document collections, consider reducing chunk size
4. **Index Corruption**: Use the "Reindex All Documents" button to rebuild

### Performance Tips

- Use smaller chunk sizes for better precision
- Increase overlap for better context continuity
- Upload related documents together for comprehensive coverage
- Regular reindexing for optimal performance

## Development

### Adding New Features
1. Extend the `RAGPipeline` class in `main.py`
2. Add new utility functions in `utils.py`
3. Update the Streamlit interface in `streamlit_app.py`

### Testing
- Test with various PDF formats and sizes
- Verify chunking produces meaningful segments
- Validate citation accuracy
- Check response quality with different question types

## License

This project is designed for internal use with Missouri Department of Corrections policy documents. Ensure compliance with relevant data handling and privacy policies.
