"""
Configuration models and dataclasses.
"""

from dataclasses import dataclass
from typing import List, Optional


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