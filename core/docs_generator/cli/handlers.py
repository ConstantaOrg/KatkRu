"""
Handler functions for CLI operations.
"""

import argparse
import logging
import sys
import json
import importlib
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..documentation_generator import DocumentationGenerator
from ..config import ConfigManager, DocumentationConfig
from .constants import (
    CLIDefaults, ArgumentNames, HelpMessages, OutputFormats, LogLevels, ExitCodes,
    ProgressMessages, ValidationMessages, ErrorMessages, InfoMessages
)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog='docs-generator',
        description=HelpMessages.PROGRAM_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HelpMessages.EPILOG
    )
    
    # Required arguments
    parser.add_argument(
        ArgumentNames.APP,
        help=HelpMessages.APP
    )
    
    # Output options
    parser.add_argument(
        ArgumentNames.OUTPUT, ArgumentNames.OUTPUT_SHORT,
        default=CLIDefaults.OUTPUT_DIR,
        help=HelpMessages.OUTPUT
    )
    
    parser.add_argument(
        ArgumentNames.FORMAT, ArgumentNames.FORMAT_SHORT,
        choices=OutputFormats.choices(),
        default=CLIDefaults.FORMAT,
        help=HelpMessages.FORMAT
    )
    
    parser.add_argument(
        ArgumentNames.SINGLE_FILE,
        action='store_true',
        help=HelpMessages.SINGLE_FILE
    )
    
    # Configuration options
    parser.add_argument(
        ArgumentNames.CONFIG, ArgumentNames.CONFIG_SHORT,
        help=HelpMessages.CONFIG
    )
    
    parser.add_argument(
        ArgumentNames.CREATE_CONFIG,
        action='store_true',
        help=HelpMessages.CREATE_CONFIG
    )
    
    parser.add_argument(
        ArgumentNames.EXCLUDE_MODULES,
        nargs='*',
        default=CLIDefaults.EXCLUDE_MODULES,
        help=HelpMessages.EXCLUDE_MODULES
    )
    
    # Logging options
    parser.add_argument(
        ArgumentNames.VERBOSE, ArgumentNames.VERBOSE_SHORT,
        action='store_true',
        help=HelpMessages.VERBOSE
    )
    
    parser.add_argument(
        ArgumentNames.QUIET, ArgumentNames.QUIET_SHORT,
        action='store_true',
        help=HelpMessages.QUIET
    )
    
    parser.add_argument(
        ArgumentNames.LOG_FILE,
        help=HelpMessages.LOG_FILE
    )
    
    # Analysis options
    parser.add_argument(
        ArgumentNames.INCLUDE_EXAMPLES,
        action='store_true',
        default=CLIDefaults.INCLUDE_EXAMPLES,
        help=HelpMessages.INCLUDE_EXAMPLES
    )
    
    parser.add_argument(
        ArgumentNames.INCLUDE_DEPENDENCIES,
        action='store_true',
        default=CLIDefaults.INCLUDE_DEPENDENCIES,
        help=HelpMessages.INCLUDE_DEPENDENCIES
    )
    
    parser.add_argument(
        ArgumentNames.INCLUDE_INTEGRATION,
        action='store_true',
        default=CLIDefaults.INCLUDE_INTEGRATION,
        help=HelpMessages.INCLUDE_INTEGRATION
    )
    
    # Validation options
    parser.add_argument(
        ArgumentNames.VALIDATE_ONLY,
        action='store_true',
        help=HelpMessages.VALIDATE_ONLY
    )
    
    parser.add_argument(
        ArgumentNames.DRY_RUN,
        action='store_true',
        help=HelpMessages.DRY_RUN
    )
    
    return parser


def setup_logging(level: str = LogLevels.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger('docs_generator')
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Setup file logging if requested
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(InfoMessages.LOGGING_TO_FILE.format(file=log_file))
    
    return logger


def determine_log_level(verbose: bool, quiet: bool) -> str:
    """Determine logging level based on CLI flags."""
    if quiet:
        return LogLevels.ERROR
    elif verbose:
        return LogLevels.DEBUG
    else:
        return LogLevels.INFO


def load_config(config_path: Optional[str], logger: logging.Logger) -> DocumentationConfig:
    """Load configuration from file or create default."""
    try:
        if config_path:
            # Load from specified file
            config = ConfigManager.load_from_file(config_path)
            logger.info(InfoMessages.LOADED_CONFIG_FROM_FILE.format(path=config_path))
        else:
            # Try to find config file automatically
            config = ConfigManager.find_and_load_config()
            if config:
                logger.info(InfoMessages.FOUND_CONFIG_FILE)
            else:
                # Use default configuration
                config = ConfigManager.create_default_config()
                logger.info(InfoMessages.USING_DEFAULT_CONFIG)
        
        return config
        
    except Exception as e:
        logger.error(ErrorMessages.CONFIG_LOAD_FAILED.format(error=e))
        sys.exit(ExitCodes.GENERAL_ERROR)


def validate_config(config: DocumentationConfig, logger: logging.Logger) -> bool:
    """Validate configuration and log errors."""
    validation_errors = ConfigManager.validate_config(config)
    if validation_errors:
        logger.error(ErrorMessages.CONFIG_VALIDATION_FAILED)
        for error in validation_errors:
            logger.error(f"  - {error}")
        return False
    return True


def load_fastapi_app(app_string: str, logger: logging.Logger):
    """Load FastAPI application from import string."""
    try:
        # Parse app string (e.g., "core.main:app")
        if ':' not in app_string:
            logger.error(ErrorMessages.INVALID_APP_STRING)
            sys.exit(ExitCodes.GENERAL_ERROR)
        
        module_name, app_name = app_string.split(':', 1)
        
        # Import the module
        module = importlib.import_module(module_name)
        
        # Get the app instance
        if not hasattr(module, app_name):
            logger.error(ErrorMessages.MODULE_NOT_FOUND.format(
                module=module_name, attribute=app_name
            ))
            sys.exit(ExitCodes.GENERAL_ERROR)
        
        app = getattr(module, app_name)
        
        # Verify it's a FastAPI instance
        from fastapi import FastAPI
        if not isinstance(app, FastAPI):
            logger.error(ErrorMessages.NOT_FASTAPI_INSTANCE.format(app_string=app_string))
            sys.exit(ExitCodes.GENERAL_ERROR)
        
        logger.info(InfoMessages.LOADED_FASTAPI_APP.format(app_string=app_string))
        return app
        
    except ImportError as e:
        logger.error(ErrorMessages.IMPORT_FAILED.format(error=e))
        sys.exit(ExitCodes.GENERAL_ERROR)
    except Exception as e:
        logger.error(ErrorMessages.APP_LOAD_FAILED.format(error=e))
        sys.exit(ExitCodes.GENERAL_ERROR)


def show_progress(message: str, step: int = 0, total: int = 0, logger: logging.Logger = None):
    """Show progress message."""
    if not logger:
        return
        
    if total > 0:
        percentage = (step / total) * 100
        logger.info(f"[{step}/{total}] ({percentage:.1f}%) {message}")
    else:
        logger.info(f"[PROGRESS] {message}")


def handle_dry_run(endpoints: List, logger: logging.Logger):
    """Handle dry run mode - show what would be analyzed."""
    logger.info(InfoMessages.DRY_RUN_HEADER)
    for endpoint in endpoints:
        logger.info(InfoMessages.DRY_RUN_ENDPOINT.format(
            method=endpoint.method,
            path=endpoint.path,
            module=endpoint.module
        ))


def handle_validation_only(generator: DocumentationGenerator, logger: logging.Logger) -> bool:
    """Handle validation-only mode."""
    validation = generator.validate_documentation()
    
    if validation['valid']:
        logger.info(ValidationMessages.VALIDATION_PASSED)
    else:
        logger.error(ValidationMessages.VALIDATION_FAILED)
        for error in validation['errors']:
            logger.error(ValidationMessages.ERROR_PREFIX.format(error=error))
    
    for warning in validation['warnings']:
        logger.warning(ValidationMessages.WARNING_PREFIX.format(warning=warning))
    
    return validation['valid']


def generate_json_output(documentation: Dict[str, Any], output_path: Path, filename: str, logger: logging.Logger):
    """Generate JSON output file."""
    json_file = output_path / f"{filename}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(documentation, f, indent=2, default=str)
    logger.info(ProgressMessages.GENERATED_JSON.format(file=json_file))


def generate_markdown_output(generator: DocumentationGenerator, documentation: Dict[str, Any], 
                           output_path: Path, filename: str, single_file: bool, logger: logging.Logger):
    """Generate Markdown output files."""
    if single_file:
        # Generate single Markdown file
        md_file = output_path / f"{filename}.md"
        generator.generate_markdown_file(documentation, str(md_file))
        logger.info(ProgressMessages.GENERATED_MARKDOWN.format(file=md_file))
    else:
        # Generate separate module files
        generated_files = generator.generate_module_markdown_files(
            documentation, str(output_path)
        )
        logger.info(ProgressMessages.GENERATED_FILES.format(
            count=len(generated_files), path=output_path
        ))
        for file_path in generated_files:
            logger.info(f"  - {file_path}")


def generate_integration_docs(generator: DocumentationGenerator, output_path: Path, 
                            include_integration: bool, logger: logging.Logger):
    """Generate integration documentation if requested."""
    if include_integration:
        integration_md = generator.generate_integration_documentation()
        integration_file = output_path / "integration.md"
        with open(integration_file, 'w', encoding='utf-8') as f:
            f.write(integration_md)
        logger.info(ProgressMessages.GENERATED_INTEGRATION.format(file=integration_file))


def show_generation_summary(generator: DocumentationGenerator, logger: logging.Logger):
    """Show documentation generation summary."""
    summary = generator.get_documentation_summary()
    logger.info(InfoMessages.SUMMARY_HEADER)
    logger.info(InfoMessages.SUMMARY_TOTAL_ENDPOINTS.format(count=summary.total_endpoints))
    logger.info(InfoMessages.SUMMARY_MODULES.format(count=len(summary.modules)))
    logger.info(InfoMessages.SUMMARY_AUTH_ENDPOINTS.format(count=summary.auth_required_endpoints))
    logger.info(InfoMessages.SUMMARY_PUBLIC_ENDPOINTS.format(count=summary.public_endpoints))


def merge_config_with_args(config: DocumentationConfig, args: Dict[str, Any]) -> DocumentationConfig:
    """Merge CLI arguments with configuration."""
    return ConfigManager.merge_with_args(config, args)


def create_config_file():
    """Create example configuration file."""
    from ..config import create_config_file
    create_config_file()


def run_generation_process(config: DocumentationConfig, logger: logging.Logger) -> bool:
    """Run the complete documentation generation process."""
    try:
        # Load FastAPI application
        show_progress(ProgressMessages.LOADING_APP, logger=logger)
        app = load_fastapi_app(config.app, logger)
        
        # Create documentation generator
        show_progress(ProgressMessages.INITIALIZING_GENERATOR, logger=logger)
        generator = DocumentationGenerator(app)
        
        # Set exclusion patterns based on config
        if config.filters.exclude_modules:
            logger.info(ProgressMessages.EXCLUDING_MODULES.format(
                modules=', '.join(config.filters.exclude_modules)
            ))
        
        # Analyze endpoints
        show_progress(ProgressMessages.ANALYZING_ENDPOINTS, logger=logger)
        endpoints = generator.analyze_endpoints()
        show_progress(ProgressMessages.FOUND_ENDPOINTS.format(count=len(endpoints)), 1, 4, logger)
        
        if config.dry_run:
            handle_dry_run(endpoints, logger)
            return True
        
        # Generate documentation
        show_progress(ProgressMessages.GENERATING_DOCS, 2, 4, logger)
        documentation = generator.generate_documentation()
        
        # Validate documentation if requested
        if config.validate_only:
            show_progress(ProgressMessages.VALIDATING_DOCS, 3, 4, logger)
            return handle_validation_only(generator, logger)
        
        # Create output directory
        output_path = Path(config.output.directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate output files
        show_progress(ProgressMessages.WRITING_FILES, 3, 4, logger)
        
        if config.output.format == OutputFormats.JSON:
            generate_json_output(documentation, output_path, config.output.filename, logger)
        elif config.output.format == OutputFormats.MARKDOWN:
            generate_markdown_output(
                generator, documentation, output_path, config.output.filename,
                config.output.single_file, logger
            )
        
        # Generate integration documentation if requested
        generate_integration_docs(generator, output_path, config.analysis.include_integration, logger)
        
        show_progress(ProgressMessages.COMPLETED, 4, 4, logger)
        
        # Show summary
        show_generation_summary(generator, logger)
        
        return True
        
    except KeyboardInterrupt:
        logger.info(ErrorMessages.GENERATION_INTERRUPTED)
        return False
    except Exception as e:
        logger.error(ErrorMessages.GENERATION_FAILED.format(error=e))
        if hasattr(config, 'logging') and config.logging.level == LogLevels.DEBUG:
            import traceback
            logger.error(traceback.format_exc())
        return False