import os
from typing import List, Dict, Any, Tuple
import cohere
from utils import extract_images_from_pdf
import google.generativeai as genai
from dotenv import load_dotenv
import re

from utils import load_pdf_files, chunk_documents, clean_text
from vector_store_stable import StableVectorStore
from prompts.base_prompt import BASE_PROMPT
from prompts.query_rewrite import QUERY_REWRITE_PROMPT, QUERY_ANALYSIS_PROMPT
from prompts.fallback import FALLBACK_PROMPT, NO_CONTEXT_FALLBACK, LOW_CONFIDENCE_RESPONSE
from evaluation import log_evaluation_data

# Try to import config, use defaults if not available
try:
    import config
except ImportError:
    # Fallback configuration if config module is not available
    class config:
        CHUNK_SIZE = 500
        CHUNK_OVERLAP = 20
        TOP_K_RETRIEVAL = 10
        TOP_K_RERANKED = 3
        SIMILARITY_THRESHOLD = 0.3
        ENABLE_QUERY_REWRITING = True
        ENABLE_EVALUATION_LOGGING = True
        LOG_FILE_PATH = "logs/rag_evaluation.log"
        GEMINI_MODEL = "gemini-2.0-flash"
        EMBEDDING_MODEL = "models/embedding-001"
        MAX_CONTEXT_LENGTH = 4000
        HALLUCINATION_DETECTION_THRESHOLD = 0.5

# Load environment variables
load_dotenv()

class RAGPipeline:
    def __init__(self, data_folder: str = "data/policies/", index_path: str = "index/faiss_index/"):
        """
        Initialize the enhanced RAG pipeline with query rewriting, semantic reranking, and evaluation.
        
        Args:
            data_folder (str): Path to folder containing PDF files
            index_path (str): Path to store FAISS index
        """
        self.data_folder = data_folder
        self.vector_store = StableVectorStore(index_path)
        
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Create necessary directories
        os.makedirs(data_folder, exist_ok=True)
        os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)
        
        # Auto-load and index documents if index is empty
        self._auto_initialize()
    
    def index_documents(self, chunk_size: int = None, overlap: int = None):
        """
        Load, process, and index all PDF documents (text and images) using settings from config.
        
        Args:
            chunk_size (int): Size of text chunks (tokens), defaults to config
            overlap (int): Overlap between chunks (tokens), defaults to config
        """
        # Use config defaults if not provided
        if chunk_size is None:
            chunk_size = config.CHUNK_SIZE
        if overlap is None:
            overlap = config.CHUNK_OVERLAP
            
        print("Loading PDF documents...")
        text_documents = load_pdf_files(self.data_folder)
        
        if not text_documents:
            print("No PDF documents found.")
            return
        
        print(f"Loaded {len(text_documents)} pages from PDF files.")
        
        # Clean text content
        for doc in text_documents:
            doc['text'] = clean_text(doc['text'])
            doc['type'] = 'text'  # Mark as text document
        
        # Chunk text documents using LangChain
        print("Chunking text documents with RecursiveCharacterTextSplitter...")
        chunked_text_docs = chunk_documents(text_documents, chunk_size, overlap)
        for doc in chunked_text_docs:
            doc['type'] = 'text'
        print(f"Created {len(chunked_text_docs)} text chunks.")
        
        # Extract images from PDFs
        print("Extracting images from PDF documents...")
        image_documents = extract_images_from_pdf(self.data_folder)
        for doc in image_documents:
            doc['type'] = 'image'  # Ensure type is set
        print(f"Extracted {len(image_documents)} images.")
        
        # Combine text and image documents
        all_documents = chunked_text_docs + image_documents
        print(f"Total documents to index: {len(all_documents)} ({len(chunked_text_docs)} text + {len(image_documents)} images)")
        
        # Create multimodal vector index
        self.vector_store.create_index(all_documents)
        
        print("Multimodal document indexing completed!")
    
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
    
    def generate_response(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Generate a response to a user query using enhanced RAG with query rewriting, semantic reranking, and evaluation.
        
        Args:
            query (str): User question
            top_k (int): Number of relevant chunks to retrieve (defaults to config)
            
        Returns:
            Dict: Response with answer and sources
        """
        # Use config defaults if not provided
        if top_k is None:
            top_k = config.TOP_K_RETRIEVAL
            
        # Step 1: Query rewriting if enabled
        original_query = query
        if config.ENABLE_QUERY_REWRITING:
            rewritten_query = self._rewrite_query(query)
            if rewritten_query and rewritten_query.strip() != query.strip():
                print(f"Query rewritten: '{query}' -> '{rewritten_query}'")
                query = rewritten_query
        
        # Step 2: Initial retrieval from FAISS
        search_results = self.vector_store.search(query, k=top_k)
        
        if not search_results:
            fallback_answer = NO_CONTEXT_FALLBACK.replace("{{query}}", original_query)
            return {
                "answer": fallback_answer,
                "sources": [],
                "query": original_query,
                "rewritten_query": query if query != original_query else None
            }
        
        # Step 3: Process retrieved chunks (simplified for testing)
        retrieved_chunks = [doc for doc, score in search_results]
        similarity_scores = [score for doc, score in search_results]
        
        # Check if similarity scores are too low
        if max(similarity_scores) < config.SIMILARITY_THRESHOLD:
            print(f"Low similarity detected. Max score: {max(similarity_scores)}")
            return self._generate_fallback_response(original_query, retrieved_chunks[:3], similarity_scores[:3])
        
        # Use top retrieved chunks directly (bypassing semantic reranking for testing)
        top_reranked = retrieved_chunks[:config.TOP_K_RERANKED]
        reranker_scores = [0.0] * len(top_reranked)  # Placeholder scores
        
        # Step 4: Generate response
        context_parts = []
        sources = []
        
        for i, doc in enumerate(top_reranked):
            # Handle different types of documents
            if doc.get('type') == 'text':
                context_parts.append(f"From {doc['source']}:\n{doc['text']}")
            elif doc.get('type') == 'image':
                context_parts.append(f"From {doc['source']} (Image):\n{doc.get('caption', 'Image from policy document')}")
            else:
                # Fallback for documents without type specified (backwards compatibility)
                if 'text' in doc:
                    context_parts.append(f"From {doc['source']}:\n{doc['text']}")
            
            # Track unique sources with type information
            source_info = {
                "filename": doc['filename'],
                "page_number": doc['page_number'],
                "source": doc['source'],
                "type": doc.get('type', 'text'),
                "similarity_score": round(similarity_scores[retrieved_chunks.index(doc)], 3),
                "reranker_score": round(reranker_scores[i], 3) if i < len(reranker_scores) else 0.0
            }
            
            # Add image-specific data if it's an image
            if doc.get('type') == 'image':
                source_info['base64_data'] = doc.get('base64_data', '')
                source_info['caption'] = doc.get('caption', 'Image from policy document')
                source_info['dimensions'] = doc.get('dimensions', (0, 0))
            
            # Avoid duplicate sources
            if source_info not in sources:
                sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        # Truncate context if too long
        if len(context) > config.MAX_CONTEXT_LENGTH:
            context = context[:config.MAX_CONTEXT_LENGTH] + "\n[Context truncated...]"
        
        # Create prompt using modular prompt system
        prompt = BASE_PROMPT.replace("{{context}}", context).replace("{{query}}", original_query)
        
        # Generate response using Gemini
        try:
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            answer = "I apologize, but I encountered an error while generating a response. Please try again."
        
        # Step 5: Log evaluation data
        if config.ENABLE_EVALUATION_LOGGING:
            log_evaluation_data(
                query=original_query,
                retrieved_chunks=retrieved_chunks,
                reranked_chunks=top_reranked,
                response=answer,
                similarity_scores=similarity_scores,
                reranker_scores=reranker_scores[:config.TOP_K_RERANKED]
            )
        
        return {
            "answer": answer,
            "sources": sources,
            "query": original_query,
            "rewritten_query": query if query != original_query else None,
            "context_used": len(top_reranked)
        }
    
    def _rewrite_query(self, query: str) -> str:
        """Rewrites a user query to be more specific and clear for retrieval."""
        try:
            prompt = QUERY_REWRITE_PROMPT.replace("{{query}}", query)
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error during query rewriting: {e}")
            return query

    def _semantic_rerank(self, query: str, chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Reranks retrieved chunks based on semantic relevance to the query."""
        try:
            # This is a simplified example of reranking.
            # A more advanced implementation would use a dedicated reranker model.
            reranker_prompt = "Please re-rank the following document chunks based on their relevance to the query: '{query}'. Return a comma-separated list of the original chunk indices, from most to least relevant."
            reranker_prompt = reranker_prompt.replace("{query}", query)

            for i, chunk in enumerate(chunks):
                reranker_prompt += f"\n\n[Chunk {i}]: {chunk['text']}"

            model = genai.GenerativeModel(config.GEMINI_MODEL)
            response = model.generate_content(reranker_prompt)
            
            # Extract ranked indices from response
            ranked_indices_str = re.findall(r"\d+", response.text)
            ranked_indices = [int(i) for i in ranked_indices_str if int(i) < len(chunks)]
            
            # Create a new list of chunks and scores based on the new order
            reranked_chunks = [chunks[i] for i in ranked_indices]
            reranker_scores = [(len(chunks) - i) / len(chunks) for i in range(len(chunks))]  # Example scores
            
            return reranked_chunks, reranker_scores

        except Exception as e:
            print(f"Error during semantic reranking: {e}")
            # Fallback to original order
            return chunks, [0.0] * len(chunks)

    def _generate_fallback_response(self, query: str, context_chunks: list, scores: list) -> Dict[str, Any]:
        """Generates a fallback response when no high-confidence context is found."""
        try:
            context = "\n".join([chunk["text"] for chunk in context_chunks])
            prompt = FALLBACK_PROMPT.replace("{{query}}", query).replace("{{context}}", context)
            
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            response = model.generate_content(prompt)
            answer = response.text

        except Exception as e:
            print(f"Error generating fallback response: {e}")
            answer = LOW_CONFIDENCE_RESPONSE.replace("{{query}}", query).replace("{{partial_info}}", "I found some information that might be related, but I cannot be certain.")

        return {
            "answer": answer,
            "sources": [],
            "query": query
        }
    
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




