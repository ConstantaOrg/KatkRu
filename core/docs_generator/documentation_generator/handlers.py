"""
Handler functions for documentation generation operations.
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..models import EndpointInfo, DependencyChain, ModuleDocumentation, Example
from ..endpoint_analyzer import EndpointAnalyzer
from ..module_documenter import ModuleDocumenter
from ..example_generator import ExampleGenerator
from ..integration_documenter import IntegrationDocumenter
from ..endpoint_notices import get_notices_config, format_notice_for_markdown

from .models import DocumentationOverview, ValidationResult, DocumentationSummary
from .constants import (
    EXCLUSION_PATTERNS, DOCUMENTATION_TEMPLATES, MARKDOWN_HEADERS,
    VALIDATION_MESSAGES, FILE_NAMES
)
from .improved_formatter import ImprovedDocumentationFormatter


def analyze_endpoints(app: FastAPI, analyzer: EndpointAnalyzer, logger: logging.Logger) -> List[EndpointInfo]:
    """Analyze all endpoints in the FastAPI application."""
    try:
        endpoints = []
        
        # Get all routes from the FastAPI application
        for route in app.routes:
            if isinstance(route, APIRoute):
                # Skip excluded endpoints
                if should_exclude_endpoint(route.path):
                    continue
                
                try:
                    # Analyze the endpoint
                    endpoint_info = analyzer.analyze_endpoint(route)
                    endpoints.append(endpoint_info)
                    logger.debug(f"Analyzed endpoint: {endpoint_info.method} {endpoint_info.path}")
                except Exception as e:
                    logger.warning(f"Failed to analyze endpoint {route.path}: {str(e)}")
                    continue
        
        logger.info(f"Successfully analyzed {len(endpoints)} endpoints")
        return endpoints
        
    except Exception as e:
        logger.error(f"Failed to analyze endpoints: {str(e)}")
        raise


def should_exclude_endpoint(endpoint_path: str, exclude_patterns: Optional[List[str]] = None) -> bool:
    """Check if an endpoint should be excluded from documentation."""
    # Use provided patterns or defaults
    exclusion_patterns = exclude_patterns or EXCLUSION_PATTERNS.PATTERNS
    
    return any(pattern in endpoint_path for pattern in exclusion_patterns)


def trace_dependencies(endpoint: EndpointInfo, analyzer: EndpointAnalyzer, logger: logging.Logger) -> DependencyChain:
    """Trace dependencies for a specific endpoint."""
    try:
        return analyzer.trace_dependency_chain(endpoint)
    except Exception as e:
        logger.warning(f"Failed to trace dependencies for {endpoint.path}: {str(e)}")
        # Return empty dependency chain on error
        return DependencyChain(
            endpoint=f"{endpoint.method} {endpoint.path}",
            direct_dependencies=[],
            database_queries=[],
            external_services=[],
            middleware=[],
            schemas=[]
        )


def generate_module_docs(module: str, endpoints: List[EndpointInfo], documenter: ModuleDocumenter, logger: logging.Logger) -> ModuleDocumentation:
    """Generate documentation for a specific module."""
    try:
        # Filter endpoints for this module
        module_endpoints = [ep for ep in endpoints if documenter.categorize_endpoint(ep) == module]
        
        # Import constants
        from core.utils.anything import ModuleNames
        
        # Module documentation methods mapping
        module_methods = {
            ModuleNames.specialties: documenter.document_specialties_module,
            ModuleNames.groups: documenter.document_groups_module,
            ModuleNames.teachers: documenter.document_teachers_module,
            ModuleNames.disciplines: documenter.document_disciplines_module,
            ModuleNames.timetable: documenter.document_timetable_module,
            ModuleNames.users: documenter.document_users_module,
            ModuleNames.n8n_ui: documenter.document_n8n_ui_module,
            ModuleNames.elastic_search: documenter.document_search_module,
            ModuleNames.ttable_versions: documenter.document_ttable_versions_module,
        }
        
        # Get the appropriate documenter method
        documenter_method = module_methods.get(module)
        if documenter_method:
            return documenter_method(endpoints)
        else:
            # Generic module documentation
            return documenter.create_module_documentation(module, endpoints, endpoints)
            
    except Exception as e:
        logger.error(f"Failed to generate documentation for module {module}: {str(e)}")
        raise


def create_examples(endpoint: EndpointInfo, example_generator: ExampleGenerator, logger: logging.Logger) -> List[Example]:
    """Create usage examples for an endpoint."""
    try:
        examples = example_generator.generate_examples(endpoint)
        
        # Добавляем notices к первому примеру (если есть)
        if examples:
            notices_config = get_notices_config()
            notices = notices_config.get_notice(endpoint.method, endpoint.path)
            
            if notices:
                # Добавляем notices к описанию первого примера
                first_example = examples[0]
                notices_text = ""
                for notice_type, notice_text in notices.items():
                    formatted_notice = format_notice_for_markdown(notice_type, notice_text)
                    notices_text += formatted_notice
                
                # Добавляем notices к описанию
                if hasattr(first_example, 'description'):
                    first_example.description = first_example.description + notices_text
                else:
                    # Если нет описания, создаем его
                    first_example.description = notices_text.strip()
        
        return examples
    except Exception as e:
        logger.warning(f"Failed to create examples for {endpoint.path}: {str(e)}")
        return []


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def get_endpoints_by_method(endpoints: List[EndpointInfo]) -> Dict[str, int]:
    """Get count of endpoints by HTTP method."""
    method_counts = {}
    for endpoint in endpoints:
        method = endpoint.method
        method_counts[method] = method_counts.get(method, 0) + 1
    return method_counts


def get_endpoints_by_module(endpoints: List[EndpointInfo]) -> Dict[str, int]:
    """Get count of endpoints by module."""
    module_counts = {}
    for endpoint in endpoints:
        module = endpoint.module
        module_counts[module] = module_counts.get(module, 0) + 1
    return module_counts


def create_documentation_overview(endpoints: List[EndpointInfo], modules_count: int) -> DocumentationOverview:
    """Create documentation overview."""
    return DocumentationOverview(
        title=DOCUMENTATION_TEMPLATES.OVERVIEW_TITLE,
        description=DOCUMENTATION_TEMPLATES.OVERVIEW_DESCRIPTION,
        total_endpoints=len(endpoints),
        modules_count=modules_count,
        generated_at=get_current_timestamp()
    )


def format_markdown_documentation(documentation: Dict[str, Any], logger: logging.Logger) -> str:
    """Format documentation as Markdown."""
    try:
        markdown_content = []
        
        # Title and overview
        overview = documentation.get('overview', {})
        title = overview.get('title', 'API Documentation')
        description = overview.get('description', 'API documentation for the system')
        
        markdown_content.append(MARKDOWN_HEADERS.MAIN_TITLE.format(title=title))
        markdown_content.append(f"{description}\n")
        
        # Statistics
        stats = documentation.get('statistics', {})
        if stats:
            markdown_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title="Overview Statistics"))
            markdown_content.append(f"- **Total Endpoints**: {overview.get('total_endpoints', 0)}")
            markdown_content.append(f"- **Modules**: {overview.get('modules_count', 0)}")
            markdown_content.append(f"- **Authenticated Endpoints**: {stats.get('auth_required_count', 0)}")
            markdown_content.append(f"- **Public Endpoints**: {stats.get('public_endpoints_count', 0)}")
            markdown_content.append(f"- **Generated**: {overview.get('generated_at', 'Unknown')}\n")
        
        # Table of Contents
        modules = documentation.get('modules', {})
        if modules:
            markdown_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title="Table of Contents"))
            for module_name in sorted(modules.keys()):
                module_title = module_name.replace('_', ' ').title()
                markdown_content.append(f"- [{module_title}](#{module_name.replace('_', '-')})")
            markdown_content.append("")
        
        # Modules documentation
        for module_name, module_doc in modules.items():
            markdown_content.extend(format_module_markdown(module_name, module_doc))
        
        # Integration documentation
        integration = documentation.get('integration', {})
        if integration:
            markdown_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title="Интеграции и База Данных"))
            
            # External services
            external_services = integration.get('external_services', [])
            if external_services:
                markdown_content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="Внешние Сервисы"))
                for service in external_services:
                    markdown_content.append(MARKDOWN_HEADERS.SUBSUBSECTION_TITLE.format(title=service['name']))
                    markdown_content.append(f"**Тип:** {service['type']}")
                    markdown_content.append(f"**Описание:** {service['description']}\n")
            
            # Database tables summary
            database_tables = integration.get('database_tables', [])
            if database_tables:
                markdown_content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="База Данных"))
                markdown_content.append(f"Система использует {len(database_tables)} основных таблиц:")
                for table in database_tables[:5]:  # Show first 5 tables
                    markdown_content.append(f"- **{table['name']}**: {table['description']}")
                if len(database_tables) > 5:
                    markdown_content.append(f"- и еще {len(database_tables) - 5} таблиц")
                markdown_content.append("")
            
            markdown_content.append(f"{DOCUMENTATION_TEMPLATES.INTEGRATION_DESCRIPTION}\n")
        
        # Endpoints by method
        endpoints_by_method = stats.get('endpoints_by_method', {})
        if endpoints_by_method:
            markdown_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title="Endpoints by HTTP Method"))
            markdown_content.append(MARKDOWN_HEADERS.STATS_TABLE_HEADER)
            markdown_content.append(MARKDOWN_HEADERS.STATS_TABLE_SEPARATOR)
            for method, count in sorted(endpoints_by_method.items()):
                markdown_content.append(f"| {method} | {count} |")
            markdown_content.append("")
        
        # Dependency chains summary
        dependency_chains = documentation.get('dependency_chains', {})
        if dependency_chains:
            markdown_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title=DOCUMENTATION_TEMPLATES.DEPENDENCY_TITLE))
            markdown_content.append(f"{DOCUMENTATION_TEMPLATES.DEPENDENCY_DESCRIPTION}\n")
            
            # Count external services
            external_services = set()
            database_queries_count = 0
            
            for chain in dependency_chains.values():
                external_services.update(chain.get('external_services', []))
                database_queries_count += len(chain.get('database_queries', []))
            
            if external_services:
                markdown_content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="External Services Used"))
                for service in sorted(external_services):
                    markdown_content.append(f"- {service}")
                markdown_content.append("")
            
            if database_queries_count > 0:
                markdown_content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="Database Integration"))
                markdown_content.append(f"Total SQL queries identified: {database_queries_count}\n")
        
        return "\n".join(markdown_content)
        
    except Exception as e:
        logger.error(f"Failed to format documentation as Markdown: {str(e)}")
        return f"# {DOCUMENTATION_TEMPLATES.ERROR_TITLE}\n\nFailed to format documentation: {str(e)}"


def format_module_markdown(module_name: str, module_doc) -> List[str]:
    """Format a single module's documentation as Markdown."""
    content = []
    
    # Module header
    module_title = module_name.replace('_', ' ').title()
    content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title=f"{module_title} {{{module_name.replace('_', '-')}}}"))
    
    # Module description
    if hasattr(module_doc, 'description'):
        description = module_doc.description
    else:
        description = getattr(module_doc, 'description', 'Module description not available')
    
    content.append(f"{description}\n")
    
    # Module endpoints
    if hasattr(module_doc, 'endpoints'):
        endpoints = module_doc.endpoints
    else:
        endpoints = getattr(module_doc, 'endpoints', [])
    
    if endpoints:
        content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="Endpoints"))
        content.append(MARKDOWN_HEADERS.TABLE_HEADER)
        content.append(MARKDOWN_HEADERS.TABLE_SEPARATOR)
        
        for endpoint in endpoints:
            method = endpoint.method if hasattr(endpoint, 'method') else 'Unknown'
            path = endpoint.path if hasattr(endpoint, 'path') else 'Unknown'
            func_name = endpoint.function_name if hasattr(endpoint, 'function_name') else 'Unknown'
            auth_req = "✓" if (hasattr(endpoint, 'auth_required') and endpoint.auth_required) else "✗"
            desc = (endpoint.description if hasattr(endpoint, 'description') else 'No description')[:50]
            if len(desc) == 50:
                desc += "..."
            
            content.append(f"| {method} | `{path}` | {func_name} | {auth_req} | {desc} |")
        
        content.append("")
    
    # Database tables
    if hasattr(module_doc, 'database_tables'):
        tables = module_doc.database_tables
    else:
        tables = getattr(module_doc, 'database_tables', [])
    
    if tables:
        content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="Database Tables"))
        for table in sorted(tables):
            content.append(f"- `{table}`")
        content.append("")
    
    # Schemas
    if hasattr(module_doc, 'schemas'):
        schemas = module_doc.schemas
    else:
        schemas = getattr(module_doc, 'schemas', [])
    
    if schemas:
        content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="Data Schemas"))
        for schema in schemas:
            schema_name = schema.__name__ if hasattr(schema, '__name__') else str(schema)
            content.append(f"- `{schema_name}`")
        content.append("")
    
    # Examples
    if hasattr(module_doc, 'examples'):
        examples = module_doc.examples
    else:
        examples = getattr(module_doc, 'examples', [])
    
    if examples:
        content.append(MARKDOWN_HEADERS.SUBSECTION_TITLE.format(title="Usage Examples"))
        for i, example in enumerate(examples[:3]):  # Limit to first 3 examples
            content.extend(format_example_markdown(example, i + 1))
    
    content.append("---\n")
    return content


def format_example_markdown(example, example_num: int) -> List[str]:
    """Format a single example as Markdown."""
    content = []
    
    title = example.title if hasattr(example, 'title') else f"Example {example_num}"
    description = example.description if hasattr(example, 'description') else ""
    
    content.append(MARKDOWN_HEADERS.SUBSUBSECTION_TITLE.format(title=title))
    if description:
        content.append(f"{description}\n")
    
    # Добавляем notices для эндпоинта (если есть)
    if hasattr(example, 'endpoint') and example.endpoint:
        endpoint = example.endpoint
        notices_config = get_notices_config()
        notices = notices_config.get_notice(endpoint.method, endpoint.path)
        
        if notices:
            for notice_type, notice_text in notices.items():
                formatted_notice = format_notice_for_markdown(notice_type, notice_text)
                content.append(formatted_notice)
    
    # cURL command
    if hasattr(example, 'curl_command') and example.curl_command:
        content.append("**Request:**")
        content.append("```bash")
        content.append(example.curl_command)
        content.append("```\n")
    
    # Response
    if hasattr(example, 'response') and example.response:
        response = example.response
        if isinstance(response, dict) and 'body' in response:
            content.append("**Response:**")
            content.append("```json")
            try:
                formatted_response = json.dumps(response['body'], indent=2, ensure_ascii=False)
                content.append(formatted_response)
            except (TypeError, ValueError):
                content.append(str(response['body']))
            content.append("```\n")
    
    return content


def generate_markdown_file(documentation: Dict[str, Any], output_path: str, logger: logging.Logger) -> str:
    """Generate a complete Markdown file from documentation."""
    try:
        markdown_content = format_markdown_documentation(documentation, logger)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown documentation written to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to write Markdown file: {str(e)}")
        raise


def generate_module_markdown_files(documentation: Dict[str, Any], output_dir: str, logger: logging.Logger) -> List[str]:
    """Generate separate Markdown files for each module."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        modules = documentation.get('modules', {})
        
        # Generate overview file
        overview_content = []
        overview = documentation.get('overview', {})
        overview_content.append(MARKDOWN_HEADERS.MAIN_TITLE.format(title=overview.get('title', 'API Documentation')))
        overview_content.append(f"{overview.get('description', '')}\n")
        
        # Add statistics
        stats = documentation.get('statistics', {})
        if stats:
            overview_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title="Statistics"))
            overview_content.append(f"- Total Endpoints: {overview.get('total_endpoints', 0)}")
            overview_content.append(f"- Modules: {overview.get('modules_count', 0)}")
            overview_content.append(f"- Authenticated Endpoints: {stats.get('auth_required_count', 0)}")
            overview_content.append(f"- Public Endpoints: {stats.get('public_endpoints_count', 0)}\n")
        
        # Add module links
        if modules:
            overview_content.append(MARKDOWN_HEADERS.SECTION_TITLE.format(title="Modules"))
            for module_name in sorted(modules.keys()):
                module_title = module_name.replace('_', ' ').title()
                # Update links to point to docs/module_name.md
                overview_content.append(f"- [{module_title}](docs/{module_name}.md)")
            overview_content.append("")
        
        # Save README.md in project root instead of docs folder
        overview_file = FILE_NAMES.README
        with open(overview_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(overview_content))
        generated_files.append(overview_file)
        
        # Generate individual module files in docs directory
        for module_name, module_doc in modules.items():
            module_content = format_module_markdown(module_name, module_doc)
            
            module_file = os.path.join(output_dir, f"{module_name}.md")
            with open(module_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(module_content))
            generated_files.append(module_file)
        
        logger.info(f"Generated {len(generated_files)} Markdown files - README.md in project root, modules in {output_dir}")
        return generated_files
        
    except Exception as e:
        logger.error(f"Failed to generate module Markdown files: {str(e)}")
        raise


def generate_integration_documentation(integration_documenter: IntegrationDocumenter, logger: logging.Logger) -> str:
    """Generate integration documentation as Markdown."""
    try:
        integration_doc = integration_documenter.generate_integration_documentation()
        return integration_documenter.format_integration_markdown(integration_doc)
    except Exception as e:
        logger.error(f"Failed to generate integration documentation: {str(e)}")
        return f"# Integration Documentation Error\n\nFailed to generate integration documentation: {str(e)}"


def get_documentation_summary(endpoints: List[EndpointInfo], modules: Dict[str, ModuleDocumentation]) -> DocumentationSummary:
    """Get a summary of the generated documentation."""
    if not endpoints:
        raise ValueError('No documentation generated')
    
    return DocumentationSummary(
        total_endpoints=len(endpoints),
        modules=list(modules.keys()) if modules else [],
        endpoints_by_method=get_endpoints_by_method(endpoints),
        endpoints_by_module=get_endpoints_by_module(endpoints),
        auth_required_endpoints=len([ep for ep in endpoints if ep.auth_required]),
        public_endpoints=len([ep for ep in endpoints if not ep.auth_required])
    )


def validate_documentation(endpoints: List[EndpointInfo], modules: Dict[str, ModuleDocumentation]) -> ValidationResult:
    """Validate the generated documentation for completeness."""
    validation_results = ValidationResult(
        valid=True,
        warnings=[],
        errors=[]
    )
    
    try:
        # Check if endpoints were analyzed
        if not endpoints:
            validation_results.errors.append(VALIDATION_MESSAGES.NO_ENDPOINTS)
            validation_results.valid = False
        
        # Check for endpoints without descriptions
        endpoints_without_desc = [ep for ep in endpoints if not ep.description.strip()]
        if endpoints_without_desc:
            validation_results.warnings.append(
                VALIDATION_MESSAGES.ENDPOINTS_WITHOUT_DESC.format(count=len(endpoints_without_desc))
            )
        
        # Check for endpoints without dependencies
        endpoints_without_deps = [ep for ep in endpoints if not ep.dependencies]
        if endpoints_without_deps:
            validation_results.warnings.append(
                VALIDATION_MESSAGES.ENDPOINTS_WITHOUT_DEPS.format(count=len(endpoints_without_deps))
            )
        
        # Check module coverage
        if not modules:
            validation_results.warnings.append(VALIDATION_MESSAGES.NO_MODULES)
        
        return validation_results
        
    except Exception as e:
        validation_results.errors.append(VALIDATION_MESSAGES.VALIDATION_FAILED.format(error=str(e)))
        validation_results.valid = False
        return validation_results