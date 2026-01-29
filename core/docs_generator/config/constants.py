"""
Constants for configuration management.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ConfigDefaults:
    """Default configuration values."""
    OUTPUT_FORMAT = "markdown"
    OUTPUT_DIRECTORY = "docs/"
    FILENAME = "api_documentation"
    SINGLE_FILE = False
    
    INCLUDE_EXAMPLES = True
    INCLUDE_DEPENDENCIES = True
    INCLUDE_INTEGRATION = True
    INCLUDE_SQL_QUERIES = True
    TRACE_DEPTH = 5
    
    EXCLUDE_MODULES = ["one_time_scripts"]
    EXCLUDE_PATTERNS = ["/docs", "/redoc", "/openapi.json"]
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    DRY_RUN = False
    VALIDATE_ONLY = False


@dataclass
class ConfigFileNames:
    """Default configuration file names to search for."""
    PRIMARY = "docs-generator.json"
    ALTERNATIVE = "docs_generator.json"
    HIDDEN = ".docs-generator.json"
    SUBDIRECTORY = "config/docs-generator.json"
    
    @classmethod
    def all_names(cls) -> List[str]:
        """Get all configuration file names."""
        return [
            cls.PRIMARY,
            cls.ALTERNATIVE,
            cls.HIDDEN,
            cls.SUBDIRECTORY
        ]


@dataclass
class OutputFormats:
    """Available output formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    
    @classmethod
    def valid_formats(cls) -> List[str]:
        """Get list of valid output formats."""
        return [cls.MARKDOWN, cls.JSON]


@dataclass
class LogLevels:
    """Available logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    
    @classmethod
    def valid_levels(cls) -> List[str]:
        """Get list of valid logging levels."""
        return [cls.DEBUG, cls.INFO, cls.WARNING, cls.ERROR]


@dataclass
class ValidationMessages:
    """Validation error messages."""
    MISSING_APP = "FastAPI app import string is required"
    INVALID_APP_FORMAT = "App string must be in format 'module:attribute'"
    MISSING_OUTPUT_DIR = "Output directory is required"
    INVALID_TRACE_DEPTH = "Trace depth must be at least 1"
    CONFLICTING_FILTERS = "Cannot specify both exclude_modules and include_only_modules"


@dataclass
class ErrorMessages:
    """Error messages for configuration operations."""
    FILE_NOT_FOUND = "Configuration file not found: {path}"
    INVALID_JSON = "Invalid JSON in configuration file {path}: {error}"
    LOAD_FAILED = "Failed to load configuration from {path}: {error}"
    SAVE_FAILED = "Failed to save configuration to {path}: {error}"
    CREATE_FAILED = "Failed to create configuration file: {error}"


@dataclass
class InfoMessages:
    """Informational messages."""
    CONFIG_CREATED = "Created example configuration file: {path}"
    CONFIG_EDIT_HINT = "Edit this file to customize your documentation generation settings."


@dataclass
class ExampleConfigTemplate:
    """Template for example configuration."""
    
    @classmethod
    def get_template(cls) -> Dict[str, Any]:
        """Get example configuration template."""
        return {
            "app": "core.main:app",
            "output": {
                "format": ConfigDefaults.OUTPUT_FORMAT,
                "directory": ConfigDefaults.OUTPUT_DIRECTORY,
                "single_file": ConfigDefaults.SINGLE_FILE,
                "filename": ConfigDefaults.FILENAME
            },
            "analysis": {
                "include_examples": ConfigDefaults.INCLUDE_EXAMPLES,
                "include_dependencies": ConfigDefaults.INCLUDE_DEPENDENCIES,
                "include_integration": ConfigDefaults.INCLUDE_INTEGRATION,
                "include_sql_queries": ConfigDefaults.INCLUDE_SQL_QUERIES,
                "trace_depth": ConfigDefaults.TRACE_DEPTH
            },
            "filters": {
                "exclude_modules": ConfigDefaults.EXCLUDE_MODULES.copy(),
                "exclude_endpoints": [],
                "include_only_modules": [],
                "exclude_patterns": ConfigDefaults.EXCLUDE_PATTERNS.copy()
            },
            "logging": {
                "level": ConfigDefaults.LOG_LEVEL,
                "file": None,
                "format": ConfigDefaults.LOG_FORMAT,
                "date_format": ConfigDefaults.LOG_DATE_FORMAT
            },
            "dry_run": ConfigDefaults.DRY_RUN,
            "validate_only": ConfigDefaults.VALIDATE_ONLY
        }