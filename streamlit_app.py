import streamlit as st
import os
import tempfile
from typing import List
import time

from main import RAGPipeline

# Page configuration
st.set_page_config(
    page_title="Missouri DOC Policy Copilot",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .source-item {
        background-color: #f5f5f5;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        border-left: 3px solid #ff9800;
    }
    .stAlert > div {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_rag_pipeline():
    """Initialize the RAG pipeline with caching."""
    return RAGPipeline()

def save_uploaded_file(uploaded_file, destination_folder: str) -> str:
    """Save uploaded file to destination folder."""
    os.makedirs(destination_folder, exist_ok=True)
    file_path = os.path.join(destination_folder, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return file_path

def display_sources(sources: List[dict]):
    """Display source information in a formatted way."""
    if not sources:
        return
    
    st.markdown("### 📚 Sources")
    for i, source in enumerate(sources, 1):
        with st.expander(f"Source {i}: {source['filename']} (Page {source['page_number']})"):
            st.markdown(f"**File:** {source['filename']}")
            st.markdown(f"**Page:** {source['page_number']}")
            st.markdown(f"**Similarity Score:** {source['similarity_score']}")

def main():
    # Header
    st.markdown('<h1 class="main-header">🏛️ Missouri DOC Policy Copilot</h1>', unsafe_allow_html=True)
    st.markdown("Ask questions about Missouri Department of Corrections policies and get answers with document citations.")
    
    # Initialize RAG pipeline
    rag = initialize_rag_pipeline()
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Document Management")
        
        # Upload section
        st.subheader("Upload New Documents")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload Missouri DOC policy documents in PDF format"
        )
        
        if uploaded_files:
            if st.button("Process Uploaded Files", type="primary"):
                with st.spinner("Processing uploaded files..."):
                    saved_files = []
                    
                    for uploaded_file in uploaded_files:
                        file_path = save_uploaded_file(uploaded_file, "data/policies/")
                        saved_files.append(file_path)
                    
                    # Add to index
                    rag.add_new_documents(saved_files)
                    
                    st.success(f"Successfully processed {len(saved_files)} files!")
                    st.rerun()
        
        # Index information
        st.subheader("📊 Index Statistics")
        stats = rag.get_index_stats()
        
        if stats['total_documents'] > 0:
            st.metric("Total Documents", stats['total_documents'])
            st.metric("Total Chunks", stats['total_chunks'])
            st.metric("Unique Files", stats['unique_files'])
            
            with st.expander("View Indexed Files"):
                for filename in stats['files']:
                    st.text(f"• {filename}")
        else:
            st.info("No documents indexed yet. Upload some PDF files to get started!")
        
        # Reindex option
        st.subheader("🔄 Maintenance")
        if st.button("Reindex All Documents"):
            with st.spinner("Reindexing all documents..."):
                rag.index_documents()
                st.success("Reindexing completed!")
                st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask a Question")
        
        # Initialize session state for chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Query input
        with st.form("query_form"):
            query = st.text_area(
                "Enter your question about Missouri DOC policies:",
                height=100,
                placeholder="Example: What are the procedures for inmate disciplinary hearings?"
            )
            
            col_submit, col_clear = st.columns([1, 1])
            with col_submit:
                submit_button = st.form_submit_button("Submit Question", type="primary")
            with col_clear:
                clear_button = st.form_submit_button("Clear History")
        
        # Handle clear history
        if clear_button:
            st.session_state.chat_history = []
            st.rerun()
        
        # Handle query submission
        if submit_button and query.strip():
            if stats['total_documents'] == 0:
                st.error("Please upload some PDF documents first before asking questions.")
            else:
                # Add user question to history
                st.session_state.chat_history.append({
                    "type": "user",
                    "content": query,
                    "timestamp": time.time()
                })
                
                # Get response
                with st.spinner("Searching policy documents and generating response..."):
                    result = rag.generate_response(query)
                
                # Add bot response to history
                st.session_state.chat_history.append({
                    "type": "bot",
                    "content": result,
                    "timestamp": time.time()
                })
                
                st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            st.header("💭 Conversation")
            
            for message in st.session_state.chat_history:
                if message["type"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                
                elif message["type"] == "bot":
                    result = message["content"]
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>Missouri DOC Policy Copilot:</strong><br>
                        {result["answer"]}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display sources
                    if result["sources"]:
                        display_sources(result["sources"])
    
    with col2:
        st.header("ℹ️ How to Use")
        st.markdown("""
        **Steps:**
        1. **Upload Documents**: Use the sidebar to upload Missouri DOC policy PDF files
        2. **Wait for Processing**: Files will be automatically indexed for search
        3. **Ask Questions**: Type your policy-related questions in the text area
        4. **Review Answers**: Get comprehensive answers with source citations
        
        **Tips:**
        - Be specific in your questions for better results
        - Questions about procedures, regulations, and guidelines work best
        - Check the sources provided to verify information
        - Upload multiple related documents for comprehensive coverage
        """)
        
        st.header("🎯 Sample Questions")
        sample_questions = [
            "What are the visiting hours and procedures?",
            "How are disciplinary actions handled?",
            "What are the requirements for inmate work programs?",
            "What is the policy on medical care for inmates?",
            "How are grievances processed?",
            "What are the security classification procedures?"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{hash(question)}"):
                if stats['total_documents'] == 0:
                    st.error("Please upload some PDF documents first.")
                else:
                    # Add to chat history and get response
                    st.session_state.chat_history.append({
                        "type": "user",
                        "content": question,
                        "timestamp": time.time()
                    })
                    
                    with st.spinner("Generating response..."):
                        result = rag.generate_response(question)
                    
                    st.session_state.chat_history.append({
                        "type": "bot",
                        "content": result,
                        "timestamp": time.time()
                    })
                    
                    st.rerun()

if __name__ == "__main__":
    main()
