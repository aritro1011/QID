"""
QID - Text Encoder
Converts text queries to semantic vector embeddings using CLIP.
"""

import torch
import clip
import numpy as np
from typing import List

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TextEncoder:
    """
    Encodes text queries into vector embeddings using CLIP.
    
    The embeddings are in the same vector space as images,
    allowing semantic search: text query → similar images
    """
    
    def __init__(self, model_name: str = "ViT-B/32", device: str = "auto"):
        """
        Initialize the text encoder.
        
        Args:
            model_name: CLIP model variant (must match ImageEncoder)
            device: Device to use ('cuda', 'cpu', 'mps', or 'auto')
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        
        logger.info(f"Loading CLIP model: {model_name} on {self.device}")
        
        # Load CLIP model (same model as ImageEncoder)
        self.model, _ = clip.load(
            model_name,
            device=self.device,
            download_root="./models"
        )
        
        self.model.eval()
        
        logger.info("✅ Text encoder ready")
    
    def _get_device(self, device: str) -> str:
        """Auto-detect best device if set to 'auto'."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode a text query to an embedding vector.
        
        Args:
            text: Text query (e.g., "a dog playing in the park")
            
        Returns:
            512-dimensional normalized embedding vector
            
        Example:
            >>> encoder = TextEncoder()
            >>> embedding = encoder.encode_text("sunset over mountains")
            >>> print(embedding.shape)  # (512,)
            
        How it works:
            1. "sunset over mountains" → Tokenize → [1, 320, 1460, ...]
            2. Pass through CLIP text encoder
            3. Get 512-dimensional vector
            4. Normalize to unit length
        """
        # Tokenize text (convert words to numbers)
        text_tokens = clip.tokenize([text]).to(self.device)
        
        # Generate embedding
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            
            # Normalize to unit length
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Convert to numpy array
        embedding = text_features.cpu().numpy().flatten()
        
        return embedding
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple text queries at once.
        
        Args:
            texts: List of text queries
            
        Returns:
            Array of embeddings, shape (num_texts, 512)
            
        Example:
            >>> encoder = TextEncoder()
            >>> queries = ["cats", "dogs", "birds"]
            >>> embeddings = encoder.encode_batch(queries)
            >>> print(embeddings.shape)  # (3, 512)
        """
        # Tokenize all texts
        text_tokens = clip.tokenize(texts).to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        embeddings = text_features.cpu().numpy()
        
        logger.info(f"✅ Encoded {len(texts)} text queries")
        return embeddings
    
    @property
    def embedding_dim(self) -> int:
        """Get the dimension of embeddings (512 for ViT-B models)."""
        dims = {
            "ViT-B/32": 512,
            "ViT-B/16": 512,
            "ViT-L/14": 768,
        }
        return dims.get(self.model_name, 512)
    
    def __repr__(self) -> str:
        return f"TextEncoder(model={self.model_name}, device={self.device})"