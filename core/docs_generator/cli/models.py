"""
Models for CLI configuration and arguments.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class CLIArguments:
    """Represents parsed CLI arguments."""
    app: Optional[str] = None
    output: str = 'docs/'
    format: str = 'markdown'
    single_file: bool = False
    config: Optional[str] = None
    create_config: bool = False
    exclude_modules: List[str] = None
    verbose: bool = False
    quiet: bool = False
    log_file: Optional[str] = None
    include_examples: bool = True
    include_dependencies: bool = True
    include_integration: bool = True
    validate_only: bool = False
    dry_run: bool = False
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.exclude_modules is None:
            self.exclude_modules = ['one_time_scripts']


@dataclass
class LoggingConfiguration:
    """Configuration for logging setup."""
    level: str = "INFO"
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'
    file_path: Optional[str] = None
    console_output: bool = True


@dataclass
class ProgressInfo:
    """Information for progress tracking."""
    message: str
    step: int = 0
    total: int = 0
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total > 0:
            return (self.step / self.total) * 100
        return 0.0


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class GenerationSummary:
    """Summary of documentation generation process."""
    success: bool
    total_endpoints: int
    modules_count: int
    files_generated: List[str]
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.files_generated is None:
            self.files_generated = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []