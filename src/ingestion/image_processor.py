"""
QID - Image Processor
Finds and validates images in directories.
"""

import os
from pathlib import Path
from typing import List, Set, Tuple
from PIL import Image

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    """
    Scans directories and validates image files.
    
    Handles:
    - Finding all images in a folder (including subfolders)
    - Filtering by file extension
    - Validating images (can be opened)
    - Skipping already-processed images
    """
    
    def __init__(self, supported_formats: List[str] = None):
        """
        Initialize image processor.
        
        Args:
            supported_formats: List of file extensions
                Default: ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        """
        self.supported_formats = supported_formats or [
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'
        ]
        
        # Normalize to lowercase
        self.supported_formats = [fmt.lower() for fmt in self.supported_formats]
        
        logger.info(f"Image processor initialized with formats: {self.supported_formats}")
    
    def find_images(
        self,
        directory: str,
        recursive: bool = True
    ) -> List[Path]:
        """
        Find all image files in a directory.
        
        Args:
            directory: Path to search
            recursive: Search subdirectories too
            
        Returns:
            List of Path objects for valid image files
            
        Example:
            >>> processor = ImageProcessor()
            >>> images = processor.find_images("data/images")
            >>> print(f"Found {len(images)} images")
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return []
        
        logger.info(f"Scanning directory: {directory}")
        
        image_paths = []
        
        # Choose search pattern
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        # Find all files
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                # Check extension
                if file_path.suffix.lower() in self.supported_formats:
                    image_paths.append(file_path)
        
        logger.info(f"Found {len(image_paths)} image files")
        return image_paths
    
    def validate_image(self, image_path: Path) -> bool:
        """
        Check if an image can be opened and is valid.
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if image is valid, False otherwise
            
        Why validation?
        - Corrupted files
        - Wrong file extension
        - Unsupported formats
        - Truncated downloads
        """
        try:
            with Image.open(image_path) as img:
                # Try to load image data (lazy loading)
                img.verify()
            
            # Re-open to actually load (verify() closes the file)
            with Image.open(image_path) as img:
                img.load()
            
            return True
            
        except Exception as e:
            logger.warning(f"Invalid image {image_path.name}: {e}")
            return False
    
    def validate_batch(
        self,
        image_paths: List[Path],
        show_progress: bool = True
    ) -> Tuple[List[Path], List[Path]]:
        """
        Validate multiple images.
        
        Args:
            image_paths: List of image paths to validate
            show_progress: Show progress bar
            
        Returns:
            Tuple of (valid_paths, invalid_paths)
        """
        from tqdm import tqdm
        
        valid_paths = []
        invalid_paths = []
        
        iterator = image_paths
        if show_progress:
            iterator = tqdm(
                image_paths,
                desc="🔍 Validating images",
                unit="img"
            )
        
        for path in iterator:
            if self.validate_image(path):
                valid_paths.append(path)
            else:
                invalid_paths.append(path)
        
        logger.info(
            f"Validation complete: {len(valid_paths)} valid, "
            f"{len(invalid_paths)} invalid"
        )
        
        return valid_paths, invalid_paths
    
    def filter_existing(
        self,
        image_paths: List[Path],
        existing_paths: Set[str]
    ) -> List[Path]:
        """
        Filter out images that are already processed.
        
        Args:
            image_paths: List of image paths to check
            existing_paths: Set of paths already in database
            
        Returns:
            List of new (unprocessed) image paths
            
        Why this matters:
        - Re-running the pipeline shouldn't re-process everything
        - Save time and computation
        - Only add new images
        """
        new_paths = []
        
        for path in image_paths:
            # Convert to absolute path for comparison
            abs_path = str(path.absolute())
            
            if abs_path not in existing_paths:
                new_paths.append(path)
        
        skipped = len(image_paths) - len(new_paths)
        
        if skipped > 0:
            logger.info(f"Skipped {skipped} already-processed images")
        
        logger.info(f"{len(new_paths)} new images to process")
        
        return new_paths
    
    def get_image_info(self, image_path: Path) -> dict:
        """
        Get basic information about an image.
        
        Args:
            image_path: Path to image
            
        Returns:
            Dictionary with image information
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'path': str(image_path.absolute()),
                    'filename': image_path.name,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,  # (width, height)
                    'file_size': image_path.stat().st_size,
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get info for {image_path}: {e}")
            return None
    
    def __repr__(self) -> str:
        return f"ImageProcessor(formats={len(self.supported_formats)})"