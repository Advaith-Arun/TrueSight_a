"""
Configuration loader for TrueSight application.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage application configuration."""
    
    def __init__(self, config_path: str = 'configs/config.yaml'):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"✅ Configuration loaded from {self.config_path}")
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dots).
        
        Args:
            key: Configuration key (e.g., 'explainability.enabled')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary."""
        return self._config
    
    def is_gradcam_enabled(self) -> bool:
        """Check if Grad-CAM is enabled."""
        return self.get('explainability.enabled', False)
    
    def get_gradcam_config(self) -> Dict[str, Any]:
        """Get Grad-CAM configuration section."""
        return self.get('explainability', {})


# Global config instance
_config_instance = None

def get_config() -> ConfigLoader:
    """
    Get or create global configuration instance (singleton pattern).
    
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
