"""
Constants for CLI interface.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class CLIDefaults:
    """Default values for CLI arguments."""
    OUTPUT_DIR = 'docs/'
    FORMAT = 'markdown'
    EXCLUDE_MODULES = ['one_time_scripts']
    LOG_LEVEL = 'INFO'
    FILENAME = 'api_documentation'
    INCLUDE_EXAMPLES = True
    INCLUDE_DEPENDENCIES = True
    INCLUDE_INTEGRATION = True


@dataclass
class ArgumentNames:
    """CLI argument names and flags."""
    APP = '--app'
    OUTPUT = '--output'
    OUTPUT_SHORT = '-o'
    FORMAT = '--format'
    FORMAT_SHORT = '-f'
    SINGLE_FILE = '--single-file'
    CONFIG = '--config'
    CONFIG_SHORT = '-c'
    CREATE_CONFIG = '--create-config'
    EXCLUDE_MODULES = '--exclude-modules'
    VERBOSE = '--verbose'
    VERBOSE_SHORT = '-v'
    QUIET = '--quiet'
    QUIET_SHORT = '-q'
    LOG_FILE = '--log-file'
    INCLUDE_EXAMPLES = '--include-examples'
    INCLUDE_DEPENDENCIES = '--include-dependencies'
    INCLUDE_INTEGRATION = '--include-integration'
    VALIDATE_ONLY = '--validate-only'
    DRY_RUN = '--dry-run'


@dataclass
class HelpMessages:
    """Help messages for CLI arguments."""
    PROGRAM_DESCRIPTION = 'Generate API documentation for FastAPI applications'
    
    APP = 'FastAPI application import string (e.g., "core.main:app")'
    OUTPUT = 'Output directory for generated documentation (default: docs/)'
    FORMAT = 'Output format (default: markdown)'
    SINGLE_FILE = 'Generate single documentation file instead of separate module files'
    CONFIG = 'Path to configuration file (JSON format)'
    CREATE_CONFIG = 'Create example configuration file and exit'
    EXCLUDE_MODULES = 'Modules to exclude from documentation (default: one_time_scripts)'
    VERBOSE = 'Enable verbose logging'
    QUIET = 'Enable quiet mode (errors only)'
    LOG_FILE = 'Write logs to file instead of console'
    INCLUDE_EXAMPLES = 'Include usage examples in documentation (default: True)'
    INCLUDE_DEPENDENCIES = 'Include dependency analysis in documentation (default: True)'
    INCLUDE_INTEGRATION = 'Include integration documentation (default: True)'
    VALIDATE_ONLY = 'Only validate documentation without generating files'
    DRY_RUN = 'Show what would be generated without creating files'
    
    EPILOG = """
Examples:
  %(prog)s --app core.main:app --output docs/
  %(prog)s --app core.main:app --format markdown --single-file
  %(prog)s --app core.main:app --config config.json --verbose
  %(prog)s --app core.main:app --exclude-modules one_time_scripts --quiet
            """


@dataclass
class OutputFormats:
    """Available output formats."""
    MARKDOWN = 'markdown'
    JSON = 'json'
    
    @classmethod
    def choices(cls) -> List[str]:
        """Get list of available format choices."""
        return [cls.MARKDOWN, cls.JSON]


@dataclass
class LogLevels:
    """Available logging levels."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


@dataclass
class ExitCodes:
    """Exit codes for CLI application."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    KEYBOARD_INTERRUPT = 130


@dataclass
class ProgressMessages:
    """Messages for progress tracking."""
    LOADING_APP = "Loading FastAPI application..."
    INITIALIZING_GENERATOR = "Initializing documentation generator..."
    ANALYZING_ENDPOINTS = "Analyzing API endpoints..."
    GENERATING_DOCS = "Generating documentation..."
    VALIDATING_DOCS = "Validating documentation..."
    WRITING_FILES = "Writing documentation files..."
    COMPLETED = "Documentation generation completed!"
    
    FOUND_ENDPOINTS = "Found {count} endpoints"
    EXCLUDING_MODULES = "Excluding modules: {modules}"
    GENERATED_FILES = "Generated {count} Markdown files in {path}"
    GENERATED_JSON = "Generated JSON documentation: {file}"
    GENERATED_MARKDOWN = "Generated Markdown documentation: {file}"
    GENERATED_INTEGRATION = "Generated integration documentation: {file}"


@dataclass
class ValidationMessages:
    """Messages for validation results."""
    VALIDATION_PASSED = "✓ Documentation validation passed"
    VALIDATION_FAILED = "✗ Documentation validation failed"
    ERROR_PREFIX = "  ERROR: {error}"
    WARNING_PREFIX = "  WARNING: {warning}"


@dataclass
class ErrorMessages:
    """Error messages for CLI operations."""
    INVALID_APP_STRING = "App string must be in format 'module:attribute'"
    MODULE_NOT_FOUND = "Module '{module}' has no attribute '{attribute}'"
    NOT_FASTAPI_INSTANCE = "'{app_string}' is not a FastAPI instance"
    IMPORT_FAILED = "Failed to import module: {error}"
    APP_LOAD_FAILED = "Failed to load FastAPI app: {error}"
    CONFIG_LOAD_FAILED = "Failed to load configuration: {error}"
    CONFIG_VALIDATION_FAILED = "Configuration validation failed:"
    GENERATION_FAILED = "Documentation generation failed: {error}"
    UNEXPECTED_ERROR = "Unexpected error: {error}"
    INTERRUPTED = "Interrupted by user"
    GENERATION_INTERRUPTED = "Documentation generation interrupted by user"
    REQUIRED_APP_MISSING = "the following arguments are required: --app"


@dataclass
class InfoMessages:
    """Informational messages."""
    LOADED_CONFIG_FROM_FILE = "Loaded configuration from {path}"
    FOUND_CONFIG_FILE = "Found and loaded configuration file"
    USING_DEFAULT_CONFIG = "Using default configuration"
    LOADED_FASTAPI_APP = "Successfully loaded FastAPI app from {app_string}"
    LOGGING_TO_FILE = "Logging to file: {file}"
    DRY_RUN_HEADER = "DRY RUN: Would analyze the following endpoints:"
    DRY_RUN_ENDPOINT = "  {method} {path} ({module})"
    SUMMARY_HEADER = "Documentation Summary:"
    SUMMARY_TOTAL_ENDPOINTS = "  Total endpoints: {count}"
    SUMMARY_MODULES = "  Modules: {count}"
    SUMMARY_AUTH_ENDPOINTS = "  Authenticated endpoints: {count}"
    SUMMARY_PUBLIC_ENDPOINTS = "  Public endpoints: {count}"