"""
Property-based tests for ModuleDocumenter.
"""

import pytest
from hypothesis import given, strategies as st
from typing import List

from core.docs_generator.documenter import ModuleDocumenter
from core.docs_generator.models import EndpointInfo, Parameter, Dependency, ModuleDocumentation


class TestModuleDocumenter:
    """Test ModuleDocumenter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.documenter = ModuleDocumenter()
    
    @given(st.lists(
        st.builds(
            EndpointInfo,
            path=st.one_of(
                st.just('/specialties'),
                st.just('/groups'),
                st.just('/teachers'),
                st.just('/disciplines'),
                st.just('/timetable'),
                st.just('/users'),
                st.just('/n8n'),
                st.just('/search'),
                st.just('/ttable_versions')
            ),
            method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']),
            function_name=st.text(min_size=1, max_size=50),
            module=st.sampled_from(['specialties', 'groups', 'teachers', 'disciplines', 
                                  'timetable', 'users', 'n8n_ui', 'elastic_search', 'ttable_versions']),
            description=st.text(max_size=200),
            parameters=st.lists(
                st.builds(
                    Parameter,
                    name=st.text(min_size=1, max_size=20),
                    type=st.sampled_from(['str', 'int', 'bool', 'float']),
                    required=st.booleans(),
                    description=st.text(max_size=100),
                    location=st.sampled_from(['query', 'path', 'header', 'body'])
                ),
                max_size=5
            ),
            request_body=st.none(),
            response_model=st.none(),
            auth_required=st.booleans(),
            roles_required=st.lists(st.text(min_size=1, max_size=20), max_size=3),
            dependencies=st.lists(
                st.builds(
                    Dependency,
                    name=st.text(min_size=1, max_size=30),
                    type=st.sampled_from(['function', 'class', 'middleware', 'external_service']),
                    module=st.text(min_size=1, max_size=50),
                    description=st.text(max_size=100)
                ),
                max_size=5
            )
        ),
        min_size=1,
        max_size=20
    ))
    def test_module_organization_consistency(self, endpoints: List[EndpointInfo]):
        """
        Feature: api-documentation, Property 4: Module organization consistency
        
        For any endpoint, it should be correctly categorized under its appropriate 
        functional module with proper module descriptions and inter-module relationships.
        
        **Validates: Requirements 1.3, 4.1, 4.2, 4.3**
        """
        # Group endpoints by modules
        grouped_endpoints = self.documenter.group_endpoints_by_modules(endpoints)
        
        # Property 1: Every endpoint should be categorized into a valid module
        valid_modules = {
            'specialties', 'groups', 'teachers', 'disciplines', 'timetable', 
            'users', 'n8n_ui', 'elastic_search', 'ttable_versions', 'miscellaneous'
        }
        
        for module_name in grouped_endpoints.keys():
            assert module_name in valid_modules, f"Invalid module: {module_name}"
        
        # Property 2: Each endpoint should be categorized consistently
        for endpoint in endpoints:
            # Skip one_time_scripts endpoints as per requirements
            if 'one_time_scripts' in endpoint.function_name:
                continue
                
            categorized_module = self.documenter.categorize_endpoint(endpoint)
            assert categorized_module in valid_modules, f"Invalid categorization: {categorized_module}"
            
            # Verify endpoint appears in the correct group
            if categorized_module in grouped_endpoints:
                assert endpoint in grouped_endpoints[categorized_module], \
                    f"Endpoint {endpoint.path} not found in module {categorized_module}"
        
        # Property 3: Module descriptions should exist for all used modules
        for module_name in grouped_endpoints.keys():
            description = self.documenter.get_module_description(module_name)
            assert description is not None, f"No description for module: {module_name}"
            assert len(description) > 0, f"Empty description for module: {module_name}"
        
        # Property 4: Module relationships should be analyzable
        for module_name in grouped_endpoints.keys():
            relationships = self.documenter.analyze_module_relationships(module_name, endpoints)
            assert isinstance(relationships, list), f"Invalid relationships type for {module_name}"
            
            # All related modules should be valid
            for related_module in relationships:
                assert related_module in valid_modules, \
                    f"Invalid related module {related_module} for {module_name}"
        
        # Property 5: Module documentation should be creatable
        for module_name, module_endpoints in grouped_endpoints.items():
            if module_endpoints:  # Only test if module has endpoints
                module_doc = self.documenter.create_module_documentation(
                    module_name, endpoints, endpoints
                )
                
                assert module_doc.name == module_name
                assert len(module_doc.description) > 0
                assert isinstance(module_doc.endpoints, list)
                assert isinstance(module_doc.schemas, list)
                assert isinstance(module_doc.database_tables, list)
                assert isinstance(module_doc.examples, list)
    
    @given(st.lists(
        st.builds(
            EndpointInfo,
            path=st.one_of(
                st.just('/specialties/list'),
                st.just('/groups/get'),
                st.just('/teachers/add'),
                st.just('/disciplines/update'),
                st.just('/timetable/create'),
                st.just('/users/login'),
                st.just('/n8n/webhook'),
                st.just('/search/query'),
                st.just('/ttable_versions/list'),
                st.just('/one_time_scripts/migrate'),  # Should be excluded
                st.just('/unknown/endpoint')
            ),
            method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']),
            function_name=st.one_of(
                st.text(min_size=1, max_size=50),
                st.just('one_time_migration'),  # Should be excluded
                st.just('schedule_parse_function')  # Should be excluded
            ),
            module=st.sampled_from(['specialties', 'groups', 'teachers', 'disciplines', 
                                  'timetable', 'users', 'n8n_ui', 'elastic_search', 
                                  'ttable_versions', 'one_time_scripts', 'miscellaneous']),
            description=st.text(max_size=200),
            parameters=st.lists(
                st.builds(
                    Parameter,
                    name=st.text(min_size=1, max_size=20),
                    type=st.sampled_from(['str', 'int', 'bool', 'float']),
                    required=st.booleans(),
                    description=st.text(max_size=100),
                    location=st.sampled_from(['query', 'path', 'header', 'body'])
                ),
                max_size=5
            ),
            request_body=st.none(),
            response_model=st.none(),
            auth_required=st.booleans(),
            roles_required=st.lists(st.text(min_size=1, max_size=20), max_size=3),
            dependencies=st.lists(
                st.builds(
                    Dependency,
                    name=st.text(min_size=1, max_size=30),
                    type=st.sampled_from(['function', 'class', 'middleware', 'external_service']),
                    module=st.text(min_size=1, max_size=50),
                    description=st.text(max_size=100)
                ),
                max_size=5
            )
        ),
        min_size=1,
        max_size=20
    ))
    def test_documentation_coverage_completeness(self, endpoints: List[EndpointInfo]):
        """
        Feature: api-documentation, Property 1: Documentation coverage completeness
        
        For any API endpoint in the system (excluding one_time_scripts), 
        there should be corresponding documentation generated.
        
        **Validates: Requirements 1.1, 1.4**
        """
        # Group endpoints by modules
        grouped_endpoints = self.documenter.group_endpoints_by_modules(endpoints)
        
        # Property 1: All non-excluded endpoints should be documented
        documented_endpoints = set()
        for module_endpoints in grouped_endpoints.values():
            for endpoint in module_endpoints:
                documented_endpoints.add((endpoint.path, endpoint.method, endpoint.function_name))
        
        # Check that all valid endpoints are documented
        for endpoint in endpoints:
            # Skip one_time_scripts as per requirements
            if ('one_time_scripts' in endpoint.function_name or 
                'one_time_scripts' in endpoint.module or
                'one_time_scripts' in endpoint.path):
                continue
            
            endpoint_key = (endpoint.path, endpoint.method, endpoint.function_name)
            assert endpoint_key in documented_endpoints, \
                f"Endpoint {endpoint.path} ({endpoint.method}) not documented"
        
        # Property 2: Each documented module should have complete documentation
        for module_name, module_endpoints in grouped_endpoints.items():
            if not module_endpoints:
                continue
                
            # Test module-specific documentation methods
            if module_name == 'specialties':
                doc = self.documenter.document_specialties_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'groups':
                doc = self.documenter.document_groups_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'teachers':
                doc = self.documenter.document_teachers_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'disciplines':
                doc = self.documenter.document_disciplines_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'timetable':
                doc = self.documenter.document_timetable_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'users':
                doc = self.documenter.document_users_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'n8n_ui':
                doc = self.documenter.document_n8n_ui_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'elastic_search':
                doc = self.documenter.document_search_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            elif module_name == 'ttable_versions':
                doc = self.documenter.document_ttable_versions_module(endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
            else:
                # For miscellaneous or other modules, use generic documentation
                doc = self.documenter.create_module_documentation(module_name, endpoints, endpoints)
                self._validate_module_documentation(doc, module_name, module_endpoints)
        
        # Property 3: Documentation should exclude one_time_scripts
        for module_name in grouped_endpoints.keys():
            assert module_name != 'one_time_scripts', \
                "one_time_scripts should be excluded from documentation"
        
        # Property 4: All documented endpoints should have basic information
        for module_endpoints in grouped_endpoints.values():
            for endpoint in module_endpoints:
                assert endpoint.path is not None and len(endpoint.path) > 0
                assert endpoint.method is not None and len(endpoint.method) > 0
                assert endpoint.function_name is not None and len(endpoint.function_name) > 0
                assert isinstance(endpoint.parameters, list)
                assert isinstance(endpoint.dependencies, list)
                assert isinstance(endpoint.roles_required, list)
    
    def _validate_module_documentation(self, doc: ModuleDocumentation, 
                                     expected_module: str, expected_endpoints: List[EndpointInfo]):
        """Helper method to validate module documentation completeness."""
        assert doc.name == expected_module, f"Expected module name {expected_module}, got {doc.name}"
        assert doc.description is not None and len(doc.description) > 0, \
            f"Module {expected_module} has empty description"
        assert isinstance(doc.endpoints, list), f"Module {expected_module} endpoints is not a list"
        assert isinstance(doc.schemas, list), f"Module {expected_module} schemas is not a list"
        assert isinstance(doc.database_tables, list), f"Module {expected_module} database_tables is not a list"
        assert isinstance(doc.examples, list), f"Module {expected_module} examples is not a list"
        
        # Verify that the documented endpoints match the expected ones
        documented_paths = {ep.path for ep in doc.endpoints}
        expected_paths = {ep.path for ep in expected_endpoints 
                         if self.documenter.categorize_endpoint(ep) == expected_module}
        
        # All expected endpoints should be documented
        for expected_path in expected_paths:
            assert expected_path in documented_paths or len(expected_paths) == 0, \
                f"Expected endpoint {expected_path} not found in {expected_module} documentation"
    
    def test_categorize_endpoint_by_path(self):
        """Test endpoint categorization based on path."""
        test_cases = [
            ('/specialties/list', 'specialties'),
            ('/groups/create', 'groups'),
            ('/teachers/update', 'teachers'),
            ('/disciplines/delete', 'disciplines'),
            ('/timetable/get', 'timetable'),
            ('/users/login', 'users'),
            ('/n8n/webhook', 'n8n_ui'),
            ('/search/query', 'elastic_search'),
            ('/ttable_versions/list', 'ttable_versions'),
            ('/unknown/path', 'miscellaneous')
        ]
        
        for path, expected_module in test_cases:
            endpoint = EndpointInfo(
                path=path,
                method='GET',
                function_name='test_func',
                module='',
                description='Test endpoint',
                parameters=[],
                request_body=None,
                response_model=None,
                auth_required=False,
                roles_required=[],
                dependencies=[]
            )
            
            result = self.documenter.categorize_endpoint(endpoint)
            assert result == expected_module, f"Expected {expected_module}, got {result} for path {path}"
    
    def test_one_time_scripts_exclusion(self):
        """Test that one_time_scripts are excluded from documentation."""
        endpoints = [
            EndpointInfo(
                path='/specialties/list',
                method='GET',
                function_name='list_specialties',
                module='specialties',
                description='List specialties',
                parameters=[],
                request_body=None,
                response_model=None,
                auth_required=False,
                roles_required=[],
                dependencies=[]
            ),
            EndpointInfo(
                path='/one_time_scripts/migrate',
                method='POST',
                function_name='one_time_migration',
                module='one_time_scripts',
                description='One time migration',
                parameters=[],
                request_body=None,
                response_model=None,
                auth_required=False,
                roles_required=[],
                dependencies=[]
            )
        ]
        
        grouped = self.documenter.group_endpoints_by_modules(endpoints)
        
        # Should only contain specialties module, not one_time_scripts
        assert 'specialties' in grouped
        assert 'one_time_scripts' not in grouped
        assert len(grouped['specialties']) == 1
        assert grouped['specialties'][0].function_name == 'list_specialties'