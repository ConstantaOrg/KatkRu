"""
Main documentation generator class.
"""

import inspect
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI
from fastapi.routing import APIRoute

from .models import EndpointInfo, DependencyChain, ModuleDocumentation, Example
from .analyzer import EndpointAnalyzer
from .documenter import ModuleDocumenter
from .example_generator import ExampleGenerator
from .integration_documenter import IntegrationDocumenter
from .endpoint_notices import get_notices_config, format_notice_for_markdown


class DocumentationGenerator:
    """Main class for generating API documentation."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.analyzer = EndpointAnalyzer()
        self.documenter = ModuleDocumenter()
        self.example_generator = ExampleGenerator()
        self.integration_documenter = IntegrationDocumenter()
        self.endpoints: List[EndpointInfo] = []
        self.modules: Dict[str, ModuleDocumentation] = {}
        self.logger = logging.getLogger(__name__)
    
    def analyze_endpoints(self) -> List[EndpointInfo]:
        """Analyze all endpoints in the FastAPI application."""
        try:
            endpoints = []
            
            # Get all routes from the FastAPI application
            for route in self.app.routes:
                if isinstance(route, APIRoute):
                    # Skip excluded endpoints
                    if self.should_exclude_endpoint(route.path):
                        continue
                    
                    try:
                        # Analyze the endpoint
                        endpoint_info = self.analyzer.analyze_endpoint(route)
                        endpoints.append(endpoint_info)
                        self.logger.debug(f"Analyzed endpoint: {endpoint_info.method} {endpoint_info.path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to analyze endpoint {route.path}: {str(e)}")
                        continue
            
            self.endpoints = endpoints
            self.logger.info(f"Successfully analyzed {len(endpoints)} endpoints")
            return endpoints
            
        except Exception as e:
            self.logger.error(f"Failed to analyze endpoints: {str(e)}")
            raise
    
    def trace_dependencies(self, endpoint: EndpointInfo) -> DependencyChain:
        """Trace dependencies for a specific endpoint."""
        try:
            return self.analyzer.trace_dependency_chain(endpoint)
        except Exception as e:
            self.logger.warning(f"Failed to trace dependencies for {endpoint.path}: {str(e)}")
            # Return empty dependency chain on error
            return DependencyChain(
                endpoint=f"{endpoint.method} {endpoint.path}",
                direct_dependencies=[],
                database_queries=[],
                external_services=[],
                middleware=[],
                schemas=[]
            )
    
    def generate_module_docs(self, module: str) -> ModuleDocumentation:
        """Generate documentation for a specific module."""
        try:
            # Filter endpoints for this module
            module_endpoints = [ep for ep in self.endpoints if self.documenter.categorize_endpoint(ep) == module]
            
            # Import constants
            from core.utils.anything import ModuleNames
            
            # Module documentation methods mapping
            module_methods = {
                ModuleNames.specialties: self.documenter.document_specialties_module,
                ModuleNames.groups: self.documenter.document_groups_module,
                ModuleNames.teachers: self.documenter.document_teachers_module,
                ModuleNames.disciplines: self.documenter.document_disciplines_module,
                ModuleNames.timetable: self.documenter.document_timetable_module,
                ModuleNames.users: self.documenter.document_users_module,
                ModuleNames.n8n_ui: self.documenter.document_n8n_ui_module,
                ModuleNames.elastic_search: self.documenter.document_search_module,
                ModuleNames.ttable_versions: self.documenter.document_ttable_versions_module,
            }
            
            # Get the appropriate documenter method
            documenter_method = module_methods.get(module)
            if documenter_method:
                return documenter_method(self.endpoints)
            else:
                # Generic module documentation
                return self.documenter.create_module_documentation(module, self.endpoints, self.endpoints)
                
        except Exception as e:
            self.logger.error(f"Failed to generate documentation for module {module}: {str(e)}")
            raise
    
    def create_examples(self, endpoint: EndpointInfo) -> List[Example]:
        """Create usage examples for an endpoint."""
        try:
            examples = self.example_generator.generate_examples(endpoint)
            
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
            self.logger.warning(f"Failed to create examples for {endpoint.path}: {str(e)}")
            return []
    
    def generate_documentation(self) -> Dict[str, Any]:
        """Generate complete documentation for the API."""
        try:
            self.logger.info("Starting documentation generation...")
            
            # Step 1: Analyze all endpoints
            if not self.endpoints:
                self.analyze_endpoints()
            
            # Step 2: Group endpoints by modules
            grouped_endpoints = self.documenter.group_endpoints_by_modules(self.endpoints)
            
            # Step 3: Generate module documentation
            modules_docs = {}
            for module_name, module_endpoints in grouped_endpoints.items():
                try:
                    module_doc = self.generate_module_docs(module_name)
                    
                    # Add examples to module documentation
                    for endpoint in module_doc.endpoints:
                        examples = self.create_examples(endpoint)
                        module_doc.examples.extend(examples)
                    
                    modules_docs[module_name] = module_doc
                    self.logger.debug(f"Generated documentation for module: {module_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to generate documentation for module {module_name}: {str(e)}")
                    # Continue with other modules
                    continue
            
            # Step 4: Generate dependency chains for all endpoints
            dependency_chains = {}
            for endpoint in self.endpoints:
                try:
                    chain = self.trace_dependencies(endpoint)
                    dependency_chains[f"{endpoint.method} {endpoint.path}"] = chain
                except Exception as e:
                    self.logger.warning(f"Failed to trace dependencies for {endpoint.path}: {str(e)}")
                    continue
            
            # Step 5: Generate integration documentation
            integration_doc = self.integration_documenter.generate_integration_documentation()
            
            # Step 6: Compile complete documentation
            documentation = {
                'overview': {
                    'title': 'API Documentation - Система управления расписанием',
                    'description': 'Техническая документация для API системы управления расписанием учебного заведения',
                    'total_endpoints': len(self.endpoints),
                    'modules_count': len(modules_docs),
                    'generated_at': self._get_current_timestamp()
                },
                'modules': modules_docs,
                'integration': {
                    'external_services': [
                        {
                            'name': service.name,
                            'type': service.type,
                            'description': service.description,
                            'configuration': service.configuration,
                            'connection_details': service.connection_details,
                            'usage_patterns': service.usage_patterns,
                            'dependencies': service.dependencies
                        } for service in integration_doc.external_services
                    ],
                    'database_tables': [
                        {
                            'name': table.name,
                            'description': table.description,
                            'columns': table.columns,
                            'relationships': table.relationships,
                            'used_by_modules': table.used_by_modules
                        } for table in integration_doc.database_tables
                    ],
                    'connection_setup': integration_doc.connection_setup,
                    'environment_variables': integration_doc.environment_variables
                },
                'endpoints': {
                    endpoint.path: {
                        'method': endpoint.method,
                        'function_name': endpoint.function_name,
                        'module': endpoint.module,
                        'description': endpoint.description,
                        'parameters': [
                            {
                                'name': p.name,
                                'type': p.type,
                                'required': p.required,
                                'description': p.description,
                                'location': p.location
                            } for p in endpoint.parameters
                        ],
                        'auth_required': endpoint.auth_required,
                        'roles_required': endpoint.roles_required,
                        'dependencies': [
                            {
                                'name': d.name,
                                'type': d.type,
                                'module': d.module,
                                'description': d.description
                            } for d in endpoint.dependencies
                        ]
                    } for endpoint in self.endpoints
                },
                'dependency_chains': {
                    key: {
                        'endpoint': chain.endpoint,
                        'direct_dependencies': chain.direct_dependencies,
                        'database_queries': chain.database_queries,
                        'external_services': chain.external_services,
                        'middleware': chain.middleware,
                        'schemas': chain.schemas
                    } for key, chain in dependency_chains.items()
                },
                'statistics': {
                    'endpoints_by_method': self._get_endpoints_by_method(),
                    'endpoints_by_module': self._get_endpoints_by_module(),
                    'auth_required_count': len([ep for ep in self.endpoints if ep.auth_required]),
                    'public_endpoints_count': len([ep for ep in self.endpoints if not ep.auth_required])
                }
            }
            
            self.modules = modules_docs
            self.logger.info(f"Documentation generation completed successfully. Generated docs for {len(modules_docs)} modules and {len(self.endpoints)} endpoints.")
            
            return documentation
            
        except Exception as e:
            self.logger.error(f"Failed to generate documentation: {str(e)}")
            raise
    
    def should_exclude_endpoint(self, endpoint_path: str, exclude_patterns: Optional[List[str]] = None) -> bool:
        """Check if an endpoint should be excluded from documentation."""
        # Default exclusion patterns
        default_patterns = [
            'one_time_scripts',
            '/docs',
            '/redoc',
            '/openapi.json'
        ]
        
        # Use provided patterns or defaults
        exclusion_patterns = exclude_patterns or default_patterns
        
        return any(pattern in endpoint_path for pattern in exclusion_patterns)
    
    def format_markdown(self, documentation: Dict[str, Any]) -> str:
        """Format documentation as Markdown."""
        try:
            markdown_content = []
            
            # Title and overview
            overview = documentation.get('overview', {})
            title = overview.get('title', 'API Documentation')
            description = overview.get('description', 'API documentation for the system')
            
            markdown_content.append(f"# {title}\n")
            markdown_content.append(f"{description}\n")
            
            # Statistics
            stats = documentation.get('statistics', {})
            if stats:
                markdown_content.append("## Overview Statistics\n")
                markdown_content.append(f"- **Total Endpoints**: {overview.get('total_endpoints', 0)}")
                markdown_content.append(f"- **Modules**: {overview.get('modules_count', 0)}")
                markdown_content.append(f"- **Authenticated Endpoints**: {stats.get('auth_required_count', 0)}")
                markdown_content.append(f"- **Public Endpoints**: {stats.get('public_endpoints_count', 0)}")
                markdown_content.append(f"- **Generated**: {overview.get('generated_at', 'Unknown')}\n")
            
            # Table of Contents
            modules = documentation.get('modules', {})
            if modules:
                markdown_content.append("## Table of Contents\n")
                for module_name in sorted(modules.keys()):
                    module_title = module_name.replace('_', ' ').title()
                    markdown_content.append(f"- [{module_title}](#{module_name.replace('_', '-')})")
                markdown_content.append("")
            
            # Modules documentation
            for module_name, module_doc in modules.items():
                markdown_content.extend(self._format_module_markdown(module_name, module_doc))
            
            # Integration documentation
            integration = documentation.get('integration', {})
            if integration:
                markdown_content.append("## Интеграции и База Данных\n")
                
                # External services
                external_services = integration.get('external_services', [])
                if external_services:
                    markdown_content.append("### Внешние Сервисы\n")
                    for service in external_services:
                        markdown_content.append(f"#### {service['name']}\n")
                        markdown_content.append(f"**Тип:** {service['type']}")
                        markdown_content.append(f"**Описание:** {service['description']}\n")
                
                # Database tables summary
                database_tables = integration.get('database_tables', [])
                if database_tables:
                    markdown_content.append("### База Данных\n")
                    markdown_content.append(f"Система использует {len(database_tables)} основных таблиц:")
                    for table in database_tables[:5]:  # Show first 5 tables
                        markdown_content.append(f"- **{table['name']}**: {table['description']}")
                    if len(database_tables) > 5:
                        markdown_content.append(f"- и еще {len(database_tables) - 5} таблиц")
                    markdown_content.append("")
                
                markdown_content.append("*Подробная документация по интеграциям доступна в отдельном разделе.*\n")
            
            # Endpoints by method
            endpoints_by_method = stats.get('endpoints_by_method', {})
            if endpoints_by_method:
                markdown_content.append("## Endpoints by HTTP Method\n")
                markdown_content.append("| Method | Count |")
                markdown_content.append("|--------|-------|")
                for method, count in sorted(endpoints_by_method.items()):
                    markdown_content.append(f"| {method} | {count} |")
                markdown_content.append("")
            
            # Dependency chains summary
            dependency_chains = documentation.get('dependency_chains', {})
            if dependency_chains:
                markdown_content.append("## Dependency Analysis\n")
                markdown_content.append("This section provides an overview of the dependency relationships between endpoints.\n")
                
                # Count external services
                external_services = set()
                database_queries_count = 0
                
                for chain in dependency_chains.values():
                    external_services.update(chain.get('external_services', []))
                    database_queries_count += len(chain.get('database_queries', []))
                
                if external_services:
                    markdown_content.append("### External Services Used")
                    for service in sorted(external_services):
                        markdown_content.append(f"- {service}")
                    markdown_content.append("")
                
                if database_queries_count > 0:
                    markdown_content.append(f"### Database Integration")
                    markdown_content.append(f"Total SQL queries identified: {database_queries_count}\n")
            
            return "\n".join(markdown_content)
            
        except Exception as e:
            self.logger.error(f"Failed to format documentation as Markdown: {str(e)}")
            return f"# Documentation Generation Error\n\nFailed to format documentation: {str(e)}"
    
    def _format_module_markdown(self, module_name: str, module_doc) -> List[str]:
        """Format a single module's documentation as Markdown."""
        content = []
        
        # Module header
        module_title = module_name.replace('_', ' ').title()
        content.append(f"## {module_title} {{{module_name.replace('_', '-')}}}\n")
        
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
            content.append("### Endpoints\n")
            content.append("| Method | Path | Function | Auth Required | Description |")
            content.append("|--------|------|----------|---------------|-------------|")
            
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
            content.append("### Database Tables")
            for table in sorted(tables):
                content.append(f"- `{table}`")
            content.append("")
        
        # Schemas
        if hasattr(module_doc, 'schemas'):
            schemas = module_doc.schemas
        else:
            schemas = getattr(module_doc, 'schemas', [])
        
        if schemas:
            content.append("### Data Schemas")
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
            content.append("### Usage Examples\n")
            for i, example in enumerate(examples[:3]):  # Limit to first 3 examples
                content.extend(self._format_example_markdown(example, i + 1))
        
        content.append("---\n")
        return content
    
    def _format_example_markdown(self, example, example_num: int) -> List[str]:
        """Format a single example as Markdown."""
        content = []
        
        title = example.title if hasattr(example, 'title') else f"Example {example_num}"
        description = example.description if hasattr(example, 'description') else ""
        
        content.append(f"#### {title}")
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
                import json
                try:
                    formatted_response = json.dumps(response['body'], indent=2, ensure_ascii=False)
                    content.append(formatted_response)
                except (TypeError, ValueError):
                    content.append(str(response['body']))
                content.append("```\n")
        
        return content
    
    def generate_markdown_file(self, documentation: Dict[str, Any], output_path: str = "api_documentation.md") -> str:
        """Generate a complete Markdown file from documentation."""
        try:
            markdown_content = self.format_markdown(documentation)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Markdown documentation written to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to write Markdown file: {str(e)}")
            raise
    
    def generate_module_markdown_files(self, documentation: Dict[str, Any], output_dir: str = "docs") -> List[str]:
        """Generate separate Markdown files for each module."""
        import os
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            generated_files = []
            modules = documentation.get('modules', {})
            
            # Generate overview file
            overview_content = []
            overview = documentation.get('overview', {})
            overview_content.append(f"# {overview.get('title', 'API Documentation')}\n")
            overview_content.append(f"{overview.get('description', '')}\n")
            
            # Add statistics
            stats = documentation.get('statistics', {})
            if stats:
                overview_content.append("## Statistics\n")
                overview_content.append(f"- Total Endpoints: {overview.get('total_endpoints', 0)}")
                overview_content.append(f"- Modules: {overview.get('modules_count', 0)}")
                overview_content.append(f"- Authenticated Endpoints: {stats.get('auth_required_count', 0)}")
                overview_content.append(f"- Public Endpoints: {stats.get('public_endpoints_count', 0)}\n")
            
            # Add module links
            if modules:
                overview_content.append("## Modules\n")
                for module_name in sorted(modules.keys()):
                    module_title = module_name.replace('_', ' ').title()
                    # Update links to point to docs/module_name.md
                    overview_content.append(f"- [{module_title}](docs/{module_name}.md)")
                overview_content.append("")
            
            # Save README.md in project root instead of docs folder
            overview_file = "README.md"
            with open(overview_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(overview_content))
            generated_files.append(overview_file)
            
            # Generate individual module files in docs directory
            for module_name, module_doc in modules.items():
                module_content = self._format_module_markdown(module_name, module_doc)
                
                module_file = os.path.join(output_dir, f"{module_name}.md")
                with open(module_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(module_content))
                generated_files.append(module_file)
            
            self.logger.info(f"Generated {len(generated_files)} Markdown files - README.md in project root, modules in {output_dir}")
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Failed to generate module Markdown files: {str(e)}")
            raise
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_endpoints_by_method(self) -> Dict[str, int]:
        """Get count of endpoints by HTTP method."""
        method_counts = {}
        for endpoint in self.endpoints:
            method = endpoint.method
            method_counts[method] = method_counts.get(method, 0) + 1
        return method_counts
    
    def _get_endpoints_by_module(self) -> Dict[str, int]:
        """Get count of endpoints by module."""
        module_counts = {}
        for endpoint in self.endpoints:
            module = endpoint.module
            module_counts[module] = module_counts.get(module, 0) + 1
        return module_counts
    
    def generate_integration_documentation(self) -> str:
        """Generate integration documentation as Markdown."""
        try:
            integration_doc = self.integration_documenter.generate_integration_documentation()
            return self.integration_documenter.format_integration_markdown(integration_doc)
        except Exception as e:
            self.logger.error(f"Failed to generate integration documentation: {str(e)}")
            return f"# Integration Documentation Error\n\nFailed to generate integration documentation: {str(e)}"
    
    def get_documentation_summary(self) -> Dict[str, Any]:
        """Get a summary of the generated documentation."""
        if not self.endpoints:
            return {'error': 'No documentation generated yet'}
        
        return {
            'total_endpoints': len(self.endpoints),
            'modules': list(self.modules.keys()) if self.modules else [],
            'endpoints_by_method': self._get_endpoints_by_method(),
            'endpoints_by_module': self._get_endpoints_by_module(),
            'auth_required_endpoints': len([ep for ep in self.endpoints if ep.auth_required]),
            'public_endpoints': len([ep for ep in self.endpoints if not ep.auth_required])
        }
    
    def validate_documentation(self) -> Dict[str, Any]:
        """Validate the generated documentation for completeness."""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check if endpoints were analyzed
            if not self.endpoints:
                validation_results['errors'].append('No endpoints analyzed')
                validation_results['valid'] = False
            
            # Check for endpoints without descriptions
            endpoints_without_desc = [ep for ep in self.endpoints if not ep.description.strip()]
            if endpoints_without_desc:
                validation_results['warnings'].append(
                    f'{len(endpoints_without_desc)} endpoints without descriptions'
                )
            
            # Check for endpoints without dependencies
            endpoints_without_deps = [ep for ep in self.endpoints if not ep.dependencies]
            if endpoints_without_deps:
                validation_results['warnings'].append(
                    f'{len(endpoints_without_deps)} endpoints without traced dependencies'
                )
            
            # Check module coverage
            if not self.modules:
                validation_results['warnings'].append('No module documentation generated')
            
            return validation_results
            
        except Exception as e:
            validation_results['errors'].append(f'Validation failed: {str(e)}')
            validation_results['valid'] = False
            return validation_results