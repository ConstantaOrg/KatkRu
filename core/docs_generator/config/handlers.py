"""
Handler functions for configuration management.
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from pathlib import Path

from .models import (
    DocumentationConfig, OutputConfig, AnalysisConfig, 
    FilterConfig, LoggingConfig
)
from .constants import (
    ConfigDefaults, ConfigFileNames, OutputFormats, LogLevels,
    ValidationMessages, ErrorMessages, InfoMessages, ExampleConfigTemplate
)


def create_default_config() -> DocumentationConfig:
    """Create default configuration."""
    return DocumentationConfig()


def load_from_file(config_path: str) -> DocumentationConfig:
    """Load configuration from JSON file."""
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(ErrorMessages.FILE_NOT_FOUND.format(path=config_path))
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return create_config_from_dict(config_data)
        
    except json.JSONDecodeError as e:
        raise ValueError(ErrorMessages.INVALID_JSON.format(path=config_path, error=e))
    except Exception as e:
        raise RuntimeError(ErrorMessages.LOAD_FAILED.format(path=config_path, error=e))


def find_and_load_config(start_dir: str = ".") -> Optional[DocumentationConfig]:
    """Find and load configuration file from default locations."""
    start_path = Path(start_dir).resolve()
    
    # Search in current directory and parent directories
    for path in [start_path] + list(start_path.parents):
        for config_name in ConfigFileNames.all_names():
            config_path = path / config_name
            if config_path.exists():
                try:
                    return load_from_file(str(config_path))
                except Exception:
                    # Continue searching if this config file is invalid
                    continue
    
    return None


def create_config_from_dict(config_data: Dict[str, Any]) -> DocumentationConfig:
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


def save_to_file(config: DocumentationConfig, config_path: str):
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
        raise RuntimeError(ErrorMessages.SAVE_FAILED.format(path=config_path, error=e))


def merge_with_args(config: DocumentationConfig, args_dict: Dict[str, Any]) -> DocumentationConfig:
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
    log_level = LogLevels.INFO
    if args_dict.get('quiet'):
        log_level = LogLevels.ERROR
    elif args_dict.get('verbose'):
        log_level = LogLevels.DEBUG
    
    merged_config.logging = LoggingConfig(
        level=log_level,
        file=args_dict.get('log_file', config.logging.file),
        format=config.logging.format,
        date_format=config.logging.date_format
    )
    
    return merged_config


def validate_config(config: DocumentationConfig) -> List[str]:
    """Validate configuration and return list of errors."""
    errors = []
    
    # Validate app string
    if not config.app:
        errors.append(ValidationMessages.MISSING_APP)
    elif ':' not in config.app:
        errors.append(ValidationMessages.INVALID_APP_FORMAT)
    
    # Validate output directory
    if not config.output.directory:
        errors.append(ValidationMessages.MISSING_OUTPUT_DIR)
    
    # Validate trace depth
    if config.analysis.trace_depth < 1:
        errors.append(ValidationMessages.INVALID_TRACE_DEPTH)
    
    # Validate exclude patterns
    if config.filters.exclude_modules and config.filters.include_only_modules:
        errors.append(ValidationMessages.CONFLICTING_FILTERS)
    
    return errors


def create_example_config() -> str:
    """Create an example configuration file content."""
    example_config = ExampleConfigTemplate.get_template()
    return json.dumps(example_config, indent=2)


def create_config_file_content(output_path: str = ConfigFileNames.PRIMARY):
    """Create an example configuration file."""
    try:
        example_content = create_example_config()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        print(InfoMessages.CONFIG_CREATED.format(path=output_path))
        print(InfoMessages.CONFIG_EDIT_HINT)
        
    except Exception as e:
        print(ErrorMessages.CREATE_FAILED.format(error=e))