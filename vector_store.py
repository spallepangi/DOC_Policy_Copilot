import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorStore:
    def __init__(self, index_path: str = "index/faiss_index/"):
        """
        Initialize the FAISS vector store.
        
        Args:
            index_path (str): Path to store the FAISS index
        """
        self.index_path = index_path
        self.index = None
        self.documents = []
        self.dimension = 768  # Gemini embedding dimension
        
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Create index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Load existing index if available
        self.load_index()
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using Gemini.
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            np.ndarray: Array of embeddings
        """
        embeddings = []
        
        for text in texts:
            try:
                # Use Gemini's embedding model
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            except Exception as e:
                print(f"Error generating embedding: {str(e)}")
                # Use zero vector as fallback
                embeddings.append([0.0] * self.dimension)
        
        return np.array(embeddings, dtype=np.float32)
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query using Gemini.
        
        Args:
            query (str): Query text
            
        Returns:
            np.ndarray: Query embedding
        """
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            return np.array([result['embedding']], dtype=np.float32)
        except Exception as e:
            print(f"Error generating query embedding: {str(e)}")
            return np.array([[0.0] * self.dimension], dtype=np.float32)
    
    def create_index(self, documents: List[Dict[str, Any]]):
        """
        Create FAISS index from documents.
        
        Args:
            documents (List[Dict]): List of documents with text and metadata
        """
        if not documents:
            print("No documents to index.")
            return
        
        print(f"Creating embeddings for {len(documents)} documents...")
        
        # Extract texts for embedding
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Store documents metadata
        self.documents = documents
        
        print(f"Created FAISS index with {self.index.ntotal} vectors.")
        
        # Save the index
        self.save_index()
    
    def add_documents(self, new_documents: List[Dict[str, Any]]):
        """
        Add new documents to existing index.
        
        Args:
            new_documents (List[Dict]): List of new documents to add
        """
        if not new_documents:
            return
        
        print(f"Adding {len(new_documents)} new documents to index...")
        
        # Extract texts for embedding
        texts = [doc['text'] for doc in new_documents]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Normalize embeddings
        faiss.normalize_L2(embeddings)
        
        if self.index is None:
            # Create new index if none exists
            self.index = faiss.IndexFlatIP(self.dimension)
        
        # Add to index
        self.index.add(embeddings)
        
        # Add to documents list
        self.documents.extend(new_documents)
        
        print(f"Index now contains {self.index.ntotal} vectors.")
        
        # Save updated index
        self.save_index()
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar documents given a query.
        
        Args:
            query (str): Search query
            k (int): Number of top results to return
            
        Returns:
            List[Tuple[Dict, float]]: List of (document, similarity_score) tuples
        """
        if self.index is None or len(self.documents) == 0:
            print("No index available. Please create index first.")
            return []
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        # Return results with documents and scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # Valid index
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save_index(self):
        """Save the FAISS index and documents to disk."""
        if self.index is not None:
            # Save FAISS index
            faiss.write_index(self.index, os.path.join(self.index_path, "faiss.index"))
            
            # Save documents metadata
            with open(os.path.join(self.index_path, "documents.pkl"), 'wb') as f:
                pickle.dump(self.documents, f)
            
            print(f"Index saved to {self.index_path}")
    
    def load_index(self):
        """Load the FAISS index and documents from disk."""
        index_file = os.path.join(self.index_path, "faiss.index")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        
        if os.path.exists(index_file) and os.path.exists(docs_file):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_file)
                
                # Load documents metadata
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                print(f"Loaded existing index with {len(self.documents)} documents.")
                return True
            except Exception as e:
                print(f"Error loading index: {str(e)}")
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if self.index is None or len(self.documents) == 0:
            return {
                "total_documents": 0, 
                "total_chunks": 0,
                "unique_files": 0,
                "files": []
            }
        
        # Count unique files
        unique_files = set()
        for doc in self.documents:
            unique_files.add(doc['filename'])
        
        return {
            "total_documents": len(self.documents),
            "total_chunks": self.index.ntotal if self.index else 0,
            "unique_files": len(unique_files),
            "files": list(unique_files)
        }
