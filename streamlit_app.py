import streamlit as st
import os
import time
from typing import List

# Try to import with fallbacks
try:
    from main import RAGPipeline
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Check for API key
if not os.getenv('GEMINI_API_KEY'):
    st.error("""
    ## 🔑 API Key Missing
    
    Please set up your Gemini API key:
    
    1. Copy `.env.example` to `.env`
    2. Edit `.env` and add your Gemini API key
    3. Get your API key from: https://makersuite.google.com/app/apikey
    4. Restart the application
    
    Your `.env` file should contain:
    ```
    GEMINI_API_KEY=your_actual_api_key_here
    ```
    """)
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
    .document-list {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
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

# Sources display function removed - no longer showing sources to users

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
    with st.spinner("🔄 Initializing system and loading policy documents..."):
        rag = initialize_rag_pipeline()
    
    if rag is None:
        st.error("Failed to initialize the application. Please check the logs above.")
        st.stop()
    
    # Get stats
    stats = rag.get_index_stats()
    
    # Sidebar
    with st.sidebar:
        # System status - simplified
        if stats['total_documents'] > 0:
            st.success("✅ System Ready")
            st.markdown(f"**📚 {stats['total_documents']} documents loaded**")
        else:
            st.error("❌ No policy documents found!")
            st.markdown("""
            **Expected Location:** `data/policies/`
            
            Please ensure PDF files are present in this folder and restart the application.
            """)
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### 🛠️ Quick Actions")
        if st.button("🔄 Refresh Index", help="Rebuild the search index from policy documents", use_container_width=True):
            with st.spinner("Rebuilding search index..."):
                try:
                    rag.index_documents()
                    st.success("✅ Index refreshed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Refresh failed: {str(e)}")
        if st.button("🗑️ Clear Chat History", help="Clear conversation history"):
            st.session_state.chat_history = []
            st.success("🧹 Chat history cleared!")
            st.rerun()
    
    # Main content area
    if stats['total_documents'] == 0:
        st.error("""
        ## ⚠️ No Policy Documents Available
        
        The system cannot find any PDF documents in the policy directory:
        `data/policies/`
        
        Please:
        1. Add PDF files to the above directory
        2. Restart the application
        3. The system will automatically index the documents
        """)
        st.stop()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 💬 Ask Questions About DOC Policies")
        
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
            
            col_submit, col_clear = st.columns([2, 1])
            with col_submit:
                submit_button = st.form_submit_button("🚀 Ask Question", type="primary", use_container_width=True)
            with col_clear:
                clear_history = st.form_submit_button("🗑️ Clear History", help="Clear conversation history")
        
        # Handle form button submissions
        if clear_history:
            st.session_state.chat_history = []
            st.success("🧹 Chat history cleared!")
            st.rerun()
        
        elif submit_button and query.strip():
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
            st.markdown("## 💬 Conversation")
            
            # Iterate through the history and display messages chronologically
            for message in st.session_state.chat_history:
                if message.get('type') == 'user':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <strong>🙋‍♂️ You asked:</strong>
                            <small style="margin-left: auto; color: #666;">
                                {time.strftime('%H:%M', time.localtime(message.get('timestamp', 0)))}
                            </small>
                        </div>
                        <div>{message.get('content', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif message.get('type') == 'bot':
                    result = message.get('content', {})
                    answer = result.get('answer', 'No answer available') if isinstance(result, dict) else str(result)
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <strong>🏛️ Answer:</strong>
                            <small style="margin-left: auto; color: #666;">
                                {time.strftime('%H:%M', time.localtime(message.get('timestamp', 0)))}
                            </small>
                        </div>
                        <div>{answer}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        # Tips section
        st.markdown("## 💡 Tips for Better Answers")
        st.markdown("""
        - **Be specific** in your questions
        - Ask about **procedures and guidelines**
        - Use **keywords** from policy topics
        - Try **different phrasings** if needed
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
            "How is mail handling conducted?",
            "What are the employee handbook guidelines?",
            "What are the rules for family and friends visiting?"
        ]
        
        for question in sample_questions:
            if st.button(f"💭 {question}", key=f"sample_{hash(question)}", use_container_width=True):
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

if __name__ == "__main__":
    main()
