"""
QID - Search Engine
Semantic search for images using natural language queries.
"""

from typing import List, Dict, Optional
from pathlib import Path

from ..embeddings.text_encoder import TextEncoder
from ..database.vector_store import VectorStore
from ..database.metadata_store import MetadataStore
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SearchEngine:
    """
    Semantic search engine for images.
    
    How it works:
    1. User types query: "sunset at the beach"
    2. Encode query to vector
    3. Search vector database
    4. Retrieve image metadata
    5. Return results with scores
    """
    
    def __init__(
        self,
        text_encoder: TextEncoder,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
        default_top_k: int = 20,
        similarity_threshold: float = 0.0
    ):
        """
        Initialize search engine.
        
        Args:
            text_encoder: Text encoder instance
            vector_store: Vector database instance
            metadata_store: Metadata database instance
            default_top_k: Default number of results
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.text_encoder = text_encoder
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.default_top_k = default_top_k
        self.similarity_threshold = similarity_threshold
        
        logger.info("✅ Search engine initialized")
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        filter_tags: Optional[List[str]] = None,
        adaptive_threshold: bool = True
    ) -> List[Dict]:
        """
        Search for images matching a text query.
        
        Args:
            query: Natural language query (e.g., "a dog playing")
            top_k: Number of results to return (if None, use adaptive filtering)
            threshold: Minimum similarity score
            filter_tags: Only return images with these tags
            adaptive_threshold: Use smart relevance filtering
            
        Returns:
            List of dictionaries with:
            - 'vector_id': Vector ID
            - 'score': Similarity score (0-1)
            - 'file_path': Path to image
            - 'file_name': Image filename
            - 'tags': Image tags
            - 'description': Image description
            
        Example:
            >>> engine = SearchEngine(text_encoder, vector_store, metadata_store)
            >>> results = engine.search("sunset at beach", top_k=5)
            >>> for r in results:
            ...     print(f"{r['file_name']}: {r['score']:.2%}")
        """
        if not query.strip():
            logger.warning("Empty query")
            return []
        
        # Use defaults if not specified
        top_k = top_k or self.default_top_k
        threshold = threshold or self.similarity_threshold
        
        logger.info(f"Searching: '{query}' (top_k={top_k}, threshold={threshold})")
        
        # Step 1: Encode query
        query_embedding = self.text_encoder.encode_text(query)
        
        # Step 2: Search vector database (get extra for filtering)
        vector_ids, scores = self.vector_store.search(
            query_embedding,
            top_k=top_k * 3,  # Get 3x more for smart filtering
            threshold=threshold
        )
        
        if not vector_ids:
            logger.info("No results found")
            return []
        
        # Step 3: Apply adaptive threshold if enabled
        if adaptive_threshold and len(scores) > 1:
            filtered_indices = self._apply_adaptive_threshold(scores)
            vector_ids = [vector_ids[i] for i in filtered_indices]
            scores = [scores[i] for i in filtered_indices]
        
        # Step 4: Get metadata for results
        results = []
        for vector_id, score in zip(vector_ids, scores):
            metadata = self.metadata_store.get(vector_id)
            
            if metadata is None:
                logger.warning(f"No metadata for vector {vector_id}")
                continue
            
            # Apply tag filter if specified
            if filter_tags:
                image_tags = metadata.get('tags', '')
                if image_tags:
                    image_tag_list = [t.strip().lower() for t in image_tags.split(',')]
                    filter_tags_lower = [t.lower() for t in filter_tags]
                    
                    # Check if any filter tag matches
                    if not any(ft in image_tag_list for ft in filter_tags_lower):
                        continue
                else:
                    continue  # No tags, skip
            
            # Build result
            result = {
                'vector_id': vector_id,
                'score': float(score),
                'file_path': metadata['file_path'],
                'file_name': metadata['file_name'],
                'file_size': metadata.get('file_size', 0),
                'date_added': metadata.get('date_added', ''),
                'tags': metadata.get('tags', ''),
                'description': metadata.get('description', '')
            }
            
            results.append(result)
            
            # Stop if we have enough results
            if len(results) >= top_k:
                break
        
        logger.info(f"Found {len(results)} results")
        
        return results
    
    def _apply_adaptive_threshold(self, scores: List[float]) -> List[int]:
        """
        Apply smart relevance filtering based on score distribution.
        
        Strategy:
        1. Find the best (top) score
        2. Calculate a dynamic threshold relative to the top score
        3. Also look for "score gaps" - big drops indicate irrelevant results
        
        Args:
            scores: List of similarity scores (sorted, descending)
            
        Returns:
            List of indices to keep
        """
        if not scores or len(scores) < 2:
            return list(range(len(scores)))
        
        top_score = scores[0]
        
        # Strategy 1: Relative threshold based on top score
        # If top score is high (>0.7), be strict (keep >80% of top)
        # If top score is low (<0.4), be lenient (keep >60% of top)
        if top_score > 0.7:
            relative_threshold = top_score * 0.80  # Keep scores within 20% of top
        elif top_score > 0.5:
            relative_threshold = top_score * 0.70  # Keep scores within 30% of top
        else:
            relative_threshold = top_score * 0.60  # Keep scores within 40% of top
        
        # Strategy 2: Find "score gaps" - sudden drops indicate irrelevance boundary
        gap_threshold = 0.08  # 8% drop is considered significant
        
        keep_indices = []
        for i, score in enumerate(scores):
            # Check relative threshold
            if score < relative_threshold:
                break
            
            # Check for score gap (if not first result)
            if i > 0:
                score_drop = scores[i-1] - score
                if score_drop > gap_threshold:
                    # Big drop! This is likely where relevant results end
                    break
            
            keep_indices.append(i)
            
            # Safety: Don't return too few results (minimum 3 if available)
            # or too many results (maximum 20)
            if len(keep_indices) >= 20:
                break
        
        # Ensure at least 3 results (or all if fewer)
        if len(keep_indices) < 3 and len(scores) >= 3:
            keep_indices = list(range(3))
        elif len(keep_indices) < len(scores) and len(scores) < 3:
            keep_indices = list(range(len(scores)))
        
        logger.info(
            f"Adaptive filtering: {len(scores)} → {len(keep_indices)} results "
            f"(top: {top_score:.2%}, threshold: {relative_threshold:.2%})"
        )
        
        return keep_indices
    
    def search_similar_to_image(
        self,
        image_path: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Find images similar to a given image.
        
        Args:
            image_path: Path to query image
            top_k: Number of results
            threshold: Minimum similarity
            
        Returns:
            List of similar images
            
        Example:
            >>> results = engine.search_similar_to_image("my_photo.jpg", top_k=10)
        """
        # Get vector ID of query image
        metadata = self.metadata_store.get_by_path(image_path)
        
        if metadata is None:
            logger.warning(f"Image not in database: {image_path}")
            return []
        
        query_vector_id = metadata['vector_id']
        
        # Get the query embedding from vector store
        # Note: FAISS doesn't have a direct "get by ID" method
        # So we'll encode the image again
        from ..embeddings.image_encoder import ImageEncoder
        
        # This is a workaround - ideally cache embeddings
        logger.warning("Re-encoding query image (consider caching embeddings)")
        
        return []  # Simplified for now
    
    def get_random_images(self, count: int = 20) -> List[Dict]:
        """
        Get random images from the database.
        
        Args:
            count: Number of random images
            
        Returns:
            List of random image metadata
        """
        import random
        
        all_metadata = self.metadata_store.get_all()
        
        if not all_metadata:
            return []
        
        # Sample random images
        sample_size = min(count, len(all_metadata))
        sampled = random.sample(all_metadata, sample_size)
        
        # Format like search results
        results = []
        for metadata in sampled:
            results.append({
                'vector_id': metadata['vector_id'],
                'score': 1.0,  # No score for random
                'file_path': metadata['file_path'],
                'file_name': metadata['file_name'],
                'file_size': metadata.get('file_size', 0),
                'date_added': metadata.get('date_added', ''),
                'tags': metadata.get('tags', ''),
                'description': metadata.get('description', '')
            })
        
        return results
    
    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from database.
        
        Returns:
            List of unique tags
        """
        all_metadata = self.metadata_store.get_all()
        
        tags = set()
        for metadata in all_metadata:
            if metadata.get('tags'):
                image_tags = [t.strip() for t in metadata['tags'].split(',')]
                tags.update(image_tags)
        
        return sorted(list(tags))
    
    def get_stats(self) -> Dict:
        """
        Get search engine statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            'total_images': len(self.metadata_store),
            'total_vectors': len(self.vector_store),
            'unique_tags': len(self.get_all_tags()),
            'embedding_dimension': self.text_encoder.embedding_dim
        }
    
    def __repr__(self) -> str:
        return (
            f"SearchEngine("
            f"images={len(self.metadata_store)}, "
            f"top_k={self.default_top_k}"
            f")"
        )