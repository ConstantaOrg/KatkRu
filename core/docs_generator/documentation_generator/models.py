"""
Data models for documentation generator.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class GeneratorConfig:
    """Configuration for documentation generator."""
    exclude_patterns: List[str]
    output_format: str
    include_examples: bool
    include_dependencies: bool
    include_integration: bool


@dataclass
class DocumentationOverview:
    """Overview information for generated documentation."""
    title: str
    description: str
    total_endpoints: int
    modules_count: int
    generated_at: str


@dataclass
class ValidationResult:
    """Result of documentation validation."""
    valid: bool
    warnings: List[str]
    errors: List[str]


@dataclass
class DocumentationSummary:
    """Summary of generated documentation."""
    total_endpoints: int
    modules: List[str]
    endpoints_by_method: Dict[str, int]
    endpoints_by_module: Dict[str, int]
    auth_required_endpoints: int
    public_endpoints: int