"""
QID - Image Encoder
Converts images to semantic vector embeddings using CLIP.
"""

import torch
import clip
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Union
from tqdm import tqdm

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ImageEncoder:
    """
    Encodes images into vector embeddings using CLIP.
    
    How it works:
    1. Load CLIP model (pre-trained on 400M image-text pairs)
    2. Preprocess image (resize, normalize)
    3. Pass through neural network
    4. Get 512-dimensional vector representing the image's meaning
    """
    
    def __init__(self, model_name: str = "ViT-B/32", device: str = "auto"):
        """
        Initialize the image encoder.
        
        Args:
            model_name: CLIP model variant
                - ViT-B/32: Fast, good quality (default)
                - ViT-B/16: Better quality, slower
                - ViT-L/14: Best quality, slowest
            device: Device to use ('cuda', 'cpu', 'mps', or 'auto')
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        
        logger.info(f"Loading CLIP model: {model_name} on {self.device}")
        
        # Load CLIP model and preprocessing function
        self.model, self.preprocess = clip.load(
            model_name,
            device=self.device,
            download_root="./models"
        )
        
        # Set to evaluation mode (no training)
        self.model.eval()
        
        logger.info("✅ Image encoder ready")
    
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
    
    def encode_image(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        """
        Encode a single image to an embedding vector.
        
        Args:
            image: Image file path or PIL Image object
            
        Returns:
            512-dimensional normalized embedding vector
            
        Example:
            >>> encoder = ImageEncoder()
            >>> embedding = encoder.encode_image("photo.jpg")
            >>> print(embedding.shape)  # (512,)
            >>> print(embedding[:5])    # [0.23, -0.45, 0.67, ...]
        """
        # Load image if path is provided
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        
        # Preprocess: resize to 224x224, normalize
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        
        # Generate embedding (no gradient computation)
        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            
            # Normalize to unit length (important for similarity search)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Convert to numpy array and flatten
        embedding = image_features.cpu().numpy().flatten()
        
        return embedding
    
    def encode_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Encode multiple images efficiently in batches.
        
        Why batches? GPUs are like buses - more efficient to process
        multiple items at once rather than one at a time.
        
        Args:
            images: List of image paths or PIL Images
            batch_size: Number of images to process together
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings, shape (num_images, 512)
            
        Example:
            >>> encoder = ImageEncoder()
            >>> paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
            >>> embeddings = encoder.encode_batch(paths)
            >>> print(embeddings.shape)  # (3, 512)
        """
        all_embeddings = []
        
        # Process in batches
        num_batches = (len(images) + batch_size - 1) // batch_size
        
        iterator = range(0, len(images), batch_size)
        if show_progress:
            iterator = tqdm(
                iterator,
                total=num_batches,
                desc="🖼️  Encoding images",
                unit="batch"
            )
        
        for i in iterator:
            batch = images[i:i + batch_size]
            batch_embeddings = self._encode_batch_internal(batch)
            all_embeddings.append(batch_embeddings)
        
        # Combine all batches
        embeddings = np.vstack(all_embeddings)
        
        logger.info(f"✅ Encoded {len(images)} images")
        return embeddings
    
    def _encode_batch_internal(
        self,
        images: List[Union[str, Path, Image.Image]]
    ) -> np.ndarray:
        """Internal method to encode a single batch."""
        image_tensors = []
        
        for img in images:
            try:
                # Load image if path
                if isinstance(img, (str, Path)):
                    img = Image.open(img).convert('RGB')
                
                # Preprocess
                tensor = self.preprocess(img)
                image_tensors.append(tensor)
                
            except Exception as e:
                logger.warning(f"Failed to process image: {e}")
                # Add zero vector for failed images
                image_tensors.append(torch.zeros(3, 224, 224))
        
        # Stack into batch tensor
        batch_tensor = torch.stack(image_tensors).to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            features = self.model.encode_image(batch_tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        
        return features.cpu().numpy()
    
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
        return f"ImageEncoder(model={self.model_name}, device={self.device})"