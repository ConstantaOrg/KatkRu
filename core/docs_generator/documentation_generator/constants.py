"""
Constants for documentation generator.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ExclusionPatterns:
    """Default exclusion patterns for endpoints."""
    PATTERNS: List[str] = None
    
    def __post_init__(self):
        if self.PATTERNS is None:
            self.PATTERNS = [
                'one_time_scripts',
                '/docs',
                '/redoc',
                '/openapi.json'
            ]


@dataclass
class OutputFormats:
    """Available output formats."""
    MARKDOWN: str = 'markdown'
    JSON: str = 'json'
    HTML: str = 'html'


@dataclass
class DocumentationTemplates:
    """Templates for documentation sections."""
    OVERVIEW_TITLE: str = 'API Documentation - Система управления расписанием'
    OVERVIEW_DESCRIPTION: str = 'Техническая документация для API системы управления расписанием учебного заведения'
    
    INTEGRATION_TITLE: str = 'Интеграции и База Данных'
    INTEGRATION_DESCRIPTION: str = '*Подробная документация по интеграциям доступна в отдельном разделе.*'
    
    DEPENDENCY_TITLE: str = 'Dependency Analysis'
    DEPENDENCY_DESCRIPTION: str = 'This section provides an overview of the dependency relationships between endpoints.'
    
    ERROR_TITLE: str = 'Documentation Generation Error'


@dataclass
class MarkdownHeaders:
    """Markdown header templates."""
    MAIN_TITLE: str = "# {title}\n"
    SECTION_TITLE: str = "## {title}\n"
    SUBSECTION_TITLE: str = "### {title}\n"
    SUBSUBSECTION_TITLE: str = "#### {title}"
    
    TABLE_HEADER: str = "| Method | Path | Function | Auth Required | Description |"
    TABLE_SEPARATOR: str = "|--------|------|----------|---------------|-------------|"
    
    STATS_TABLE_HEADER: str = "| Method | Count |"
    STATS_TABLE_SEPARATOR: str = "|--------|-------|"


@dataclass
class ValidationMessages:
    """Validation error and warning messages."""
    NO_ENDPOINTS: str = 'No endpoints analyzed'
    NO_MODULES: str = 'No module documentation generated'
    ENDPOINTS_WITHOUT_DESC: str = '{count} endpoints without descriptions'
    ENDPOINTS_WITHOUT_DEPS: str = '{count} endpoints without traced dependencies'
    VALIDATION_FAILED: str = 'Validation failed: {error}'


@dataclass
class FileNames:
    """Default file names for output."""
    API_DOCUMENTATION: str = "api_documentation.md"
    README: str = "README.md"
    DOCS_DIR: str = "docs"


# Create instances for easy access
EXCLUSION_PATTERNS = ExclusionPatterns()
OUTPUT_FORMATS = OutputFormats()
DOCUMENTATION_TEMPLATES = DocumentationTemplates()
MARKDOWN_HEADERS = MarkdownHeaders()
VALIDATION_MESSAGES = ValidationMessages()
FILE_NAMES = FileNames()