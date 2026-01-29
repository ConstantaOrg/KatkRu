"""
Configuration management for API Documentation Generator.
"""

from typing import Dict, Any, List, Optional

from .models import DocumentationConfig
from .constants import ConfigFileNames
from . import handlers


class ConfigManager:
    """Manager for loading and validating configuration."""
    
    DEFAULT_CONFIG_NAMES = ConfigFileNames.all_names()
    
    @classmethod
    def create_default_config(cls) -> DocumentationConfig:
        """Create default configuration."""
        return handlers.create_default_config()
    
    @classmethod
    def load_from_file(cls, config_path: str) -> DocumentationConfig:
        """Load configuration from JSON file."""
        return handlers.load_from_file(config_path)
    
    @classmethod
    def find_and_load_config(cls, start_dir: str = ".") -> Optional[DocumentationConfig]:
        """Find and load configuration file from default locations."""
        return handlers.find_and_load_config(start_dir)
    
    @classmethod
    def _create_config_from_dict(cls, config_data: Dict[str, Any]) -> DocumentationConfig:
        """Create configuration from dictionary."""
        return handlers.create_config_from_dict(config_data)
    
    @classmethod
    def save_to_file(cls, config: DocumentationConfig, config_path: str):
        """Save configuration to JSON file."""
        return handlers.save_to_file(config, config_path)
    
    @classmethod
    def merge_with_args(cls, config: DocumentationConfig, args_dict: Dict[str, Any]) -> DocumentationConfig:
        """Merge configuration with command line arguments."""
        return handlers.merge_with_args(config, args_dict)
    
    @classmethod
    def validate_config(cls, config: DocumentationConfig) -> List[str]:
        """Validate configuration and return list of errors."""
        return handlers.validate_config(config)
    
    @classmethod
    def create_example_config(cls) -> str:
        """Create an example configuration file content."""
        return handlers.create_example_config()


def create_config_file(output_path: str = ConfigFileNames.PRIMARY):
    """Create an example configuration file."""
    handlers.create_config_file_content(output_path)


if __name__ == '__main__':
    # Create example config file when run directly
    create_config_file()