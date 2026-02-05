# Response Schema Analyzer

This module analyzes API endpoints and suggests response schemas for FastAPI applications.

## Structure

The module is organized following the docs_generator pattern:

```
response_schema_analyzer/
├── __init__.py          # Module exports
├── analyzer.py          # Main analyzer class
├── constants.py         # Configuration constants
├── handlers.py          # Helper functions
├── models.py           # Data models
└── README.md           # This file
```

## Components

### Constants (`constants.py`)
- `ROUTER_METHODS`: Supported HTTP methods
- `SCHEMA_PATTERNS`: Response pattern detection rules
- `FILE_PATTERNS`: File analysis configuration
- `SCHEMA_NAME_PATTERNS`: Schema naming conventions
- `ANALYSIS_CONFIG`: Analysis parameters

### Models (`models.py`)
- `EndpointAnalysis`: Analysis result for a single endpoint
- `SchemaAnalysis`: Suggested response schema information
- `ReturnStatement`: Parsed return statement data
- `FileAnalysisResult`: File analysis results
- `AnalysisReport`: Complete analysis report

### Handlers (`handlers.py`)
- `is_router_decorator()`: Detect FastAPI router decorators
- `extract_endpoint_info()`: Parse endpoint information from AST
- `extract_return_statements()`: Extract return statements
- `suggest_response_schema()`: Generate schema suggestions
- `generate_schema_code()`: Create Python schema code
- `analyze_file_content()`: Analyze single API file

### Analyzer (`analyzer.py`)
- `ResponseSchemaAnalyzer`: Main analyzer class
- File and directory analysis
- Report generation
- Statistics collection

## Usage

```python
from core.docs_generator.response_schema_analyzer import ResponseSchemaAnalyzer

# Create analyzer
analyzer = ResponseSchemaAnalyzer()

# Analyze all API files
report = analyzer.analyze_all_files()

# Generate report
markdown_report = analyzer.generate_report()

# Save to file
analyzer.save_report("analysis_report.md")

# Get statistics
stats = analyzer.get_statistics()
```

## Features

- **AST-based analysis**: Parses Python code using AST for accurate endpoint detection
- **Pattern recognition**: Identifies common response patterns in return statements
- **Schema suggestions**: Generates Pydantic model suggestions with confidence scores
- **Comprehensive reporting**: Creates detailed markdown reports with code examples
- **Modular design**: Clean separation of concerns following docs_generator patterns

## Configuration

Customize analysis behavior through constants:

```python
from core.docs_generator.response_schema_analyzer.constants import ANALYSIS_CONFIG

# Modify analysis parameters
ANALYSIS_CONFIG.MAX_RETURN_STATEMENTS = 5
ANALYSIS_CONFIG.MAX_LINE_LENGTH = 150
```

## Integration

This module integrates with the broader docs_generator system and follows the same architectural patterns as other analyzer modules.