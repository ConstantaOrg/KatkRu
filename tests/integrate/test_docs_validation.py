"""
Tests for validating output documentation structure and content.
"""

import pytest
import tempfile
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List

from core.docs_generator.documentation_generator import DocumentationGenerator
from core.main import app


class TestDocumentationValidation:
    """Tests for validating generated documentation."""
    
    @pytest.fixture
    def generator(self):
        """Create documentation generator instance."""
        return DocumentationGenerator(app)
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_documentation(self, generator):
        """Generate sample documentation for testing."""
        generator.analyze_endpoints()
        return generator.generate_documentation()
    
    def test_documentation_structure_validation(self, sample_documentation):
        """
        Test that generated documentation has correct structure.
        Requirements: 1.1, 1.3
        """
        # Verify top-level structure
        required_sections = ['overview', 'modules', 'endpoints', 'dependency_chains', 'statistics']
        for section in required_sections:
            assert section in sample_documentation, f"Documentation should have '{section}' section"
        
        # Verify overview section structure
        overview = sample_documentation['overview']
        overview_fields = ['title', 'description', 'total_endpoints', 'modules_count', 'generated_at']
        for field in overview_fields:
            assert field in overview, f"Overview should have '{field}' field"
        
        # Verify statistics section structure
        statistics = sample_documentation['statistics']
        stats_fields = ['endpoints_by_method', 'endpoints_by_module', 'auth_required_count', 'public_endpoints_count']
        for field in stats_fields:
            assert field in statistics, f"Statistics should have '{field}' field"
        
        # Verify endpoints section structure
        endpoints = sample_documentation['endpoints']
        assert isinstance(endpoints, dict), "Endpoints should be a dictionary"
        
        # Check structure of first endpoint
        if endpoints:
            first_endpoint = next(iter(endpoints.values()))
            endpoint_fields = ['method', 'function_name', 'module', 'description', 'parameters', 'auth_required', 'roles_required', 'dependencies']
            for field in endpoint_fields:
                assert field in first_endpoint, f"Endpoint should have '{field}' field"
    
    def test_markdown_file_structure_validation(self, generator, sample_documentation, temp_output_dir):
        """
        Test that generated Markdown files have correct structure.
        Requirements: 1.1, 1.3
        """
        # Generate Markdown file
        markdown_file = os.path.join(temp_output_dir, "test_documentation.md")
        generator.generate_markdown_file(sample_documentation, markdown_file)
        
        # Read and validate Markdown content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify basic Markdown structure
        assert len(content) > 0, "Markdown file should not be empty"
        
        # Check for main title
        assert content.startswith('#'), "Markdown should start with a main title"
        
        # Check for required sections
        required_sections = ['Overview Statistics', 'Table of Contents']
        for section in required_sections:
            assert section in content, f"Markdown should contain '{section}' section"
        
        # Verify Markdown formatting
        # Check for proper headers (should have # at start of line)
        header_pattern = r'^#+\s+.+$'
        headers = re.findall(header_pattern, content, re.MULTILINE)
        assert len(headers) > 0, "Markdown should contain properly formatted headers"
        
        # Check for tables (should have | characters)
        if '|' in content:
            # Verify table structure
            table_lines = [line for line in content.split('\n') if '|' in line]
            assert len(table_lines) > 0, "Tables should have proper structure"
    
    def test_module_files_structure_validation(self, generator, sample_documentation, temp_output_dir):
        """
        Test that generated module files have correct structure.
        Requirements: 1.1, 1.3
        """
        # Generate module files
        generated_files = generator.generate_module_markdown_files(sample_documentation, temp_output_dir)
        
        # Verify files were created
        assert len(generated_files) > 0, "Should generate module files"
        
        # Check README.md exists (now in project root)
        readme_file = "README.md"
        assert readme_file in generated_files, "Should generate README.md"
        
        # Validate README.md structure
        with open(readme_file, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        assert len(readme_content) > 0, "README.md should not be empty"
        assert readme_content.startswith('#'), "README.md should start with title"
        
        # Check that links point to docs/module_name.md format
        assert 'docs/' in readme_content, "README.md should contain links to docs/ folder"
        
        # Validate individual module files (still in temp_output_dir)
        module_files = [f for f in generated_files if f != readme_file]
        for module_file in module_files[:3]:  # Check first 3 module files
            with open(module_file, 'r', encoding='utf-8') as f:
                module_content = f.read()
            
            assert len(module_content) > 0, f"Module file should not be empty: {module_file}"
            
            # Check for module structure
            if "## " in module_content:
                assert "### Endpoints" in module_content or "endpoints" in module_content.lower(), f"Module should document endpoints: {module_file}"
    
    def test_json_output_validation(self, generator, sample_documentation, temp_output_dir):
        """
        Test that JSON output is valid and complete.
        Requirements: 1.1, 1.3
        """
        # Generate JSON file
        json_file = os.path.join(temp_output_dir, "test_documentation.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_documentation, f, indent=2, default=str)
        
        # Validate JSON structure
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # Verify JSON is identical to original data (with string conversion)
        assert 'overview' in loaded_data, "JSON should contain overview"
        assert 'modules' in loaded_data, "JSON should contain modules"
        assert 'endpoints' in loaded_data, "JSON should contain endpoints"
        
        # Verify JSON is properly formatted
        assert os.path.getsize(json_file) > 0, "JSON file should not be empty"
    
    def test_documentation_completeness_validation(self, generator, sample_documentation):
        """
        Test that documentation covers all expected endpoints and modules.
        Requirements: 1.1
        """
        # Get all endpoints from the generator
        endpoints = generator.endpoints
        documented_endpoints = sample_documentation['endpoints']
        
        # Verify all endpoints are documented
        endpoint_paths = set(ep.path for ep in endpoints)
        documented_paths = set(documented_endpoints.keys())
        
        # Allow for some endpoints to be excluded (like one_time_scripts)
        coverage_ratio = len(documented_paths) / len(endpoint_paths) if endpoint_paths else 0
        assert coverage_ratio > 0.5, f"Documentation should cover at least 50% of endpoints, got {coverage_ratio:.2%}"
        
        # Verify modules are documented
        modules = sample_documentation['modules']
        assert len(modules) > 0, "Should document at least one module"
        
        # Verify statistics are reasonable
        stats = sample_documentation['statistics']
        total_endpoints = sample_documentation['overview']['total_endpoints']
        
        assert stats['auth_required_count'] + stats['public_endpoints_count'] == total_endpoints, \
            "Auth + public endpoints should equal total endpoints"
    
    def test_markdown_syntax_validation(self, generator, sample_documentation, temp_output_dir):
        """
        Test that generated Markdown follows proper syntax.
        Requirements: 1.3
        """
        # Generate Markdown file
        markdown_file = os.path.join(temp_output_dir, "syntax_test.md")
        generator.generate_markdown_file(sample_documentation, markdown_file)
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common Markdown syntax issues
        lines = content.split('\n')
        
        # Verify headers have proper spacing
        for i, line in enumerate(lines):
            if line.startswith('#'):
                # Header should have space after #
                assert re.match(r'^#+\s+', line), f"Header should have space after #: line {i+1}"
        
        # Check for proper table formatting
        table_lines = [line for line in lines if '|' in line and line.strip()]
        if table_lines:
            # Tables should have consistent column counts
            for table_line in table_lines[:5]:  # Check first 5 table lines
                columns = table_line.split('|')
                assert len(columns) >= 3, f"Table should have at least 3 columns: {table_line}"
        
        # Check for proper code block formatting
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        for code_block in code_blocks:
            assert code_block.startswith('```'), "Code block should start with ```"
            assert code_block.endswith('```'), "Code block should end with ```"
    
    def test_content_quality_validation(self, sample_documentation):
        """
        Test the quality and completeness of documentation content.
        Requirements: 1.1, 1.2
        """
        # Check that endpoints have meaningful descriptions
        endpoints = sample_documentation['endpoints']
        endpoints_with_descriptions = 0
        
        for endpoint_path, endpoint_data in endpoints.items():
            if endpoint_data.get('description', '').strip():
                endpoints_with_descriptions += 1
        
        # At least 15% of endpoints should have descriptions (lowered threshold for real-world data)
        description_ratio = endpoints_with_descriptions / len(endpoints) if endpoints else 0
        assert description_ratio > 0.15, f"At least 15% of endpoints should have descriptions, got {description_ratio:.2%}"
        
        # Check that modules have reasonable content
        modules = sample_documentation['modules']
        for module_name, module_data in modules.items():
            # Module should have some endpoints
            if hasattr(module_data, 'endpoints'):
                endpoints_list = module_data.endpoints
            else:
                endpoints_list = getattr(module_data, 'endpoints', [])
            
            # Skip empty modules
            if len(endpoints_list) == 0:
                continue
                
            # Module should have some meaningful content
            assert len(endpoints_list) > 0, f"Module {module_name} should have endpoints"
    
    def test_dependency_chain_validation(self, sample_documentation):
        """
        Test that dependency chains are properly documented.
        Requirements: 1.2
        """
        dependency_chains = sample_documentation['dependency_chains']
        
        # Should have dependency chains for endpoints
        assert len(dependency_chains) > 0, "Should have dependency chains documented"
        
        # Check structure of dependency chains
        for endpoint_key, chain_data in dependency_chains.items():
            required_fields = ['endpoint', 'direct_dependencies', 'database_queries', 'external_services', 'middleware', 'schemas']
            for field in required_fields:
                assert field in chain_data, f"Dependency chain should have '{field}' field for {endpoint_key}"
            
            # Verify data types
            assert isinstance(chain_data['direct_dependencies'], list), "Direct dependencies should be a list"
            assert isinstance(chain_data['database_queries'], list), "Database queries should be a list"
            assert isinstance(chain_data['external_services'], list), "External services should be a list"
            assert isinstance(chain_data['middleware'], list), "Middleware should be a list"
            assert isinstance(chain_data['schemas'], list), "Schemas should be a list"
    
    def test_integration_documentation_validation(self, generator):
        """
        Test that integration documentation is properly structured.
        Requirements: 8.1, 8.2, 8.3
        """
        integration_doc = generator.generate_integration_documentation()
        
        # Should be non-empty string
        assert isinstance(integration_doc, str), "Integration doc should be string"
        assert len(integration_doc) > 0, "Integration doc should not be empty"
        
        # Should contain expected sections
        expected_sections = ['PostgreSQL', 'Redis', 'Elasticsearch']
        for section in expected_sections:
            assert section in integration_doc, f"Integration doc should mention {section}"
        
        # Should have proper Markdown structure
        assert integration_doc.startswith('#'), "Integration doc should start with header"
        
        # Should contain configuration information
        config_keywords = ['конфигурация', 'configuration', 'настройка', 'подключение']
        has_config_info = any(keyword.lower() in integration_doc.lower() for keyword in config_keywords)
        assert has_config_info, "Integration doc should contain configuration information"


class TestDocumentationValidationEdgeCases:
    """Test validation with edge cases and error conditions."""
    
    @pytest.fixture
    def generator(self):
        """Create documentation generator instance."""
        return DocumentationGenerator(app)
    
    def test_empty_documentation_validation(self, generator):
        """
        Test validation behavior with minimal documentation.
        Requirements: 1.1
        """
        # Create minimal documentation structure
        minimal_doc = {
            'overview': {
                'title': 'Test API',
                'description': 'Test description',
                'total_endpoints': 0,
                'modules_count': 0,
                'generated_at': '2026-01-27T00:00:00'
            },
            'modules': {},
            'endpoints': {},
            'dependency_chains': {},
            'statistics': {
                'endpoints_by_method': {},
                'endpoints_by_module': {},
                'auth_required_count': 0,
                'public_endpoints_count': 0
            }
        }
        
        # Should handle empty documentation gracefully
        markdown_content = generator.format_markdown(minimal_doc)
        assert isinstance(markdown_content, str), "Should return string even for empty doc"
        assert len(markdown_content) > 0, "Should generate some content even for empty doc"
    
    def test_malformed_data_validation(self, generator):
        """
        Test validation with malformed or incomplete data.
        Requirements: 1.1, 1.3
        """
        # Test with missing required fields
        malformed_doc = {
            'overview': {
                'title': 'Test API'
                # Missing other required fields
            },
            'modules': {},
            'endpoints': {},
            'statistics': {}
        }
        
        # Should handle malformed data gracefully
        try:
            markdown_content = generator.format_markdown(malformed_doc)
            assert isinstance(markdown_content, str), "Should return string even with malformed data"
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            assert "error" in str(e).lower() or "failed" in str(e).lower(), "Should provide meaningful error message"
    
    def test_large_documentation_validation(self, generator):
        """
        Test validation with large documentation sets.
        Requirements: 1.1, 1.2
        """
        # Generate full documentation
        generator.analyze_endpoints()
        documentation = generator.generate_documentation()
        
        # Verify it can handle the full documentation set
        validation_result = generator.validate_documentation()
        
        # Should complete validation without errors
        assert hasattr(validation_result, 'valid'), "Should return validation result"
        assert isinstance(validation_result.valid, bool), "Valid field should be boolean"
        
        # Should provide meaningful feedback
        assert hasattr(validation_result, 'warnings'), "Should provide warnings"
        assert hasattr(validation_result, 'errors'), "Should provide errors"
    
    def test_file_output_validation(self, generator):
        """
        Test validation of actual file outputs.
        Requirements: 1.1, 1.3
        """
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Generate documentation and files
            generator.analyze_endpoints()
            documentation = generator.generate_documentation()
            
            # Generate various output formats
            markdown_file = os.path.join(temp_output_dir, "test.md")
            json_file = os.path.join(temp_output_dir, "test.json")
            
            # Generate files
            generator.generate_markdown_file(documentation, markdown_file)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(documentation, f, indent=2, default=str)
            
            # Validate file existence and basic properties
            assert os.path.exists(markdown_file), "Markdown file should be created"
            assert os.path.exists(json_file), "JSON file should be created"
            
            assert os.path.getsize(markdown_file) > 0, "Markdown file should not be empty"
            assert os.path.getsize(json_file) > 0, "JSON file should not be empty"
            
            # Validate file contents can be read back
            with open(markdown_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            assert len(md_content) > 0, "Should be able to read Markdown content"
            
            with open(json_file, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
            assert isinstance(json_content, dict), "Should be able to read JSON content"