"""
Command Line Interface for API Documentation Generator.
"""

import argparse
import logging
import sys
from typing import Optional
from pathlib import Path

from .generator import DocumentationGenerator
from .config import ConfigManager, DocumentationConfig


class DocumentationCLI:
    """Command line interface for documentation generation."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.config: Optional[DocumentationConfig] = None
        
    def _setup_logging(self, level: str = "INFO") -> logging.Logger:
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
        
        return logger
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            prog='docs-generator',
            description='Generate API documentation for FastAPI applications',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --app core.main:app --output docs/
  %(prog)s --app core.main:app --format markdown --single-file
  %(prog)s --app core.main:app --config config.json --verbose
  %(prog)s --app core.main:app --exclude-modules one_time_scripts --quiet
            """
        )
        
        # Required arguments
        parser.add_argument(
            '--app',
            help='FastAPI application import string (e.g., "core.main:app")'
        )
        
        # Output options
        parser.add_argument(
            '--output', '-o',
            default='docs/',
            help='Output directory for generated documentation (default: docs/)'
        )
        
        parser.add_argument(
            '--format', '-f',
            choices=['markdown', 'json'],
            default='markdown',
            help='Output format (default: markdown)'
        )
        
        parser.add_argument(
            '--single-file',
            action='store_true',
            help='Generate single documentation file instead of separate module files'
        )
        
        # Configuration options
        parser.add_argument(
            '--config', '-c',
            help='Path to configuration file (JSON format)'
        )
        
        parser.add_argument(
            '--create-config',
            action='store_true',
            help='Create example configuration file and exit'
        )
        
        parser.add_argument(
            '--exclude-modules',
            nargs='*',
            default=['one_time_scripts'],
            help='Modules to exclude from documentation (default: one_time_scripts)'
        )
        
        # Logging options
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Enable quiet mode (errors only)'
        )
        
        parser.add_argument(
            '--log-file',
            help='Write logs to file instead of console'
        )
        
        # Analysis options
        parser.add_argument(
            '--include-examples',
            action='store_true',
            default=True,
            help='Include usage examples in documentation (default: True)'
        )
        
        parser.add_argument(
            '--include-dependencies',
            action='store_true',
            default=True,
            help='Include dependency analysis in documentation (default: True)'
        )
        
        parser.add_argument(
            '--include-integration',
            action='store_true',
            default=True,
            help='Include integration documentation (default: True)'
        )
        
        # Validation options
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate documentation without generating files'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without creating files'
        )
        
        return parser
    
    def load_config(self, config_path: Optional[str] = None) -> DocumentationConfig:
        """Load configuration from file or create default."""
        try:
            if config_path:
                # Load from specified file
                config = ConfigManager.load_from_file(config_path)
                self.logger.info(f"Loaded configuration from {config_path}")
            else:
                # Try to find config file automatically
                config = ConfigManager.find_and_load_config()
                if config:
                    self.logger.info("Found and loaded configuration file")
                else:
                    # Use default configuration
                    config = ConfigManager.create_default_config()
                    self.logger.info("Using default configuration")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def load_fastapi_app(self, app_string: str):
        """Load FastAPI application from import string."""
        try:
            # Parse app string (e.g., "core.main:app")
            if ':' not in app_string:
                self.logger.error("App string must be in format 'module:attribute'")
                sys.exit(1)
            
            module_name, app_name = app_string.split(':', 1)
            
            # Import the module
            import importlib
            module = importlib.import_module(module_name)
            
            # Get the app instance
            if not hasattr(module, app_name):
                self.logger.error(f"Module '{module_name}' has no attribute '{app_name}'")
                sys.exit(1)
            
            app = getattr(module, app_name)
            
            # Verify it's a FastAPI instance
            from fastapi import FastAPI
            if not isinstance(app, FastAPI):
                self.logger.error(f"'{app_string}' is not a FastAPI instance")
                sys.exit(1)
            
            self.logger.info(f"Successfully loaded FastAPI app from {app_string}")
            return app
            
        except ImportError as e:
            self.logger.error(f"Failed to import module: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Failed to load FastAPI app: {e}")
            sys.exit(1)
    
    def show_progress(self, message: str, step: int = 0, total: int = 0):
        """Show progress message."""
        if total > 0:
            percentage = (step / total) * 100
            self.logger.info(f"[{step}/{total}] ({percentage:.1f}%) {message}")
        else:
            self.logger.info(f"[PROGRESS] {message}")
    
    def generate_documentation(self, args: argparse.Namespace) -> bool:
        """Generate documentation based on CLI arguments."""
        try:
            # Load configuration
            self.config = self.load_config(args.config)
            
            # Merge CLI arguments with configuration
            self.config = ConfigManager.merge_with_args(self.config, vars(args))
            
            # Validate configuration
            validation_errors = ConfigManager.validate_config(self.config)
            if validation_errors:
                self.logger.error("Configuration validation failed:")
                for error in validation_errors:
                    self.logger.error(f"  - {error}")
                return False
            
            # Load FastAPI application
            self.show_progress("Loading FastAPI application...")
            app = self.load_fastapi_app(self.config.app)
            
            # Create documentation generator
            self.show_progress("Initializing documentation generator...")
            generator = DocumentationGenerator(app)
            
            # Set exclusion patterns based on config
            if self.config.filters.exclude_modules:
                self.logger.info(f"Excluding modules: {', '.join(self.config.filters.exclude_modules)}")
            
            # Analyze endpoints
            self.show_progress("Analyzing API endpoints...")
            endpoints = generator.analyze_endpoints()
            self.show_progress(f"Found {len(endpoints)} endpoints", 1, 4)
            
            if self.config.dry_run:
                self.logger.info("DRY RUN: Would analyze the following endpoints:")
                for endpoint in endpoints:
                    self.logger.info(f"  {endpoint.method} {endpoint.path} ({endpoint.module})")
                return True
            
            # Generate documentation
            self.show_progress("Generating documentation...", 2, 4)
            documentation = generator.generate_documentation()
            
            # Validate documentation if requested
            if self.config.validate_only:
                self.show_progress("Validating documentation...", 3, 4)
                validation = generator.validate_documentation()
                
                if validation['valid']:
                    self.logger.info("✓ Documentation validation passed")
                else:
                    self.logger.error("✗ Documentation validation failed")
                    for error in validation['errors']:
                        self.logger.error(f"  ERROR: {error}")
                
                for warning in validation['warnings']:
                    self.logger.warning(f"  WARNING: {warning}")
                
                return validation['valid']
            
            # Create output directory
            output_path = Path(self.config.output.directory)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate output files
            self.show_progress("Writing documentation files...", 3, 4)
            
            if self.config.output.format == 'json':
                # Generate JSON output
                import json
                json_file = output_path / f"{self.config.output.filename}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(documentation, f, indent=2, default=str)
                self.logger.info(f"Generated JSON documentation: {json_file}")
                
            elif self.config.output.format == 'markdown':
                if self.config.output.single_file:
                    # Generate single Markdown file
                    md_file = output_path / f"{self.config.output.filename}.md"
                    generator.generate_markdown_file(documentation, str(md_file))
                    self.logger.info(f"Generated Markdown documentation: {md_file}")
                else:
                    # Generate separate module files
                    generated_files = generator.generate_module_markdown_files(
                        documentation, str(output_path)
                    )
                    self.logger.info(f"Generated {len(generated_files)} Markdown files in {output_path}")
                    for file_path in generated_files:
                        self.logger.info(f"  - {file_path}")
            
            # Generate integration documentation if requested
            if self.config.analysis.include_integration:
                integration_md = generator.generate_integration_documentation()
                integration_file = output_path / "integration.md"
                with open(integration_file, 'w', encoding='utf-8') as f:
                    f.write(integration_md)
                self.logger.info(f"Generated integration documentation: {integration_file}")
            
            self.show_progress("Documentation generation completed!", 4, 4)
            
            # Show summary
            summary = generator.get_documentation_summary()
            self.logger.info("Documentation Summary:")
            self.logger.info(f"  Total endpoints: {summary.get('total_endpoints', 0)}")
            self.logger.info(f"  Modules: {len(summary.get('modules', []))}")
            self.logger.info(f"  Authenticated endpoints: {summary.get('auth_required_endpoints', 0)}")
            self.logger.info(f"  Public endpoints: {summary.get('public_endpoints', 0)}")
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Documentation generation interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            if hasattr(self.config, 'logging') and self.config.logging.level == 'DEBUG':
                import traceback
                self.logger.error(traceback.format_exc())
            return False
    
    def run(self, argv: Optional[list] = None) -> int:
        """Run the CLI application."""
        try:
            # Parse arguments
            parser = self.create_parser()
            args = parser.parse_args(argv)
            
            # Handle config creation
            if args.create_config:
                from .config import create_config_file
                create_config_file()
                return 0
            
            # Validate required arguments
            if not args.app:
                parser.error("the following arguments are required: --app")
            
            # Setup logging based on arguments
            if args.quiet:
                log_level = "ERROR"
            elif args.verbose:
                log_level = "DEBUG"
            else:
                log_level = "INFO"
            
            # Reconfigure logging
            self.logger = self._setup_logging(log_level)
            
            # Setup file logging if requested
            if args.log_file:
                file_handler = logging.FileHandler(args.log_file)
                file_handler.setLevel(getattr(logging, log_level))
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
                self.logger.info(f"Logging to file: {args.log_file}")
            
            # Generate documentation
            success = self.generate_documentation(args)
            
            return 0 if success else 1
            
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1


def main():
    """Main entry point for the CLI."""
    cli = DocumentationCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()