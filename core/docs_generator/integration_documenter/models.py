"""
Models for integration documentation.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class DatabaseTable:
    """Information about a database table."""
    name: str
    description: str
    columns: List[str]
    relationships: List[str]
    used_by_modules: List[str]


@dataclass
class ExternalService:
    """Information about an external service integration."""
    name: str
    type: str  # elasticsearch, redis, postgresql
    description: str
    configuration: Dict[str, Any]
    connection_details: Dict[str, str]
    usage_patterns: List[str]
    dependencies: List[str]


@dataclass
class IntegrationDocumentation:
    """Complete integration documentation."""
    external_services: List[ExternalService]
    database_tables: List[DatabaseTable]
    connection_setup: Dict[str, str]
    environment_variables: List[str]