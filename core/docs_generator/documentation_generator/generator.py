"""
Main documentation generator class.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI

from ..models import EndpointInfo, DependencyChain, ModuleDocumentation, Example
from ..endpoint_analyzer import EndpointAnalyzer
from ..module_documenter import ModuleDocumenter
from ..example_generator import ExampleGenerator
from ..integration_documenter import IntegrationDocumenter

from .models import DocumentationOverview, ValidationResult, DocumentationSummary
from .constants import FILE_NAMES
from . import handlers


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
        self.endpoints = handlers.analyze_endpoints(self.app, self.analyzer, self.logger)
        return self.endpoints
    
    def trace_dependencies(self, endpoint: EndpointInfo) -> DependencyChain:
        """Trace dependencies for a specific endpoint."""
        return handlers.trace_dependencies(endpoint, self.analyzer, self.logger)
    
    def generate_module_docs(self, module: str) -> ModuleDocumentation:
        """Generate documentation for a specific module."""
        return handlers.generate_module_docs(module, self.endpoints, self.documenter, self.logger)
    
    def create_examples(self, endpoint: EndpointInfo) -> List[Example]:
        """Create usage examples for an endpoint."""
        return handlers.create_examples(endpoint, self.example_generator, self.logger)
    
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
            
            # Step 6: Create overview
            overview = handlers.create_documentation_overview(self.endpoints, len(modules_docs))
            
            # Step 7: Compile complete documentation
            documentation = {
                'overview': {
                    'title': overview.title,
                    'description': overview.description,
                    'total_endpoints': overview.total_endpoints,
                    'modules_count': overview.modules_count,
                    'generated_at': overview.generated_at
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
                    'endpoints_by_method': handlers.get_endpoints_by_method(self.endpoints),
                    'endpoints_by_module': handlers.get_endpoints_by_module(self.endpoints),
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
        return handlers.should_exclude_endpoint(endpoint_path, exclude_patterns)
    
    def format_markdown(self, documentation: Dict[str, Any]) -> str:
        """Format documentation as Markdown."""
        return handlers.format_markdown_documentation(documentation, self.logger)
    
    def generate_markdown_file(self, documentation: Dict[str, Any], output_path: str = None) -> str:
        """Generate a complete Markdown file from documentation."""
        if output_path is None:
            output_path = FILE_NAMES.API_DOCUMENTATION
        return handlers.generate_markdown_file(documentation, output_path, self.logger)
    
    def generate_module_markdown_files(self, documentation: Dict[str, Any], output_dir: str = None) -> List[str]:
        """Generate separate Markdown files for each module."""
        if output_dir is None:
            output_dir = FILE_NAMES.DOCS_DIR
        return handlers.generate_module_markdown_files(documentation, output_dir, self.logger)
    
    def generate_integration_documentation(self) -> str:
        """Generate integration documentation as Markdown."""
        return handlers.generate_integration_documentation(self.integration_documenter, self.logger)
    
    def get_documentation_summary(self) -> DocumentationSummary:
        """Get a summary of the generated documentation."""
        return handlers.get_documentation_summary(self.endpoints, self.modules)
    
    def validate_documentation(self) -> ValidationResult:
        """Validate the generated documentation for completeness."""
        return handlers.validate_documentation(self.endpoints, self.modules)