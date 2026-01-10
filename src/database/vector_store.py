"""
QID - Vector Store
Stores and searches image embeddings using FAISS.
"""

import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    Vector database for storing and searching image embeddings.
    
    Uses FAISS (Facebook AI Similarity Search) for efficient
    nearest neighbor search in high-dimensional space.
    
    Think of it like a specialized database where:
    - Keys = image IDs
    - Values = 512-dimensional vectors
    - Query = "find most similar vectors"
    """
    
    def __init__(
        self,
        dimension: int = 512,
        index_type: str = "Flat",
        metric: str = "cosine"
    ):
        """
        Initialize vector store.
        
        Args:
            dimension: Embedding dimension (512 for CLIP ViT-B)
            index_type: 
                - "Flat": Exact search (slower, perfect accuracy)
                - "IVF": Approximate search (faster, 98%+ accuracy)
            metric:
                - "cosine": Cosine similarity (angle between vectors)
                - "l2": Euclidean distance
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        
        # Create FAISS index
        self.index = self._create_index()
        
        # Track number of vectors
        self.num_vectors = 0
        
        logger.info(f"✅ Vector store initialized: {index_type}, dim={dimension}")
    
    def _create_index(self) -> faiss.Index:
        """Create appropriate FAISS index based on settings."""
        
        if self.metric == "cosine":
            # For cosine similarity, use Inner Product on normalized vectors
            if self.index_type == "Flat":
                index = faiss.IndexFlatIP(self.dimension)
            else:
                # IVF index for approximate search
                quantizer = faiss.IndexFlatIP(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        
        elif self.metric == "l2":
            # L2 (Euclidean) distance
            if self.index_type == "Flat":
                index = faiss.IndexFlatL2(self.dimension)
            else:
                quantizer = faiss.IndexFlatL2(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        
        else:
            raise ValueError(f"Unknown metric: {self.metric}")
        
        return index
    
    def add(self, embeddings: np.ndarray) -> List[int]:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: Array of shape (N, dimension)
            
        Returns:
            List of IDs assigned to each embedding
            
        Example:
            >>> store = VectorStore()
            >>> embeddings = np.random.rand(10, 512)
            >>> ids = store.add(embeddings)
            >>> print(ids)  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        """
        # Ensure correct shape
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Ensure float32 (FAISS requirement)
        embeddings = embeddings.astype(np.float32)
        
        # Train index if needed (for IVF)
        if self.index_type == "IVF" and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(embeddings)
        
        # Add to index
        start_id = self.num_vectors
        self.index.add(embeddings)
        self.num_vectors += len(embeddings)
        
        # Return assigned IDs
        ids = list(range(start_id, self.num_vectors))
        
        logger.info(f"Added {len(embeddings)} vectors (total: {self.num_vectors})")
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 20,
        threshold: float = 0.0
    ) -> Tuple[List[int], List[float]]:
        """
        Search for most similar vectors.
        
        Args:
            query_embedding: Query vector (1D array of length 512)
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            Tuple of (ids, scores)
            - ids: List of vector IDs
            - scores: List of similarity scores
            
        Example:
            >>> store = VectorStore()
            >>> # ... add some vectors ...
            >>> query = np.random.rand(512)
            >>> ids, scores = store.search(query, top_k=5)
            >>> print(ids)     # [42, 17, 99, 3, 56]
            >>> print(scores)  # [0.95, 0.89, 0.87, 0.82, 0.78]
        """
        if self.num_vectors == 0:
            logger.warning("Vector store is empty!")
            return [], []
        
        # Ensure correct shape and type
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype(np.float32)
        
        # Search
        scores, ids = self.index.search(query_embedding, top_k)
        
        # Flatten results
        scores = scores[0].tolist()
        ids = ids[0].tolist()
        
        # Filter by threshold
        results = [
            (id, score) for id, score in zip(ids, scores)
            if score >= threshold and id != -1  # -1 means no result
        ]
        
        if results:
            ids, scores = zip(*results)
            return list(ids), list(scores)
        else:
            return [], []
    
    def save(self, path: str):
        """
        Save index to disk.
        
        Args:
            path: File path to save to (e.g., "data/embeddings/index.faiss")
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(path))
        logger.info(f"💾 Saved vector store to {path}")
    
    def load(self, path: str):
        """
        Load index from disk.
        
        Args:
            path: File path to load from
        """
        path = Path(path)
        
        if not path.exists():
            logger.warning(f"Index file not found: {path}, starting with empty index")
            return
        
        try:
            self.index = faiss.read_index(str(path))
            self.num_vectors = self.index.ntotal
            
            logger.info(f"📂 Loaded vector store from {path} ({self.num_vectors} vectors)")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            logger.info("Starting with empty index")
    
    def clear(self):
        """Clear all vectors from the index."""
        self.index = self._create_index()
        self.num_vectors = 0
        logger.info("🗑️  Cleared vector store")
    
    def __len__(self) -> int:
        """Get number of vectors in the store."""
        return self.num_vectors
    
    def __repr__(self) -> str:
        return f"VectorStore(vectors={self.num_vectors}, type={self.index_type})"