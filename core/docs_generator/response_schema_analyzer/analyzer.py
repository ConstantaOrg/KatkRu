"""
Main analyzer class for response schema analysis.
"""

from pathlib import Path
from typing import Dict, List

from .models import AnalysisReport, FileAnalysisResult, EndpointAnalysis, SchemaAnalysis
from .handlers import (
    analyze_file_content, suggest_response_schema, generate_schema_code,
    format_analysis_summary
)
from .constants import FILE_PATTERNS, ANALYSIS_CONFIG


class ResponseSchemaAnalyzer:
    """Analyzes API endpoints and suggests response schemas."""
    
    def __init__(self, api_dir: str = "core/api"):
        """Initialize analyzer with API directory path."""
        self.api_dir = Path(api_dir)
        self.analysis_results: Dict[str, FileAnalysisResult] = {}
    
    def analyze_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze a single API file."""
        return analyze_file_content(file_path)
    
    def analyze_all_files(self) -> AnalysisReport:
        """Analyze all API files in the directory."""
        results = {}
        
        # Analyze files in root API directory
        for file_path in self.api_dir.glob(f"*{FILE_PATTERNS.API_FILE_EXTENSION}"):
            if file_path.name not in FILE_PATTERNS.EXCLUDED_FILES:
                result = self.analyze_file(file_path)
                results[file_path.name] = result
        
        # Analyze files in subdirectories
        for subdir in self.api_dir.iterdir():
            if (subdir.is_dir() and 
                subdir.name not in FILE_PATTERNS.EXCLUDED_DIRS):
                
                for file_path in subdir.glob(f"*{FILE_PATTERNS.API_FILE_EXTENSION}"):
                    if file_path.name not in FILE_PATTERNS.EXCLUDED_FILES:
                        result = self.analyze_file(file_path)
                        key = f"{subdir.name}/{file_path.name}"
                        results[key] = result
        
        # Store results and create report
        self.analysis_results = results
        return AnalysisReport.from_file_results(results)
    
    def get_endpoint_schemas(self, file_key: str) -> List[SchemaAnalysis]:
        """Get suggested schemas for endpoints in a specific file."""
        if file_key not in self.analysis_results:
            return []
        
        file_result = self.analysis_results[file_key]
        schemas = []
        
        for endpoint in file_result.endpoints:
            schema = suggest_response_schema(endpoint)
            schemas.append(schema)
        
        return schemas
    
    def generate_schema_code_for_file(self, file_key: str) -> str:
        """Generate Python code for all schemas in a file."""
        schemas = self.get_endpoint_schemas(file_key)
        
        if not schemas:
            return "# No endpoints found in this file"
        
        code_parts = [
            "from pydantic import BaseModel",
            "from typing import Any, List, Optional, Dict",
            "",
            "# Generated response schemas",
            ""
        ]
        
        for schema in schemas:
            code = generate_schema_code(schema)
            code_parts.append(code)
            code_parts.append("")
        
        return '\n'.join(code_parts)
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        if not self.analysis_results:
            # Run analysis if not done yet
            report_data = self.analyze_all_files()
        else:
            report_data = AnalysisReport.from_file_results(self.analysis_results)
        
        report_parts = [
            "# Response Schema Analysis Report",
            "",
            f"**Analysis Summary:**",
            f"- Total files analyzed: {report_data.total_files}",
            f"- Successfully analyzed: {report_data.successful_files}",
            f"- Total endpoints found: {report_data.total_endpoints}",
            f"- Success rate: {report_data.success_rate:.1%}",
            "",
        ]
        
        # Add detailed file analysis
        for file_key, file_result in report_data.file_results.items():
            report_parts.extend(self._generate_file_report_section(file_key, file_result))
        
        return '\n'.join(report_parts)
    
    def _generate_file_report_section(self, file_key: str, 
                                    file_result: FileAnalysisResult) -> List[str]:
        """Generate report section for a single file."""
        section = [f"## {file_key}", ""]
        
        if not file_result.analysis_success:
            section.extend([
                f"**Analysis failed:** {file_result.error_message}",
                "",
                "---",
                ""
            ])
            return section
        
        if not file_result.endpoints:
            section.extend([
                "No API endpoints found in this file.",
                "",
                "---", 
                ""
            ])
            return section
        
        # Add endpoint details
        for endpoint in file_result.endpoints:
            section.extend(self._generate_endpoint_section(endpoint))
        
        section.extend(["---", ""])
        return section
    
    def _generate_endpoint_section(self, endpoint: EndpointAnalysis) -> List[str]:
        """Generate report section for a single endpoint."""
        section = [
            f"### {endpoint.method} {endpoint.path or 'N/A'} - {endpoint.function_name}",
            f"**Line:** {endpoint.line_number}",
            ""
        ]
        
        # Add return statements
        if endpoint.return_statements:
            section.append("**Return statements:**")
            for ret_stmt in endpoint.return_statements:
                section.append(f"- Line {ret_stmt.line_number}: `{ret_stmt.content}`")
            section.append("")
        
        # Add suggested schema
        schema = suggest_response_schema(endpoint)
        section.extend([
            "**Suggested schema:**",
            format_analysis_summary(schema),
            "",
            "**Generated code:**",
            "```python"
        ])
        
        schema_code = generate_schema_code(schema)
        section.append(schema_code)
        section.extend(["```", ""])
        
        return section
    
    def save_report(self, output_path: str = "response_schemas_analysis.md") -> None:
        """Save analysis report to file."""
        report = self.generate_report()
        
        with open(output_path, "w", encoding=ANALYSIS_CONFIG.ENCODING) as f:
            f.write(report)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get analysis statistics."""
        if not self.analysis_results:
            return {}
        
        stats = {
            'total_files': len(self.analysis_results),
            'successful_files': sum(1 for r in self.analysis_results.values() if r.analysis_success),
            'total_endpoints': sum(r.endpoint_count for r in self.analysis_results.values()),
            'files_with_endpoints': sum(1 for r in self.analysis_results.values() if r.endpoint_count > 0)
        }
        
        # Method distribution
        method_counts = {}
        for file_result in self.analysis_results.values():
            for endpoint in file_result.endpoints:
                method = endpoint.method
                method_counts[method] = method_counts.get(method, 0) + 1
        
        stats.update(method_counts)
        return stats