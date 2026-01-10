"""
QID - Metadata Store
Stores image metadata (paths, dates, tags) in SQLite database.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetadataStore:
    """
    SQLite database for storing image metadata.
    
    Stores information like:
    - Vector ID (connects to FAISS)
    - Image file path
    - Date added
    - File size
    - Optional tags/descriptions
    """
    
    def __init__(self, db_path: str = "data/metadata/image_metadata.db"):
        """
        Initialize metadata store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        # Create tables
        self._create_tables()
        
        logger.info(f"✅ Metadata store initialized: {db_path}")
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Main images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                vector_id INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                date_added TEXT NOT NULL,
                date_modified TEXT,
                tags TEXT,
                description TEXT
            )
        """)
        
        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path ON images(file_path)
        """)
        
        self.conn.commit()
    
    def add(
        self,
        vector_id: int,
        file_path: str,
        tags: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Add image metadata.
        
        Args:
            vector_id: ID in vector store (links to FAISS)
            file_path: Path to image file
            tags: Optional comma-separated tags
            description: Optional description
            
        Returns:
            True if added successfully
            
        Example:
            >>> store = MetadataStore()
            >>> store.add(
            ...     vector_id=0,
            ...     file_path="/path/to/photo.jpg",
            ...     tags="vacation, beach, sunset",
            ...     description="Beautiful sunset at the beach"
            ... )
        """
        try:
            path = Path(file_path)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO images (
                    vector_id, file_path, file_name, file_size,
                    date_added, date_modified, tags, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vector_id,
                str(path.absolute()),
                path.name,
                path.stat().st_size if path.exists() else 0,
                datetime.now().isoformat(),
                datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None,
                tags,
                description
            ))
            
            self.conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Image already exists: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to add metadata: {e}")
            return False
    
    def add_batch(self, metadata_list: List[Dict[str, Any]]) -> int:
        """
        Add multiple image metadata entries.
        
        Args:
            metadata_list: List of dictionaries with keys:
                - vector_id, file_path, tags (optional), description (optional)
                
        Returns:
            Number of entries added successfully
            
        Example:
            >>> store = MetadataStore()
            >>> metadata = [
            ...     {"vector_id": 0, "file_path": "img1.jpg"},
            ...     {"vector_id": 1, "file_path": "img2.jpg"},
            ... ]
            >>> count = store.add_batch(metadata)
            >>> print(f"Added {count} images")
        """
        added = 0
        for metadata in metadata_list:
            if self.add(**metadata):
                added += 1
        
        logger.info(f"Added {added}/{len(metadata_list)} metadata entries")
        return added
    
    def get(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific vector ID.
        
        Args:
            vector_id: Vector ID from FAISS
            
        Returns:
            Dictionary with metadata or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE vector_id = ?", (vector_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata by file path."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE file_path = ?", (str(Path(file_path).absolute()),))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all metadata entries."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images ORDER BY date_added DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def exists(self, file_path: str) -> bool:
        """Check if image already exists in database."""
        return self.get_by_path(file_path) is not None
    
    def update_tags(self, vector_id: int, tags: str) -> bool:
        """Update tags for an image."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE images SET tags = ? WHERE vector_id = ?",
                (tags, vector_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update tags: {e}")
            return False
    
    def update_description(self, vector_id: int, description: str) -> bool:
        """Update description for an image."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE images SET description = ? WHERE vector_id = ?",
                (description, vector_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update description: {e}")
            return False
    
    def delete(self, vector_id: int) -> bool:
        """Delete metadata entry."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM images WHERE vector_id = ?", (vector_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete metadata: {e}")
            return False
    
    def count(self) -> int:
        """Get total number of images in database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM images")
        return cursor.fetchone()[0]
    
    def clear(self):
        """Clear all metadata (dangerous!)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM images")
        self.conn.commit()
        logger.warning("🗑️  Cleared all metadata")
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __len__(self) -> int:
        """Get number of entries."""
        return self.count()
    
    def __repr__(self) -> str:
        return f"MetadataStore(images={self.count()}, db={self.db_path.name})"