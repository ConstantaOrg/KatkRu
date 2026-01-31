"""
Handler functions for response schema analysis operations.
"""

import ast
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import EndpointAnalysis, ReturnStatement, SchemaAnalysis, FileAnalysisResult
from .constants import (
    ROUTER_METHODS, SCHEMA_PATTERNS, SCHEMA_NAME_PATTERNS, ANALYSIS_CONFIG
)


def is_router_decorator(decorator: ast.AST) -> bool:
    """Check if decorator is a FastAPI router method."""
    if isinstance(decorator, ast.Call):
        if isinstance(decorator.func, ast.Attribute):
            # Check router.get, router.post etc.
            if (isinstance(decorator.func.value, ast.Name) and 
                decorator.func.value.id == 'router' and
                decorator.func.attr in ROUTER_METHODS.SUPPORTED_METHODS):
                return True
            # Also check direct method calls
            return decorator.func.attr in ROUTER_METHODS.SUPPORTED_METHODS
    return False


def extract_endpoint_info(func_node: ast.FunctionDef, decorator: ast.Call, 
                         content: str, file_path: str) -> Optional[EndpointAnalysis]:
    """Extract endpoint information from AST nodes."""
    try:
        # Get HTTP method
        method = decorator.func.attr.upper()
        
        # Get path from decorator arguments
        path = None
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            path = decorator.args[0].value
        
        # Get function name
        func_name = func_node.name
        
        # Extract return statements
        return_statements = extract_return_statements(func_node, content)
        
        return EndpointAnalysis(
            method=method,
            path=path,
            function_name=func_name,
            line_number=func_node.lineno,
            return_statements=return_statements,
            file_path=str(file_path)
        )
    
    except Exception:
        return None


def extract_return_statements(func_node: ast.FunctionDef, content: str) -> List[ReturnStatement]:
    """Extract return statements from function AST node."""
    returns = []
    lines = content.split('\n')
    
    for node in ast.walk(func_node):
        if isinstance(node, ast.Return) and node.value:
            if node.lineno <= len(lines):
                raw_line = lines[node.lineno - 1].strip()
                
                # Limit line length for readability
                if len(raw_line) > ANALYSIS_CONFIG.MAX_LINE_LENGTH:
                    raw_line = raw_line[:ANALYSIS_CONFIG.MAX_LINE_LENGTH] + "..."
                
                return_stmt = ReturnStatement(
                    line_number=node.lineno,
                    content=raw_line,
                    raw_line=raw_line
                )
                returns.append(return_stmt)
                
                # Limit number of return statements
                if len(returns) >= ANALYSIS_CONFIG.MAX_RETURN_STATEMENTS:
                    break
    
    return returns


def analyze_file_content(file_path: Path) -> FileAnalysisResult:
    """Analyze a single API file for endpoints."""
    endpoints = []
    
    try:
        with open(file_path, 'r', encoding=ANALYSIS_CONFIG.ENCODING) as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        # Walk through AST nodes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for router decorators
                for decorator in node.decorator_list:
                    if is_router_decorator(decorator):
                        endpoint_info = extract_endpoint_info(
                            node, decorator, content, file_path
                        )
                        if endpoint_info:
                            endpoints.append(endpoint_info)
        
        return FileAnalysisResult(
            file_path=str(file_path),
            endpoints=endpoints,
            analysis_success=True
        )
    
    except Exception as e:
        return FileAnalysisResult(
            file_path=str(file_path),
            endpoints=[],
            analysis_success=False,
            error_message=str(e)
        )


def suggest_response_schema(endpoint: EndpointAnalysis) -> SchemaAnalysis:
    """Suggest response schema for an endpoint."""
    method = endpoint.method
    func_name = endpoint.function_name
    return_statements = endpoint.return_statements
    
    # Analyze return statements for patterns
    return_patterns = []
    suggested_base_classes = []
    
    for return_stmt in return_statements:
        content_lower = return_stmt.content.lower()
        return_patterns.append(return_stmt.content)
        
        # Check for known patterns
        for pattern, schema_class in SCHEMA_PATTERNS.RESPONSE_PATTERNS.items():
            if pattern in content_lower:
                if schema_class not in suggested_base_classes:
                    suggested_base_classes.append(schema_class)
    
    # Add method-specific suggestions
    if method in SCHEMA_PATTERNS.SCHEMA_SUGGESTIONS:
        for suggestion in SCHEMA_PATTERNS.SCHEMA_SUGGESTIONS[method]:
            if suggestion not in suggested_base_classes:
                suggested_base_classes.append(suggestion)
    
    # Generate schema class name
    class_name = generate_schema_name(func_name, method)
    
    return SchemaAnalysis(
        class_name=class_name,
        suggested_base_classes=suggested_base_classes,
        return_patterns=return_patterns,
        method=method,
        function_name=func_name
    )


def generate_schema_name(func_name: str, method: str) -> str:
    """Generate response schema class name."""
    # Remove common prefixes
    name = func_name
    for prefix in SCHEMA_NAME_PATTERNS.FUNCTION_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    
    # Convert to CamelCase
    parts = name.split('_')
    camel_name = ''.join(word.capitalize() for word in parts)
    
    # Add method suffix if needed
    if method in SCHEMA_NAME_PATTERNS.METHOD_SUFFIXES:
        camel_name += SCHEMA_NAME_PATTERNS.METHOD_SUFFIXES[method]
    
    return f"{camel_name}Response"


def generate_schema_code(schema_analysis: SchemaAnalysis) -> str:
    """Generate Python code for response schema."""
    class_name = schema_analysis.class_name
    base_classes = schema_analysis.suggested_base_classes
    return_patterns = schema_analysis.return_patterns
    confidence = schema_analysis.confidence_score
    
    # Create base class inheritance
    inheritance = "BaseModel"
    if base_classes:
        # Use the most specific base class
        inheritance = base_classes[0]
    
    # Generate docstring with analysis info
    docstring = f'"""Response schema for {schema_analysis.function_name} endpoint."""'
    
    # Generate field suggestions based on return patterns
    field_suggestions = generate_field_suggestions(return_patterns)
    
    code = f'''
class {class_name}({inheritance}):
    {docstring}
    
    # Analysis confidence: {confidence:.2f}
    # Suggested base classes: {base_classes}
    # Return patterns analyzed: {len(return_patterns)}
    
{field_suggestions}
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {{
            # Add custom encoders if needed
        }}
'''
    
    return code


def generate_field_suggestions(return_patterns: List[str]) -> str:
    """Generate field suggestions based on return patterns."""
    if not return_patterns:
        return "    # TODO: Define response fields based on actual endpoint behavior"
    
    suggestions = []
    common_fields = {
        'success': 'success: bool',
        'message': 'message: str',
        'data': 'data: Any',
        'id': 'id: int',
        'count': 'count: int',
        'items': 'items: List[Any]',
        'error': 'error: Optional[str] = None'
    }
    
    # Analyze patterns for common fields
    found_fields = []
    for pattern in return_patterns:
        pattern_lower = pattern.lower()
        for field_name, field_def in common_fields.items():
            if field_name in pattern_lower and field_def not in found_fields:
                found_fields.append(field_def)
    
    if found_fields:
        suggestions.extend([f"    {field}" for field in found_fields])
    else:
        suggestions.append("    # TODO: Define response fields based on actual endpoint behavior")
    
    return '\n'.join(suggestions)


def format_analysis_summary(schema_analysis: SchemaAnalysis) -> str:
    """Format schema analysis as readable summary."""
    summary = f"""
**{schema_analysis.class_name}**
- Method: {schema_analysis.method}
- Function: {schema_analysis.function_name}
- Confidence: {schema_analysis.confidence_score:.2f}
- Suggested base classes: {', '.join(schema_analysis.suggested_base_classes) if schema_analysis.suggested_base_classes else 'None'}
- Return patterns: {len(schema_analysis.return_patterns)}
"""
    return summary.strip()