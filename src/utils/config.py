"""
QID - Query Images by Description
Configuration Manager
"""

import yaml
import torch
from pathlib import Path
from typing import Any, Dict


class Config:
    """Manages application configuration."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._setup_directories()
        self._detect_device()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Please create config/config.yaml"
            )
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_directories(self):
        """Create necessary directories."""
        dirs = [
            Path(self._config['model']['cache_dir']),
            Path(self._config['database']['embeddings_path']).parent,
            Path(self._config['database']['metadata_path']).parent,
            Path(self._config['logging']['file']).parent,
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _detect_device(self):
        """Auto-detect best compute device."""
        device_config = self._config['model']['device']
        
        if device_config == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
                print("🎮 GPU detected! Using CUDA")
            elif torch.backends.mps.is_available():
                self.device = "mps"
                print("🍎 Apple Silicon detected! Using MPS")
            else:
                self.device = "cpu"
                print("💻 Using CPU")
        else:
            self.device = device_config
        
        self._config['model']['device'] = self.device
    
    def get(self, key_path: str, default=None):
        """
        Get config value using dot notation.
        Example: config.get('model.name')
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    @property
    def model_name(self) -> str:
        return self.get('model.name')
    
    @property
    def embedding_dim(self) -> int:
        return self.get('database.dimension')
    
    @property
    def batch_size(self) -> int:
        return self.get('images.batch_size')
    
    def __repr__(self) -> str:
        return f"Config(device={self.device}, model={self.model_name})"


# Global config instance
_config = None

def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config