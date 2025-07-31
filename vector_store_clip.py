import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
import torch
import base64
import io
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CLIPVectorStore:
    """
    FAISS vector store using CLIP for multimodal embeddings.
    Supports both text and image embeddings in the same vector space.
    """
    
    def __init__(self, index_path: str = "index/clip_faiss_index/"):
        """
        Initialize the FAISS vector store with CLIP embeddings.
        
        Args:
            index_path (str): Path to store the FAISS index
        """
        self.index_path = index_path
        self.index = None
        self.documents = []
        
        # Initialize CLIP model and processor with fallback
        print("🔄 Loading CLIP model...")
        try:
            self.model_name = "openai/clip-vit-base-patch32"
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.use_clip = True
            print(f"✅ CLIP model loaded successfully on {self.device}")
        except Exception as e:
            print(f"⚠️  CLIP model loading failed: {str(e)}")
            print("   Falling back to SentenceTransformers for text-only embeddings...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_clip = False
            print("✅ SentenceTransformers model loaded as fallback")
        
        # Get embedding dimension
        if self.use_clip:
            with torch.no_grad():
                dummy_input = self.processor(text=["test"], return_tensors="pt")
                dummy_features = self.model.get_text_features(**dummy_input)
                self.dimension = dummy_features.shape[1]
            print(f"✅ CLIP model loaded on {self.device}, embedding dimension: {self.dimension}")
        else:
            # SentenceTransformers fallback
            dummy_embedding = self.model.encode(["test"])
            self.dimension = dummy_embedding.shape[1]
            print(f"✅ SentenceTransformers model loaded, embedding dimension: {self.dimension}")
        
        # Create index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Load existing index if available
        self.load_index()
    
    def embed_text_chunk(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text chunk using CLIP or SentenceTransformers.
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Text embedding
        """
        try:
            if self.use_clip:
                with torch.no_grad():
                    inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True)
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    text_features = self.model.get_text_features(**inputs)
                    # Normalize for cosine similarity
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    return text_features.cpu().numpy()[0].astype(np.float32)
            else:
                # Use SentenceTransformers fallback
                embedding = self.model.encode([text], normalize_embeddings=True)
                return embedding[0].astype(np.float32)
        except Exception as e:
            print(f"Error generating text embedding: {str(e)}")
            return np.zeros(self.dimension, dtype=np.float32)
    
    def embed_image_chunk(self, base64_image: str, caption: str = None) -> np.ndarray:
        """
        Generate embedding for a single image using CLIP or fallback to caption.
        
        Args:
            base64_image (str): Base64-encoded image
            caption (str): Optional caption (used as fallback for non-CLIP)
            
        Returns:
            np.ndarray: Image embedding
        """
        if not self.use_clip:
            # If not using CLIP, always use caption text embedding
            if caption:
                return self.embed_text_chunk(caption)
            else:
                return self.embed_text_chunk("Image from policy document")
        
        try:
            # Decode base64 image
            if base64_image.startswith('data:image'):
                # Remove data URI prefix if present
                base64_image = base64_image.split(',', 1)[1]
            
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            with torch.no_grad():
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                image_features = self.model.get_image_features(**inputs)
                # Normalize for cosine similarity
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                return image_features.cpu().numpy()[0].astype(np.float32)
                
        except Exception as e:
            print(f"❌ CLIP image embedding failed: {str(e)}")
            # Fallback to text embedding of caption
            if caption:
                print(f"   Falling back to caption embedding: '{caption[:50]}...'")
                return self.embed_text_chunk(caption)
            else:
                print("   No caption available, using generic text")
                return self.embed_text_chunk("Image from policy document")
    
    def generate_embeddings(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """
        Generate embeddings for a list of documents using CLIP.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents with text or image data
            
        Returns:
            np.ndarray: Array of embeddings
        """
        embeddings = []
        
        print(f"🔄 Generating CLIP embeddings for {len(documents)} documents...")
        
        for i, doc in enumerate(documents):
            if i % 50 == 0:  # Progress indicator
                print(f"   Progress: {i}/{len(documents)}")
                
            if doc.get('type') == 'text':
                embedding = self.embed_text_chunk(doc['text'])
            elif doc.get('type') == 'image':
                base64_data = doc.get('base64_data', '')
                caption = doc.get('caption', 'Image from policy document')
                embedding = self.embed_image_chunk(base64_data, caption)
            else:
                print(f"Unknown document type: {doc.get('type')}")
                embedding = np.zeros(self.dimension, dtype=np.float32)
            
            embeddings.append(embedding)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        return np.array(embeddings, dtype=np.float32)
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query using CLIP.
        
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
        
        print(f"Creating CLIP-based FAISS index for {len(documents)} documents...")
        
        # Generate embeddings for all documents (text and images)
        embeddings = self.generate_embeddings(documents)
        
        # Create FAISS index (Inner Product since embeddings are already normalized)
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
        
        print(f"Adding {len(new_documents)} new documents to CLIP index...")
        
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
        
        # Search (no need to normalize since both query and index are normalized)
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
            
            print(f"💾 CLIP index saved to {self.index_path}")
    
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
                
                print(f"📁 Loaded existing CLIP index with {len(self.documents)} documents")
                return True
            except Exception as e:
                print(f"Error loading CLIP index: {str(e)}")
        
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
            "dimension": self.dimension,
            "device": self.device
        }
