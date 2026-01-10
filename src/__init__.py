"""
QID - Query Images by Description
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "QID Project"

# Make common imports easier
from .embeddings.image_encoder import ImageEncoder
from .embeddings.text_encoder import TextEncoder
from .database.vector_store import VectorStore
from .database.metadata_store import MetadataStore
from .ingestion.batch_indexer import BatchIndexer
from .query.search_engine import SearchEngine
from .utils.config import get_config
from .utils.logger import setup_logging, get_logger

__all__ = [
    'ImageEncoder',
    'TextEncoder',
    'VectorStore',
    'MetadataStore',
    'BatchIndexer',
    'SearchEngine',
    'get_config',
    'setup_logging',
    'get_logger'
]