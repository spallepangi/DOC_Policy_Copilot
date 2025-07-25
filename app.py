import streamlit as st
import os
import tempfile
from typing import List
import time
import traceback

# Try to import with fallbacks
try:
    from main import RAGPipeline
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Missouri DOC Policy Copilot",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 5px solid #2196f3;
    }
    .bot-message {
        background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%);
        border-left: 5px solid #4caf50;
    }
    .source-item {
        background-color: #f5f5f5;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        transition: all 0.3s ease;
    }
    .source-item:hover {
        background-color: #eeeeee;
        transform: translateX(5px);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .stAlert > div {
        padding: 1rem;
        border-radius: 10px;
    }
    .upload-section {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_rag_pipeline():
    """Initialize the RAG pipeline with caching."""
    try:
        return RAGPipeline()
    except Exception as e:
        st.error(f"Failed to initialize RAG pipeline: {str(e)}")
        st.error("Please check your API key and dependencies.")
        return None

def save_uploaded_file(uploaded_file, destination_folder: str) -> str:
    """Save uploaded file to destination folder."""
    try:
        os.makedirs(destination_folder, exist_ok=True)
        file_path = os.path.join(destination_folder, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        return file_path
    except Exception as e:
        st.error(f"Error saving file {uploaded_file.name}: {str(e)}")
        return None

def display_sources(sources: List[dict]):
    """Display source information in a formatted way."""
    if not sources:
        return
    
    st.markdown("### 📚 Sources Used")
    for i, source in enumerate(sources, 1):
        with st.expander(f"📄 Source {i}: {source['filename']} (Page {source['page_number']})", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**📁 File:** {source['filename']}")
                st.markdown(f"**📃 Page:** {source['page_number']}")
            with col2:
                st.markdown(f"**🎯 Relevance:** {source['similarity_score']}")
                relevance_percent = int(source['similarity_score'] * 100)
                st.progress(relevance_percent / 100)

def create_sample_pdf():
    """Create a sample PDF for demonstration purposes."""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open()
        page = doc.new_page()
        
        sample_text = """
Missouri Department of Corrections
Policy Manual - Sample Document

VISITING PROCEDURES

1. General Guidelines:
   - Visiting hours are from 9:00 AM to 3:00 PM on weekends
   - All visitors must present valid photo identification
   - Maximum of 3 visitors per inmate per visit
   
2. Security Procedures:
   - All visitors subject to search
   - No personal items allowed in visiting area
   - Cell phones must be secured in lockers
   
3. Disciplinary Actions:
   - Minor infractions result in verbal warnings
   - Major infractions may result in loss of privileges
   - All disciplinary actions are documented
   
4. Medical Care:
   - 24/7 medical staff availability
   - Emergency medical procedures in place
   - Regular health screenings conducted
        """
        
        # Insert text into the PDF
        page.insert_text((50, 50), sample_text, fontsize=11)
        
        # Save to the policies folder
        os.makedirs("data/policies", exist_ok=True)
        sample_path = "data/policies/sample_policy.pdf"
        doc.save(sample_path)
        doc.close()
        
        return sample_path
    except Exception as e:
        st.error(f"Error creating sample PDF: {str(e)}")
        return None

def main():
    # Header with enhanced styling
    st.markdown('<h1 class="main-header">🏛️ Missouri DOC Policy Copilot</h1>', unsafe_allow_html=True)
    
    # Subtitle
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem; color: #666;'>
        <h3>AI-Powered Assistant for Missouri Department of Corrections Policies</h3>
        <p>Ask questions about DOC policies and get accurate answers with source citations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize RAG pipeline
    rag = initialize_rag_pipeline()
    
    if rag is None:
        st.error("Failed to initialize the application. Please check the logs above.")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📁 Document Management")
        
        # Quick start section
        with st.expander("🚀 Quick Start Guide", expanded=True):
            st.markdown("""
            **New to the system?**
            1. Upload your first PDF document below
            2. Wait for processing to complete
            3. Ask questions in the main chat area
            4. Review answers with source citations
            
            **Need a demo?** Click 'Create Sample PDF' to get started!
            """)
            
            if st.button("🎯 Create Sample PDF", help="Creates a sample Missouri DOC policy document"):
                with st.spinner("Creating sample document..."):
                    sample_path = create_sample_pdf()
                    if sample_path:
                        st.success("✅ Sample PDF created! It will be automatically indexed.")
                        st.rerun()
        
        # Upload section with enhanced UI
        st.markdown("### 📤 Upload New Documents")
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload Missouri DOC policy documents in PDF format"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.info(f"📄 {len(uploaded_files)} file(s) selected for upload")
            
            if st.button("🔄 Process Uploaded Files", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    saved_files = []
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing {uploaded_file.name}...")
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        
                        file_path = save_uploaded_file(uploaded_file, "data/policies/")
                        if file_path:
                            saved_files.append(file_path)
                    
                    if saved_files:
                        status_text.text("Adding documents to search index...")
                        rag.add_new_documents(saved_files)
                        
                        st.success(f"✅ Successfully processed {len(saved_files)} files!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
                    st.error("Please try again or check the file format.")
        
        # Index statistics with enhanced display
        st.markdown("### 📊 Knowledge Base Stats")
        stats = rag.get_index_stats()
        
        if stats['total_documents'] > 0:
            # Create metric cards
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📚 Documents", stats['total_documents'], help="Total number of document chunks indexed")
            with col2:
                st.metric("🗂️ Files", stats['unique_files'], help="Number of unique PDF files")
            
            st.metric("🔍 Search Chunks", stats['total_chunks'], help="Total searchable text chunks")
            
            with st.expander("📋 View Indexed Files"):
                for i, filename in enumerate(stats['files'], 1):
                    st.markdown(f"**{i}.** {filename}")
        else:
            st.info("📝 No documents indexed yet. Upload some PDF files to get started!")
        
        # Maintenance section
        st.markdown("### 🔧 Maintenance")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reindex All", help="Rebuild the entire search index"):
                with st.spinner("Reindexing all documents..."):
                    try:
                        rag.index_documents()
                        st.success("✅ Reindexing completed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Reindexing failed: {str(e)}")
        
        with col2:
            if st.button("🗑️ Clear History", help="Clear chat conversation history"):
                st.session_state.chat_history = []
                st.success("🧹 History cleared!")
                st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 💬 Ask Questions")
        
        # Initialize session state for chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Query input with enhanced form
        with st.form("query_form", clear_on_submit=True):
            query = st.text_area(
                "💭 Enter your question about Missouri DOC policies:",
                height=100,
                placeholder="Example: What are the procedures for inmate disciplinary hearings?",
                help="Be specific for better results. Ask about procedures, regulations, guidelines, etc."
            )
            
            col_submit, col_advanced = st.columns([2, 1])
            with col_submit:
                submit_button = st.form_submit_button("🚀 Ask Question", type="primary", use_container_width=True)
            with col_advanced:
                advanced_search = st.form_submit_button("🔍 Advanced", help="Coming soon: Advanced search options")
        
        # Handle query submission
        if submit_button and query.strip():
            if stats['total_documents'] == 0:
                st.error("📚 Please upload some PDF documents first before asking questions.")
            else:
                # Add user question to history
                st.session_state.chat_history.append({
                    "type": "user",
                    "content": query,
                    "timestamp": time.time()
                })
                
                # Get response with progress indicators
                with st.spinner("🔍 Searching policy documents and generating response..."):
                    try:
                        result = rag.generate_response(query)
                        
                        # Add bot response to history
                        st.session_state.chat_history.append({
                            "type": "bot",
                            "content": result,
                            "timestamp": time.time()
                        })
                    except Exception as e:
                        st.error(f"❌ Error generating response: {str(e)}")
                        st.error("Please try rephrasing your question or check your API key.")
                
                st.rerun()
        
        # Display chat history with enhanced styling
        if st.session_state.chat_history:
            st.markdown("## 💭 Conversation History")
            
            for i, message in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10 messages
                if message["type"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <strong>🙋‍♂️ You asked:</strong>
                            <small style="margin-left: auto; color: #666;">
                                {time.strftime('%H:%M', time.localtime(message['timestamp']))}
                            </small>
                        </div>
                        <div>{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                elif message["type"] == "bot":
                    result = message["content"]
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <strong>🏛️ Missouri DOC Policy Copilot:</strong>
                            <small style="margin-left: auto; color: #666;">
                                {time.strftime('%H:%M', time.localtime(message['timestamp']))}
                            </small>
                        </div>
                        <div>{result["answer"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display sources
                    if result["sources"]:
                        display_sources(result["sources"])
                    
                    # Add separator
                    if i < len(st.session_state.chat_history) - 1:
                        st.markdown("---")
    
    with col2:
        # How to use section
        st.markdown("## ℹ️ How to Use")
        with st.expander("📖 User Guide", expanded=True):
            st.markdown("""
            **Getting Started:**
            1. 📤 **Upload Documents**: Use the sidebar to upload Missouri DOC policy PDF files
            2. ⏳ **Wait for Processing**: Files are automatically indexed for search
            3. 💬 **Ask Questions**: Type policy-related questions in the text area
            4. 📚 **Review Answers**: Get comprehensive answers with source citations
            
            **💡 Tips for Better Results:**
            - Be specific in your questions
            - Ask about procedures, regulations, and guidelines
            - Check the sources provided to verify information
            - Upload multiple related documents for comprehensive coverage
            """)
        
        # Sample questions section
        st.markdown("## 🎯 Sample Questions")
        sample_questions = [
            "What are the visiting hours and procedures?",
            "How are disciplinary actions handled?",
            "What are the requirements for inmate work programs?",
            "What is the policy on medical care for inmates?",
            "How are grievances processed?",
            "What are the security classification procedures?",
            "What are the rules for inmate phone calls?",
            "How is mail handling conducted?"
        ]
        
        for question in sample_questions:
            if st.button(f"💭 {question}", key=f"sample_{hash(question)}", use_container_width=True):
                if stats['total_documents'] == 0:
                    st.error("📚 Please upload some PDF documents first.")
                else:
                    # Add to chat history and get response
                    st.session_state.chat_history.append({
                        "type": "user",
                        "content": question,
                        "timestamp": time.time()
                    })
                    
                    with st.spinner("🔍 Generating response..."):
                        try:
                            result = rag.generate_response(question)
                            
                            st.session_state.chat_history.append({
                                "type": "bot",
                                "content": result,
                                "timestamp": time.time()
                            })
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    
                    st.rerun()
        
        # System status
        st.markdown("## 🔧 System Status")
        with st.expander("📊 System Info"):
            st.markdown(f"""
            **Application Status:** ✅ Running  
            **API Connection:** ✅ Connected  
            **Documents Indexed:** {stats['total_documents']}  
            **Files Available:** {stats['unique_files']}  
            **Last Updated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
            """)

if __name__ == "__main__":
    main()
