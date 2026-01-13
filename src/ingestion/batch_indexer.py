"""
QID - Enhanced Batch Indexer
Includes automatic cleanup of missing images.
"""

from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

from ..embeddings.image_encoder import ImageEncoder
from ..database.vector_store import VectorStore
from ..database.metadata_store import MetadataStore
from .image_processor import ImageProcessor
from .index_cleaner import IndexCleaner
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BatchIndexer:
    """
    Complete pipeline for indexing images with automatic cleanup.
    
    Pipeline:
    1. Find images in directory
    2. Validate images
    3. Clean missing images (optional)
    4. Filter already-processed images
    5. Encode images in batches
    6. Store embeddings in vector database
    7. Store metadata in SQLite
    8. Save everything to disk
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
        self.cleaner = IndexCleaner(vector_store, metadata_store)
        
        logger.info("✅ Batch indexer initialized")
    
    def index_directory(
        self,
        directory: str,
        recursive: bool = True,
        validate: bool = True,
        skip_existing: bool = True,
        clean_missing: bool = True
    ) -> Dict[str, int]:
        """
        Index all images in a directory with automatic cleanup.
        
        Args:
            directory: Path to image directory
            recursive: Include subdirectories
            validate: Validate images before processing
            skip_existing: Skip already-indexed images
            clean_missing: Automatically clean missing images before indexing
            
        Returns:
            Dictionary with statistics:
            - 'found': Total images found
            - 'valid': Valid images
            - 'new': New images to process
            - 'processed': Successfully processed
            - 'failed': Failed to process
            - 'cleaned': Missing images removed (if clean_missing=True)
            
        Example:
            >>> indexer = BatchIndexer(encoder, vector_store, metadata_store)
            >>> stats = indexer.index_directory("data/images", clean_missing=True)
            >>> print(f"Processed {stats['processed']}, cleaned {stats['cleaned']}")
        """
        logger.info(f"Starting indexing: {directory}")
        
        # Statistics
        stats = {
            'found': 0,
            'valid': 0,
            'new': 0,
            'processed': 0,
            'failed': 0,
            'cleaned': 0
        }
        
        # Step 0: Clean missing images (if enabled)
        if clean_missing:
            print("\n🧹 Step 0: Cleaning missing images...")
            clean_results = self.cleaner.clean_missing(
                dry_run=False,
                show_progress=True
            )
            stats['cleaned'] = clean_results['removed']
            
            if stats['cleaned'] > 0:
                print(f"✅ Cleaned {stats['cleaned']} missing images")
        
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
        if stats['cleaned'] > 0:
            print(f"Cleaned:    {stats['cleaned']} missing images")
        print(f"Total in DB: {len(self.metadata_store)} images")
        print("="*60)
        
        logger.info(f"Indexing complete: {stats}")
        
        return stats
    
    def clean_database(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Clean database by removing entries for missing images.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary with cleanup results
            
        Example:
            >>> # First check what would be removed
            >>> results = indexer.clean_database(dry_run=True)
            >>> print(f"Would remove {results['missing']} entries")
            >>> 
            >>> # Then actually clean
            >>> results = indexer.clean_database(dry_run=False)
            >>> print(f"Removed {results['removed']} entries")
        """
        logger.info("Running database cleanup...")
        
        results = self.cleaner.clean_missing(
            dry_run=dry_run,
            show_progress=True
        )
        
        if not dry_run and results['removed'] > 0:
            # Save changes
            self._save_all()
        
        return results
    
    def get_database_health(self) -> Dict[str, any]:
        """
        Get comprehensive database health status.
        
        Returns:
            Dictionary with health metrics
            
        Example:
            >>> health = indexer.get_database_health()
            >>> if not health['is_healthy']:
            ...     print("Database needs maintenance!")
        """
        return self.cleaner.validate_database_integrity()
    
    def generate_health_report(self) -> str:
        """
        Generate detailed health report.
        
        Returns:
            Formatted report string
        """
        return self.cleaner.generate_report()
    
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
        
        # Index fresh (no need to clean since we just cleared)
        return self.index_directory(
            directory,
            skip_existing=False,
            clean_missing=False
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
    def set_model(self, model_name: str):
        """
        Update CLIP model and reload encoder.
        """
        self.image_encoder.set_model(model_name)


    def set_device(self, device: str):
        """
        Update device (cpu / cuda) and reload encoder.
        """
        self.image_encoder.set_device(device)
