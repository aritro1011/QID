"""
QID - Index Cleaner
Detects and removes embeddings/metadata for missing image files.
"""

from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm

from ..database.vector_store import VectorStore
from ..database.metadata_store import MetadataStore
from ..utils.logger import get_logger

logger = get_logger(__name__)


class IndexCleaner:
    """
    Cleans the index by removing entries for missing image files.
    
    This is essential when:
    - Images are deleted/moved outside the app
    - Directories are reorganized
    - Storage drives are disconnected
    - You want to sync the database with actual filesystem state
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        metadata_store: MetadataStore
    ):
        """
        Initialize index cleaner.
        
        Args:
            vector_store: Vector database instance
            metadata_store: Metadata database instance
        """
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        
        logger.info("✅ Index cleaner initialized")
    
    def scan_for_missing(self, show_progress: bool = True) -> Dict[str, any]:
        """
        Scan database for missing image files.
        
        Args:
            show_progress: Show progress bar during scan
            
        Returns:
            Dictionary with scan results:
            - 'total': Total images in database
            - 'found': Images that exist on disk
            - 'missing': Images that are missing
            - 'missing_ids': List of vector IDs for missing images
            - 'missing_paths': List of file paths for missing images
            
        Example:
            >>> cleaner = IndexCleaner(vector_store, metadata_store)
            >>> results = cleaner.scan_for_missing()
            >>> print(f"Found {results['missing']} missing images")
        """
        logger.info("🔍 Scanning for missing images...")
        
        # Get all metadata entries
        all_metadata = self.metadata_store.get_all()
        total = len(all_metadata)
        
        results = {
            'total': total,
            'found': 0,
            'missing': 0,
            'missing_ids': [],
            'missing_paths': []
        }
        
        if total == 0:
            logger.info("Database is empty, nothing to scan")
            return results
        
        # Check each image
        iterator = tqdm(all_metadata, desc="🔍 Scanning", disable=not show_progress)
        
        for metadata in iterator:
            file_path = Path(metadata['file_path'])
            
            if file_path.exists():
                results['found'] += 1
            else:
                results['missing'] += 1
                results['missing_ids'].append(metadata['vector_id'])
                results['missing_paths'].append(str(file_path))
        
        logger.info(
            f"Scan complete: {results['found']} found, "
            f"{results['missing']} missing"
        )
        
        return results
    
    def clean_missing(
        self,
        dry_run: bool = False,
        show_progress: bool = True
    ) -> Dict[str, any]:
        """
        Remove entries for missing images.
        
        Args:
            dry_run: If True, only report what would be deleted (don't actually delete)
            show_progress: Show progress bar
            
        Returns:
            Dictionary with cleanup results:
            - 'scanned': Total images scanned
            - 'missing': Missing images found
            - 'removed': Images removed from database
            - 'failed': Failed to remove
            - 'remaining': Images remaining in database
            
        Example:
            >>> cleaner = IndexCleaner(vector_store, metadata_store)
            >>> # First, do a dry run
            >>> results = cleaner.clean_missing(dry_run=True)
            >>> print(f"Would remove {results['missing']} images")
            >>> 
            >>> # Then actually clean
            >>> results = cleaner.clean_missing(dry_run=False)
            >>> print(f"Removed {results['removed']} images")
        """
        logger.info("🧹 Starting cleanup...")
        
        # First, scan for missing images
        scan_results = self.scan_for_missing(show_progress=show_progress)
        
        results = {
            'scanned': scan_results['total'],
            'missing': scan_results['missing'],
            'removed': 0,
            'failed': 0,
            'remaining': scan_results['total']
        }
        
        if scan_results['missing'] == 0:
            logger.info("✅ No missing images found, database is clean!")
            return results
        
        if dry_run:
            logger.info(
                f"DRY RUN: Would remove {scan_results['missing']} missing images"
            )
            return results
        
        # Remove missing entries
        missing_ids = scan_results['missing_ids']
        
        iterator = tqdm(
            missing_ids,
            desc="🗑️  Removing",
            disable=not show_progress
        )
        
        for vector_id in iterator:
            try:
                # Remove from metadata store
                success = self.metadata_store.delete(vector_id)
                
                if success:
                    results['removed'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to remove vector_id {vector_id}: {e}")
                results['failed'] += 1
        
        results['remaining'] = results['scanned'] - results['removed']
        
        # Note: We can't easily remove from FAISS index by ID
        # FAISS doesn't support deletion, so we note this limitation
        logger.warning(
            "⚠️  Note: Vector embeddings remain in FAISS index. "
            "Run full reindex to reclaim space."
        )
        
        logger.info(
            f"✅ Cleanup complete: Removed {results['removed']} entries, "
            f"{results['failed']} failed"
        )
        
        return results
    
    def rebuild_vector_store(self, show_progress: bool = True) -> bool:
        """
        Rebuild vector store from scratch using current metadata.
        
        This is necessary because FAISS doesn't support deletion.
        Only use this after cleaning metadata to reclaim disk space.
        
        WARNING: This requires re-encoding all images, which can be slow!
        
        Args:
            show_progress: Show progress bar
            
        Returns:
            True if successful
        """
        logger.warning("⚠️  This will rebuild the entire vector store!")
        logger.warning("⚠️  This requires re-encoding all images.")
        
        # This would need the image encoder, which we don't have here
        # This should be implemented in BatchIndexer instead
        logger.error(
            "Vector store rebuild must be done through BatchIndexer.reindex_all()"
        )
        
        return False
    
    def get_orphaned_vectors(self) -> int:
        """
        Get count of vectors in FAISS that have no metadata.
        
        Returns:
            Number of orphaned vectors
        """
        vector_count = len(self.vector_store)
        metadata_count = len(self.metadata_store)
        
        orphaned = vector_count - metadata_count
        
        if orphaned > 0:
            logger.info(f"Found {orphaned} orphaned vectors in FAISS index")
        
        return max(0, orphaned)
    
    def validate_database_integrity(self) -> Dict[str, any]:
        """
        Comprehensive database integrity check.
        
        Returns:
            Dictionary with integrity status:
            - 'vector_count': Total vectors in FAISS
            - 'metadata_count': Total metadata entries
            - 'orphaned_vectors': Vectors without metadata
            - 'missing_files': Metadata entries for missing files
            - 'is_healthy': True if database is in good state
        """
        logger.info("🔍 Checking database integrity...")
        
        # Scan for missing files
        scan = self.scan_for_missing(show_progress=False)
        
        # Check for orphaned vectors
        orphaned = self.get_orphaned_vectors()
        
        results = {
            'vector_count': len(self.vector_store),
            'metadata_count': len(self.metadata_store),
            'orphaned_vectors': orphaned,
            'missing_files': scan['missing'],
            'missing_file_list': scan['missing_paths'],
            'is_healthy': orphaned == 0 and scan['missing'] == 0
        }
        
        if results['is_healthy']:
            logger.info("✅ Database integrity check passed!")
        else:
            logger.warning("⚠️  Database integrity issues found:")
            if orphaned > 0:
                logger.warning(f"  - {orphaned} orphaned vectors")
            if scan['missing'] > 0:
                logger.warning(f"  - {scan['missing']} missing files")
        
        return results
    
    def generate_report(self) -> str:
        """
        Generate a detailed text report of database status.
        
        Returns:
            Formatted report string
        """
        integrity = self.validate_database_integrity()
        
        report = []
        report.append("=" * 60)
        report.append("DATABASE INTEGRITY REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Vector Store Count:    {integrity['vector_count']:,}")
        report.append(f"Metadata Store Count:  {integrity['metadata_count']:,}")
        report.append("")
        report.append(f"Orphaned Vectors:      {integrity['orphaned_vectors']:,}")
        report.append(f"Missing Files:         {integrity['missing_files']:,}")
        report.append("")
        
        if integrity['is_healthy']:
            report.append("Status: ✅ HEALTHY")
        else:
            report.append("Status: ⚠️  NEEDS ATTENTION")
            report.append("")
            report.append("Recommendations:")
            
            if integrity['missing_files'] > 0:
                report.append("  1. Run clean_missing() to remove stale metadata")
            
            if integrity['orphaned_vectors'] > 0:
                report.append("  2. Run reindex_all() to rebuild vector store")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def clean_index_interactive(
    vector_store: VectorStore,
    metadata_store: MetadataStore
):
    """
    Interactive command-line interface for cleaning the index.
    
    Example:
        >>> from qid.indexing.index_cleaner import clean_index_interactive
        >>> clean_index_interactive(vector_store, metadata_store)
    """
    cleaner = IndexCleaner(vector_store, metadata_store)
    
    print("\n" + "=" * 60)
    print("QID - INDEX CLEANER")
    print("=" * 60)
    
    # Generate report
    print("\nGenerating integrity report...")
    print(cleaner.generate_report())
    
    integrity = cleaner.validate_database_integrity()
    
    if integrity['is_healthy']:
        print("\n✅ Your database is healthy! No cleaning needed.")
        return
    
    if integrity['missing_files'] == 0:
        print("\n✅ No missing files found.")
        return
    
    # Offer to clean
    print(f"\n⚠️  Found {integrity['missing_files']} missing files.")
    print("\nMissing files:")
    for i, path in enumerate(integrity['missing_file_list'][:10], 1):
        print(f"  {i}. {path}")
    
    if len(integrity['missing_file_list']) > 10:
        print(f"  ... and {len(integrity['missing_file_list']) - 10} more")
    
    print("\nOptions:")
    print("  1. Remove missing entries (recommended)")
    print("  2. Cancel")
    
    choice = input("\nYour choice (1-2): ").strip()
    
    if choice == "1":
        print("\n🧹 Cleaning database...")
        results = cleaner.clean_missing(dry_run=False, show_progress=True)
        
        print("\n" + "=" * 60)
        print("CLEANUP RESULTS")
        print("=" * 60)
        print(f"Scanned:   {results['scanned']:,} entries")
        print(f"Missing:   {results['missing']:,} entries")
        print(f"Removed:   {results['removed']:,} entries")
        print(f"Failed:    {results['failed']:,} entries")
        print(f"Remaining: {results['remaining']:,} entries")
        print("=" * 60)
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} entries failed to remove")
        else:
            print("\n✅ Cleanup completed successfully!")
        
        print("\n💡 Tip: Run a full reindex to reclaim disk space from FAISS.")
    
    else:
        print("\n❌ Cleanup cancelled")