"""
Data models for response schema analyzer.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ReturnStatement:
    """Represents a return statement found in endpoint function."""
    line_number: int
    content: str
    raw_line: str


@dataclass
class EndpointAnalysis:
    """Analysis result for a single API endpoint."""
    method: str
    path: Optional[str]
    function_name: str
    line_number: int
    return_statements: List[ReturnStatement]
    file_path: str
    
    def __post_init__(self):
        """Validate endpoint analysis data."""
        if not self.method:
            raise ValueError("Method is required")
        if not self.function_name:
            raise ValueError("Function name is required")


@dataclass
class SchemaAnalysis:
    """Analysis result for suggested response schema."""
    class_name: str
    suggested_base_classes: List[str]
    return_patterns: List[str]
    method: str
    function_name: str
    confidence_score: float = 0.0
    
    def __post_init__(self):
        """Calculate confidence score based on patterns."""
        if not self.confidence_score:
            self.confidence_score = self._calculate_confidence()
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence score for schema suggestion."""
        score = 0.0
        
        # Base score for having return statements
        if self.return_patterns:
            score += 0.3
        
        # Score for having suggested base classes
        if self.suggested_base_classes:
            score += 0.4
        
        # Score for method-specific patterns
        method_patterns = {
            'GET': ['data', 'list', 'items'],
            'POST': ['id', 'created', 'success'],
            'PUT': ['updated', 'success'],
            'DELETE': ['deleted', 'success']
        }
        
        if self.method in method_patterns:
            for pattern in method_patterns[self.method]:
                if any(pattern in ret_pattern.lower() for ret_pattern in self.return_patterns):
                    score += 0.1
        
        return min(score, 1.0)


@dataclass
class FileAnalysisResult:
    """Result of analyzing a single API file."""
    file_path: str
    endpoints: List[EndpointAnalysis]
    analysis_success: bool
    error_message: Optional[str] = None
    
    @property
    def endpoint_count(self) -> int:
        """Get number of endpoints found in file."""
        return len(self.endpoints)


@dataclass
class AnalysisReport:
    """Complete analysis report for all API files."""
    file_results: Dict[str, FileAnalysisResult]
    total_endpoints: int
    total_files: int
    successful_files: int
    
    @classmethod
    def from_file_results(cls, file_results: Dict[str, FileAnalysisResult]) -> 'AnalysisReport':
        """Create analysis report from file results."""
        total_endpoints = sum(result.endpoint_count for result in file_results.values())
        total_files = len(file_results)
        successful_files = sum(1 for result in file_results.values() if result.analysis_success)
        
        return cls(
            file_results=file_results,
            total_endpoints=total_endpoints,
            total_files=total_files,
            successful_files=successful_files
        )
    
    @property
    def success_rate(self) -> float:
        """Calculate analysis success rate."""
        if self.total_files == 0:
            return 0.0
        return self.successful_files / self.total_files