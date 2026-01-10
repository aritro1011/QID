"""
QID - Batch Indexer
Orchestrates the complete image indexing pipeline.
"""

from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

from ..embeddings.image_encoder import ImageEncoder
from ..database.vector_store import VectorStore
from ..database.metadata_store import MetadataStore
from .image_processor import ImageProcessor
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BatchIndexer:
    """
    Complete pipeline for indexing images.
    
    Pipeline:
    1. Find images in directory
    2. Validate images
    3. Filter already-processed images
    4. Encode images in batches
    5. Store embeddings in vector database
    6. Store metadata in SQLite
    7. Save everything to disk
    """
    
    def __init__(
        self,
        image_encoder: ImageEncoder,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
        batch_size: int = 32,
        config = None
    ):
        """
        Initialize batch indexer.
        
        Args:
            image_encoder: Image encoder instance
            vector_store: Vector database instance
            metadata_store: Metadata database instance
            batch_size: Number of images to process at once
            config: Config instance (optional)
        """
        self.image_encoder = image_encoder
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.batch_size = batch_size
        self.config = config
        
        self.image_processor = ImageProcessor()
        
        logger.info("✅ Batch indexer initialized")
    
    def index_directory(
        self,
        directory: str,
        recursive: bool = True,
        validate: bool = True,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        Index all images in a directory.
        
        Args:
            directory: Path to image directory
            recursive: Include subdirectories
            validate: Validate images before processing
            skip_existing: Skip already-indexed images
            
        Returns:
            Dictionary with statistics:
            - 'found': Total images found
            - 'valid': Valid images
            - 'new': New images to process
            - 'processed': Successfully processed
            - 'failed': Failed to process
            
        Example:
            >>> indexer = BatchIndexer(encoder, vector_store, metadata_store)
            >>> stats = indexer.index_directory("data/images")
            >>> print(f"Processed {stats['processed']} images")
        """
        logger.info(f"Starting indexing: {directory}")
        
        # Statistics
        stats = {
            'found': 0,
            'valid': 0,
            'new': 0,
            'processed': 0,
            'failed': 0
        }
        
        # Step 1: Find images
        print("\n📁 Step 1: Finding images...")
        image_paths = self.image_processor.find_images(directory, recursive)
        stats['found'] = len(image_paths)
        
        if not image_paths:
            logger.warning("No images found!")
            return stats
        
        # Step 2: Validate images (optional but recommended)
        if validate:
            print("\n🔍 Step 2: Validating images...")
            valid_paths, invalid_paths = self.image_processor.validate_batch(
                image_paths,
                show_progress=True
            )
            stats['valid'] = len(valid_paths)
            stats['failed'] = len(invalid_paths)
            
            image_paths = valid_paths
        else:
            stats['valid'] = len(image_paths)
        
        # Step 3: Filter already-processed images
        if skip_existing:
            print("\n🔎 Step 3: Checking for existing images...")
            existing_metadata = self.metadata_store.get_all()
            existing_paths = {m['file_path'] for m in existing_metadata}
            
            image_paths = self.image_processor.filter_existing(
                image_paths,
                existing_paths
            )
            stats['new'] = len(image_paths)
        else:
            stats['new'] = len(image_paths)
        
        if not image_paths:
            print("\n✅ All images already indexed!")
            return stats
        
        # Step 4: Process images in batches
        print(f"\n🚀 Step 4: Processing {len(image_paths)} images...")
        processed = self._process_batch(image_paths)
        stats['processed'] = processed
        
        # Step 5: Save to disk
        print("\n💾 Step 5: Saving to disk...")
        self._save_all()
        
        # Summary
        print("\n" + "="*60)
        print("✅ INDEXING COMPLETE!")
        print("="*60)
        print(f"Found:      {stats['found']} images")
        print(f"Valid:      {stats['valid']} images")
        print(f"New:        {stats['new']} images")
        print(f"Processed:  {stats['processed']} images")
        print(f"Failed:     {stats['failed']} images")
        print(f"Total in DB: {len(self.metadata_store)} images")
        print("="*60)
        
        logger.info(f"Indexing complete: {stats}")
        
        return stats
    
    def _process_batch(self, image_paths: List[Path]) -> int:
        """
        Process a batch of images.
        
        Returns:
            Number of images successfully processed
        """
        processed = 0
        total_batches = (len(image_paths) + self.batch_size - 1) // self.batch_size
        
        # Process in batches
        for i in tqdm(
            range(0, len(image_paths), self.batch_size),
            total=total_batches,
            desc="🖼️  Encoding batches",
            unit="batch"
        ):
            batch_paths = image_paths[i:i + self.batch_size]
            
            try:
                # Encode images
                embeddings = self.image_encoder.encode_batch(
                    [str(p) for p in batch_paths],
                    batch_size=len(batch_paths),
                    show_progress=False  # We're showing batch-level progress
                )
                
                # Add to vector store
                vector_ids = self.vector_store.add(embeddings)
                
                # Add metadata
                for vector_id, path in zip(vector_ids, batch_paths):
                    success = self.metadata_store.add(
                        vector_id=vector_id,
                        file_path=str(path.absolute())
                    )
                    
                    if success:
                        processed += 1
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                continue
        
        return processed
    
    def index_single_image(
        self,
        image_path: str,
        tags: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Index a single image.
        
        Args:
            image_path: Path to image
            tags: Optional comma-separated tags
            description: Optional description
            
        Returns:
            True if successful
            
        Example:
            >>> indexer.index_single_image(
            ...     "photo.jpg",
            ...     tags="vacation, beach",
            ...     description="Sunset at the beach"
            ... )
        """
        path = Path(image_path)
        
        # Check if already exists
        if self.metadata_store.exists(str(path.absolute())):
            logger.warning(f"Image already indexed: {path.name}")
            return False
        
        # Validate
        if not self.image_processor.validate_image(path):
            logger.error(f"Invalid image: {path}")
            return False
        
        try:
            # Encode
            embedding = self.image_encoder.encode_image(str(path))
            
            # Add to vector store
            vector_ids = self.vector_store.add(embedding)
            vector_id = vector_ids[0]
            
            # Add metadata
            success = self.metadata_store.add(
                vector_id=vector_id,
                file_path=str(path.absolute()),
                tags=tags,
                description=description
            )
            
            if success:
                logger.info(f"✅ Indexed: {path.name}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to index {path}: {e}")
        
        return False
    
    def reindex_all(self, directory: str):
        """
        Clear database and reindex everything.
        
        Warning: This deletes all existing data!
        """
        logger.warning("⚠️  Reindexing: Clearing all data...")
        
        # Clear everything
        self.vector_store.clear()
        self.metadata_store.clear()
        
        # Index fresh
        return self.index_directory(
            directory,
            skip_existing=False
        )
    
    def _save_all(self):
        """Save vector store and metadata to disk."""
        embeddings_path = Path(self.config.get('database.embeddings_path'))
        embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save vector store
        self.vector_store.save(str(embeddings_path))
        
        # Metadata is auto-saved (SQLite commits on each operation)
        logger.info("💾 All data saved")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get current database statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_images': len(self.metadata_store),
            'total_vectors': len(self.vector_store),
            'vector_dimension': self.vector_store.dimension,
            'index_type': self.vector_store.index_type
        }
    
    def __repr__(self) -> str:
        return (
            f"BatchIndexer("
            f"images={len(self.metadata_store)}, "
            f"batch_size={self.batch_size}"
            f")"
        )