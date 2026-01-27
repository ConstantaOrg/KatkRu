"""
Configuration management for API Documentation Generator.
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    format: str = "markdown"  # markdown, json
    directory: str = "docs/"
    single_file: bool = False
    filename: str = "api_documentation"
    
    def __post_init__(self):
        """Validate output configuration."""
        if self.format not in ["markdown", "json"]:
            raise ValueError(f"Invalid output format: {self.format}")


@dataclass
class AnalysisConfig:
    """Configuration for analysis options."""
    include_examples: bool = True
    include_dependencies: bool = True
    include_integration: bool = True
    include_sql_queries: bool = True
    trace_depth: int = 5  # Maximum depth for dependency tracing
    
    
@dataclass
class FilterConfig:
    """Configuration for filtering endpoints and modules."""
    exclude_modules: List[str] = None
    exclude_endpoints: List[str] = None
    include_only_modules: List[str] = None
    exclude_patterns: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.exclude_modules is None:
            self.exclude_modules = ["one_time_scripts"]
        if self.exclude_endpoints is None:
            self.exclude_endpoints = []
        if self.include_only_modules is None:
            self.include_only_modules = []
        if self.exclude_patterns is None:
            self.exclude_patterns = ["/docs", "/redoc", "/openapi.json"]


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    file: Optional[str] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    def __post_init__(self):
        """Validate logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")
        self.level = self.level.upper()


@dataclass
class DocumentationConfig:
    """Main configuration class for documentation generator."""
    app: str = ""  # FastAPI app import string
    output: OutputConfig = None
    analysis: AnalysisConfig = None
    filters: FilterConfig = None
    logging: LoggingConfig = None
    
    # Additional options
    dry_run: bool = False
    validate_only: bool = False
    
    def __post_init__(self):
        """Initialize nested configurations."""
        if self.output is None:
            self.output = OutputConfig()
        if self.analysis is None:
            self.analysis = AnalysisConfig()
        if self.filters is None:
            self.filters = FilterConfig()
        if self.logging is None:
            self.logging = LoggingConfig()


class ConfigManager:
    """Manager for loading and validating configuration."""
    
    DEFAULT_CONFIG_NAMES = [
        "docs-generator.json",
        "docs_generator.json", 
        ".docs-generator.json",
        "config/docs-generator.json"
    ]
    
    @classmethod
    def create_default_config(cls) -> DocumentationConfig:
        """Create default configuration."""
        return DocumentationConfig()
    
    @classmethod
    def load_from_file(cls, config_path: str) -> DocumentationConfig:
        """Load configuration from JSON file."""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return cls._create_config_from_dict(config_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {config_path}: {e}")
    
    @classmethod
    def find_and_load_config(cls, start_dir: str = ".") -> Optional[DocumentationConfig]:
        """Find and load configuration file from default locations."""
        start_path = Path(start_dir).resolve()
        
        # Search in current directory and parent directories
        for path in [start_path] + list(start_path.parents):
            for config_name in cls.DEFAULT_CONFIG_NAMES:
                config_path = path / config_name
                if config_path.exists():
                    try:
                        return cls.load_from_file(str(config_path))
                    except Exception:
                        # Continue searching if this config file is invalid
                        continue
        
        return None
    
    @classmethod
    def _create_config_from_dict(cls, config_data: Dict[str, Any]) -> DocumentationConfig:
        """Create configuration from dictionary."""
        # Extract nested configurations
        output_data = config_data.pop('output', {})
        analysis_data = config_data.pop('analysis', {})
        filters_data = config_data.pop('filters', {})
        logging_data = config_data.pop('logging', {})
        
        # Create nested config objects
        output_config = OutputConfig(**output_data)
        analysis_config = AnalysisConfig(**analysis_data)
        filters_config = FilterConfig(**filters_data)
        logging_config = LoggingConfig(**logging_data)
        
        # Create main config
        config = DocumentationConfig(
            output=output_config,
            analysis=analysis_config,
            filters=filters_config,
            logging=logging_config,
            **config_data
        )
        
        return config
    
    @classmethod
    def save_to_file(cls, config: DocumentationConfig, config_path: str):
        """Save configuration to JSON file."""
        try:
            # Convert to dictionary
            config_dict = asdict(config)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
                
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration to {config_path}: {e}")
    
    @classmethod
    def merge_with_args(cls, config: DocumentationConfig, args_dict: Dict[str, Any]) -> DocumentationConfig:
        """Merge configuration with command line arguments."""
        # Create a copy of the config
        merged_config = DocumentationConfig(
            app=args_dict.get('app', config.app),
            dry_run=args_dict.get('dry_run', config.dry_run),
            validate_only=args_dict.get('validate_only', config.validate_only)
        )
        
        # Merge output configuration
        merged_config.output = OutputConfig(
            format=args_dict.get('format', config.output.format),
            directory=args_dict.get('output', config.output.directory),
            single_file=args_dict.get('single_file', config.output.single_file),
            filename=config.output.filename
        )
        
        # Merge analysis configuration
        merged_config.analysis = AnalysisConfig(
            include_examples=args_dict.get('include_examples', config.analysis.include_examples),
            include_dependencies=args_dict.get('include_dependencies', config.analysis.include_dependencies),
            include_integration=args_dict.get('include_integration', config.analysis.include_integration),
            include_sql_queries=config.analysis.include_sql_queries,
            trace_depth=config.analysis.trace_depth
        )
        
        # Merge filter configuration
        exclude_modules = args_dict.get('exclude_modules')
        if exclude_modules is not None:
            merged_config.filters = FilterConfig(
                exclude_modules=exclude_modules,
                exclude_endpoints=config.filters.exclude_endpoints,
                include_only_modules=config.filters.include_only_modules,
                exclude_patterns=config.filters.exclude_patterns
            )
        else:
            merged_config.filters = config.filters
        
        # Merge logging configuration
        log_level = "INFO"
        if args_dict.get('quiet'):
            log_level = "ERROR"
        elif args_dict.get('verbose'):
            log_level = "DEBUG"
        
        merged_config.logging = LoggingConfig(
            level=log_level,
            file=args_dict.get('log_file', config.logging.file),
            format=config.logging.format,
            date_format=config.logging.date_format
        )
        
        return merged_config
    
    @classmethod
    def validate_config(cls, config: DocumentationConfig) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate app string
        if not config.app:
            errors.append("FastAPI app import string is required")
        elif ':' not in config.app:
            errors.append("App string must be in format 'module:attribute'")
        
        # Validate output directory
        if not config.output.directory:
            errors.append("Output directory is required")
        
        # Validate trace depth
        if config.analysis.trace_depth < 1:
            errors.append("Trace depth must be at least 1")
        
        # Validate exclude patterns
        if config.filters.exclude_modules and config.filters.include_only_modules:
            errors.append("Cannot specify both exclude_modules and include_only_modules")
        
        return errors
    
    @classmethod
    def create_example_config(cls) -> str:
        """Create an example configuration file content."""
        example_config = {
            "app": "core.main:app",
            "output": {
                "format": "markdown",
                "directory": "docs/",
                "single_file": False,
                "filename": "api_documentation"
            },
            "analysis": {
                "include_examples": True,
                "include_dependencies": True,
                "include_integration": True,
                "include_sql_queries": True,
                "trace_depth": 5
            },
            "filters": {
                "exclude_modules": ["one_time_scripts"],
                "exclude_endpoints": [],
                "include_only_modules": [],
                "exclude_patterns": ["/docs", "/redoc", "/openapi.json"]
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S"
            },
            "dry_run": False,
            "validate_only": False
        }
        
        return json.dumps(example_config, indent=2)


def create_config_file(output_path: str = "docs-generator.json"):
    """Create an example configuration file."""
    try:
        example_content = ConfigManager.create_example_config()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        print(f"Created example configuration file: {output_path}")
        print("Edit this file to customize your documentation generation settings.")
        
    except Exception as e:
        print(f"Failed to create configuration file: {e}")


if __name__ == '__main__':
    # Create example config file when run directly
    create_config_file()