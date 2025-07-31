import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StableVectorStore:
    """
    FAISS vector store using SentenceTransformers for stable embeddings.
    Supports text documents and images via caption embeddings.
    """
    
    def __init__(self, index_path: str = "index/stable_faiss_index/"):
        """
        Initialize the FAISS vector store with SentenceTransformers embeddings.
        
        Args:
            index_path (str): Path to store the FAISS index
        """
        self.index_path = index_path
        self.index = None
        self.documents = []
        
        # Initialize SentenceTransformers model
        print("🔄 Loading SentenceTransformers model...")
        self.model_name = "all-MiniLM-L6-v2"  # Fast and reliable
        self.model = SentenceTransformer(self.model_name)
        print(f"✅ SentenceTransformers model loaded: {self.model_name}")
        
        # Get embedding dimension
        dummy_embedding = self.model.encode(["test"])
        self.dimension = dummy_embedding.shape[1]
        print(f"✅ Embedding dimension: {self.dimension}")
        
        # Create index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Load existing index if available
        self.load_index()
    
    def embed_text_chunk(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text chunk using SentenceTransformers.
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Text embedding
        """
        try:
            embedding = self.model.encode([text], normalize_embeddings=True)
            return embedding[0].astype(np.float32)
        except Exception as e:
            print(f"Error generating text embedding: {str(e)}")
            return np.zeros(self.dimension, dtype=np.float32)
    
    def embed_image_chunk(self, base64_image: str, caption: str = None) -> np.ndarray:
        """
        Generate embedding for an image by using its caption.
        
        Args:
            base64_image (str): Base64-encoded image (not used, kept for compatibility)
            caption (str): Caption to embed
            
        Returns:
            np.ndarray: Caption embedding
        """
        # Use caption text embedding for images
        if caption:
            return self.embed_text_chunk(caption)
        else:
            return self.embed_text_chunk("Image from policy document")
    
    def generate_embeddings(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents with text or image data
            
        Returns:
            np.ndarray: Array of embeddings
        """
        embeddings = []
        
        print(f"🔄 Generating embeddings for {len(documents)} documents...")
        
        for i, doc in enumerate(documents):
            if i % 50 == 0:  # Progress indicator
                print(f"   Progress: {i}/{len(documents)}")
                
            if doc.get('type') == 'text':
                embedding = self.embed_text_chunk(doc['text'])
            elif doc.get('type') == 'image':
                caption = doc.get('caption', 'Image from policy document')
                embedding = self.embed_image_chunk('', caption)  # Don't process actual image
            else:
                print(f"Unknown document type: {doc.get('type')}")
                embedding = np.zeros(self.dimension, dtype=np.float32)
            
            embeddings.append(embedding)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        return np.array(embeddings, dtype=np.float32)
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query.
        
        Args:
            query (str): Query text
            
        Returns:
            np.ndarray: Query embedding
        """
        embedding = self.embed_text_chunk(query)
        return np.array([embedding], dtype=np.float32)
    
    def create_index(self, documents: List[Dict[str, Any]]):
        """
        Create FAISS index from documents.
        
        Args:
            documents (List[Dict]): List of documents with text and image data
        """
        if not documents:
            print("No documents to index.")
            return
        
        print(f"Creating FAISS index for {len(documents)} documents...")
        
        # Generate embeddings for all documents
        embeddings = self.generate_embeddings(documents)
        
        # Create FAISS index (Inner Product since embeddings are normalized)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Store documents metadata
        self.documents = documents
        
        print(f"✅ Created FAISS index with {self.index.ntotal} vectors")
        
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
        
        # Generate embeddings for new documents
        embeddings = self.generate_embeddings(new_documents)
        
        if self.index is None:
            # Create new index if none exists
            self.index = faiss.IndexFlatIP(self.dimension)
        
        # Add to index
        self.index.add(embeddings)
        
        # Add to documents list
        self.documents.extend(new_documents)
        
        print(f"✅ Index now contains {self.index.ntotal} vectors")
        
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
            
            print(f"💾 Index saved to {self.index_path}")
    
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
                
                print(f"📁 Loaded existing index with {len(self.documents)} documents")
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
                "files": [],
                "model": "None"
            }
        
        # Count unique files
        unique_files = set()
        text_count = sum(1 for doc in self.documents if doc.get('type') == 'text')
        image_count = sum(1 for doc in self.documents if doc.get('type') == 'image')
        
        for doc in self.documents:
            unique_files.add(doc['filename'])
        
        return {
            "total_documents": len(self.documents),
            "text_documents": text_count,
            "image_documents": image_count,
            "total_chunks": self.index.ntotal if self.index else 0,
            "unique_files": len(unique_files),
            "files": list(unique_files),
            "model": self.model_name,
            "dimension": self.dimension
        }
