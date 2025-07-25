import os
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

from utils import load_pdf_files, chunk_documents, clean_text
from vector_store import VectorStore

# Load environment variables
load_dotenv()

class RAGPipeline:
    def __init__(self, data_folder: str = "data/policies/", index_path: str = "index/faiss_index/"):
        """
        Initialize the RAG pipeline.
        
        Args:
            data_folder (str): Path to folder containing PDF files
            index_path (str): Path to store FAISS index
        """
        self.data_folder = data_folder
        self.vector_store = VectorStore(index_path)
        
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Create data folder if it doesn't exist
        os.makedirs(data_folder, exist_ok=True)
        
        # Auto-load and index documents if index is empty
        self._auto_initialize()
    
    def index_documents(self, chunk_size: int = 500, overlap: int = 50):
        """
        Load, process, and index all PDF documents.
        
        Args:
            chunk_size (int): Size of text chunks
            overlap (int): Overlap between chunks
        """
        print("Loading PDF documents...")
        documents = load_pdf_files(self.data_folder)
        
        if not documents:
            print("No PDF documents found.")
            return
        
        print(f"Loaded {len(documents)} pages from PDF files.")
        
        # Clean text content
        for doc in documents:
            doc['text'] = clean_text(doc['text'])
        
        # Chunk documents
        print("Chunking documents...")
        chunked_docs = chunk_documents(documents, chunk_size, overlap)
        print(f"Created {len(chunked_docs)} chunks.")
        
        # Create vector index
        self.vector_store.create_index(chunked_docs)
        
        print("Document indexing completed!")
    
    def add_new_documents(self, pdf_paths: List[str], chunk_size: int = 500, overlap: int = 50):
        """
        Add new PDF documents to existing index.
        
        Args:
            pdf_paths (List[str]): List of paths to new PDF files
            chunk_size (int): Size of text chunks
            overlap (int): Overlap between chunks
        """
        new_documents = []
        
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
                # Load single PDF
                folder_path = os.path.dirname(pdf_path)
                filename = os.path.basename(pdf_path)
                
                # Only copy if the file is not already in the data folder
                if folder_path != os.path.abspath(self.data_folder):
                    import shutil
                    dest_path = os.path.join(self.data_folder, filename)
                    # Check if destination file already exists and is the same
                    if not os.path.exists(dest_path) or not os.path.samefile(pdf_path, dest_path):
                        shutil.copy2(pdf_path, dest_path)
                
                # Load the document
                docs = load_pdf_files(self.data_folder)
                # Filter for just the new document
                docs = [doc for doc in docs if doc['filename'] == filename]
                new_documents.extend(docs)
        
        if not new_documents:
            print("No new documents to add.")
            return
        
        # Clean text content
        for doc in new_documents:
            doc['text'] = clean_text(doc['text'])
        
        # Chunk documents
        chunked_docs = chunk_documents(new_documents, chunk_size, overlap)
        
        # Add to vector store
        self.vector_store.add_documents(chunked_docs)
        
        print(f"Added {len(chunked_docs)} new chunks to the index.")
    
    def generate_response(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Generate a response to a user query using RAG.
        
        Args:
            query (str): User question
            top_k (int): Number of relevant chunks to retrieve
            
        Returns:
            Dict: Response with answer and sources
        """
        # Search for relevant documents
        search_results = self.vector_store.search(query, k=top_k)
        
        if not search_results:
            return {
                "answer": "I'm sorry, I couldn't find any relevant information in the Missouri DOC policy documents to answer your question.",
                "sources": [],
                "query": query
            }
        
        # Prepare context from retrieved documents
        context_parts = []
        sources = []
        
        for doc, score in search_results:
            context_parts.append(f"From {doc['source']}:\\n{doc['text']}")
            
            # Track unique sources
            source_info = {
                "filename": doc['filename'],
                "page_number": doc['page_number'],
                "source": doc['source'],
                "similarity_score": round(score, 3)
            }
            
            # Avoid duplicate sources
            if source_info not in sources:
                sources.append(source_info)
        
        context = "\\n\\n".join(context_parts)
        
        # Create prompt for Gemini
        prompt = self._create_prompt(query, context)
        
        # Generate response using Gemini
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')  # Updated to available model
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            answer = "I apologize, but I encountered an error while generating a response. Please try again."
        
        return {
            "answer": answer,
            "sources": sources,
            "query": query,
            "context_used": len(search_results)
        }
    
    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create a prompt for the language model.
        
        Args:
            query (str): User question
            context (str): Retrieved context
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""You are a helpful assistant that explains Missouri Department of Corrections policies in simple, easy-to-understand language.

Based on the information provided below, answer the user's question in a conversational, human-friendly way.

IMPORTANT GUIDELINES:
1. Write in plain English that anyone can understand
2. Use a warm, conversational tone like you're explaining to a friend or family member
3. DO NOT include any document names, page numbers, or source citations in your response
4. Avoid technical jargon, policy codes, or formal bureaucratic language
5. Break down complex processes into simple, easy-to-follow steps
6. Use everyday words instead of official terminology
7. If the information isn't available, say so in a friendly way
8. Focus on what people actually need to know in practical terms

INFORMATION FROM POLICY DOCUMENTS:
{context}

USER QUESTION: {query}

Please provide a clear, friendly explanation without any document references or technical jargon:"""
        
        return prompt
    
    def _auto_initialize(self):
        """Auto-initialize the system by loading PDFs from the policies folder."""
        stats = self.vector_store.get_stats()
        
        # Check if we have an existing index
        if stats['total_documents'] > 0:
            print(f"Found existing index with {stats['total_documents']} documents.")
            return
        
        # Check if there are PDF files to load
        pdf_files = [f for f in os.listdir(self.data_folder) if f.lower().endswith('.pdf')]
        
        if pdf_files:
            print(f"Found {len(pdf_files)} PDF files. Auto-indexing...")
            print(f"Files found: {', '.join(pdf_files)}")
            self.index_documents()
        else:
            print(f"No PDF files found in {self.data_folder}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        return self.vector_store.get_stats()


def main():
    """Main function to demonstrate the RAG pipeline."""
    # Initialize pipeline
    rag = RAGPipeline()
    
    # Check if index exists
    stats = rag.get_index_stats()
    
    if stats['total_documents'] == 0:
        print("No existing index found. Please add some PDF documents to the data/policies/ folder and run indexing.")
        print("You can also use the Streamlit app to upload documents.")
    else:
        print(f"Loaded existing index with {stats['total_documents']} documents from {stats['unique_files']} files.")
        
        # Interactive query loop
        print("\\nMissouri DOC Policy Copilot - Ready for questions!")
        print("Type 'quit' to exit.")
        
        while True:
            query = input("\\nYour question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("\\nSearching for relevant information...")
            result = rag.generate_response(query)
            
            print(f"\\n**Answer:**\\n{result['answer']}")
            
            if result['sources']:
                print(f"\\n**Sources:**")
                for source in result['sources']:
                    print(f"- {source['source']} (Similarity: {source['similarity_score']})")


if __name__ == "__main__":
    main()
