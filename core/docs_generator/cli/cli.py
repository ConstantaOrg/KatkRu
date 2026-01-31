"""
Command Line Interface for API Documentation Generator.
"""

import logging
import sys
from typing import Optional

from ..config import DocumentationConfig
from .constants import ExitCodes, ErrorMessages
from . import handlers


class DocumentationCLI:
    """Command line interface for documentation generation."""
    
    def __init__(self):
        self.logger = handlers.setup_logging()
        self.config: Optional[DocumentationConfig] = None
        
    def _setup_logging(self, level: str = "INFO") -> logging.Logger:
        """Setup logging configuration."""
        return handlers.setup_logging(level)
    
    def create_parser(self):
        """Create command line argument parser."""
        return handlers.create_parser()
    
    def load_config(self, config_path: Optional[str] = None) -> DocumentationConfig:
        """Load configuration from file or create default."""
        return handlers.load_config(config_path, self.logger)
    
    def load_fastapi_app(self, app_string: str):
        """Load FastAPI application from import string."""
        return handlers.load_fastapi_app(app_string, self.logger)
    
    def show_progress(self, message: str, step: int = 0, total: int = 0):
        """Show progress message."""
        handlers.show_progress(message, step, total, self.logger)
    
    def generate_documentation(self, args) -> bool:
        """Generate documentation based on CLI arguments."""
        try:
            # Load configuration
            self.config = self.load_config(args.config)
            
            # Merge CLI arguments with configuration
            self.config = handlers.merge_config_with_args(self.config, vars(args))
            
            # Validate configuration
            if not handlers.validate_config(self.config, self.logger):
                return False
            
            # Run generation process
            return handlers.run_generation_process(self.config, self.logger)
            
        except KeyboardInterrupt:
            self.logger.info(ErrorMessages.GENERATION_INTERRUPTED)
            return False
        except Exception as e:
            self.logger.error(ErrorMessages.GENERATION_FAILED.format(error=e))
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
                handlers.create_config_file()
                return ExitCodes.SUCCESS
            
            # Validate required arguments
            if not args.app:
                parser.error(ErrorMessages.REQUIRED_APP_MISSING)
            
            # Setup logging based on arguments
            log_level = handlers.determine_log_level(args.verbose, args.quiet)
            
            # Reconfigure logging
            self.logger = handlers.setup_logging(log_level, args.log_file)
            
            # Generate documentation
            success = self.generate_documentation(args)
            
            return ExitCodes.SUCCESS if success else ExitCodes.GENERAL_ERROR
            
        except KeyboardInterrupt:
            self.logger.info(ErrorMessages.INTERRUPTED)
            return ExitCodes.KEYBOARD_INTERRUPT
        except Exception as e:
            self.logger.error(ErrorMessages.UNEXPECTED_ERROR.format(error=e))
            return ExitCodes.GENERAL_ERROR


def main():
    """Main entry point for the CLI."""
    cli = DocumentationCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()