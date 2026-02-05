"""
Data models for the documentation generator.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


@dataclass
class Parameter:
    """Represents a parameter in an API endpoint."""
    name: str
    type: str
    required: bool
    description: str
    location: str  # query, path, header, body


@dataclass
class Dependency:
    """Represents a dependency of an endpoint."""
    name: str
    type: str  # function, class, middleware, external_service
    module: str
    description: str


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""
    path: str
    method: str
    function_name: str
    module: str
    description: str
    parameters: List[Parameter]
    request_body: Optional[BaseModel]
    response_model: Optional[BaseModel]
    auth_required: bool
    roles_required: List[str]
    dependencies: List[Dependency]


@dataclass
class DependencyChain:
    """Chain of dependencies for an endpoint."""
    endpoint: str
    direct_dependencies: List[str]
    database_queries: List[str]
    external_services: List[str]
    middleware: List[str]
    schemas: List[str]


@dataclass
class Example:
    """Example usage of an API endpoint."""
    title: str
    description: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    curl_command: str


@dataclass
class ModuleDocumentation:
    """Documentation for a module."""
    name: str
    description: str
    endpoints: List[EndpointInfo]
    schemas: List[BaseModel]
    database_tables: List[str]
    examples: List[Example]