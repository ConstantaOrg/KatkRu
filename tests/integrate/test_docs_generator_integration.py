"""
Integration tests for the documentation generator.
Tests the full process of documentation generation with real FastAPI application.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch

from core.docs_generator.generator import DocumentationGenerator
from core.docs_generator.cli import DocumentationCLI
from core.main import app


class TestDocumentationGeneratorIntegration:
    """Integration tests for the documentation generator."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def generator(self):
        """Create documentation generator instance with real FastAPI app."""
        return DocumentationGenerator(app)
    
    def test_full_documentation_generation_process(self, generator, temp_output_dir):
        """
        Test the complete documentation generation process.
        Requirements: 1.1, 1.2, 1.3
        """
        # Step 1: Analyze endpoints
        endpoints = generator.analyze_endpoints()
        
        # Verify endpoints were found
        assert len(endpoints) > 0, "Should find endpoints in the FastAPI application"
        
        # Verify endpoints have required attributes
        for endpoint in endpoints[:5]:  # Check first 5 endpoints
            assert hasattr(endpoint, 'path'), "Endpoint should have path"
            assert hasattr(endpoint, 'method'), "Endpoint should have method"
            assert hasattr(endpoint, 'function_name'), "Endpoint should have function_name"
            assert hasattr(endpoint, 'module'), "Endpoint should have module"
        
        # Step 2: Generate complete documentation
        documentation = generator.generate_documentation()
        
        # Verify documentation structure
        assert 'overview' in documentation, "Documentation should have overview section"
        assert 'modules' in documentation, "Documentation should have modules section"
        assert 'endpoints' in documentation, "Documentation should have endpoints section"
        assert 'dependency_chains' in documentation, "Documentation should have dependency_chains section"
        assert 'statistics' in documentation, "Documentation should have statistics section"
        
        # Verify overview section
        overview = documentation['overview']
        assert 'title' in overview, "Overview should have title"
        assert 'total_endpoints' in overview, "Overview should have total_endpoints count"
        assert overview['total_endpoints'] > 0, "Should have counted endpoints"
        
        # Verify modules section
        modules = documentation['modules']
        assert len(modules) > 0, "Should have generated module documentation"
        
        # Verify at least one module has proper structure
        first_module = next(iter(modules.values()))
        assert hasattr(first_module, 'endpoints') or 'endpoints' in first_module.__dict__, "Module should have endpoints"
        
        # Step 3: Generate Markdown output
        markdown_file = os.path.join(temp_output_dir, "api_documentation.md")
        generated_file = generator.generate_markdown_file(documentation, markdown_file)
        
        # Verify file was created
        assert os.path.exists(generated_file), "Markdown file should be created"
        assert os.path.getsize(generated_file) > 0, "Markdown file should not be empty"
        
        # Step 4: Generate module-specific files
        module_files = generator.generate_module_markdown_files(documentation, temp_output_dir)
        
        # Verify module files were created
        assert len(module_files) > 0, "Should generate module files"
        for file_path in module_files:
            assert os.path.exists(file_path), f"Module file should exist: {file_path}"
            assert os.path.getsize(file_path) > 0, f"Module file should not be empty: {file_path}"
    
    def test_endpoint_analysis_completeness(self, generator):
        """
        Test that endpoint analysis covers all expected endpoints.
        Requirements: 1.1, 1.2
        """
        endpoints = generator.analyze_endpoints()
        
        # Verify we have endpoints from different modules
        modules_found = set()
        for endpoint in endpoints:
            modules_found.add(endpoint.module)
        
        # Should have multiple modules (at least 3)
        assert len(modules_found) >= 3, f"Should find endpoints from multiple modules, found: {modules_found}"
        
        # Verify no one_time_scripts endpoints are included
        one_time_scripts_endpoints = [ep for ep in endpoints if 'one_time_scripts' in ep.path]
        assert len(one_time_scripts_endpoints) == 0, "Should exclude one_time_scripts endpoints"
        
        # Verify endpoints have dependency information
        endpoints_with_deps = [ep for ep in endpoints if ep.dependencies]
        assert len(endpoints_with_deps) > 0, "Some endpoints should have dependencies traced"
    
    def test_dependency_chain_tracing(self, generator):
        """
        Test dependency chain tracing for endpoints.
        Requirements: 1.2, 3.1, 3.2
        """
        endpoints = generator.analyze_endpoints()
        
        # Test dependency tracing for a few endpoints
        for endpoint in endpoints[:3]:  # Test first 3 endpoints
            dependency_chain = generator.trace_dependencies(endpoint)
            
            # Verify dependency chain structure
            assert hasattr(dependency_chain, 'endpoint'), "Dependency chain should have endpoint"
            assert hasattr(dependency_chain, 'direct_dependencies'), "Should have direct_dependencies"
            assert hasattr(dependency_chain, 'database_queries'), "Should have database_queries"
            assert hasattr(dependency_chain, 'external_services'), "Should have external_services"
            assert hasattr(dependency_chain, 'middleware'), "Should have middleware"
            assert hasattr(dependency_chain, 'schemas'), "Should have schemas"
            
            # Verify endpoint identifier
            expected_endpoint = f"{endpoint.method} {endpoint.path}"
            assert dependency_chain.endpoint == expected_endpoint, "Dependency chain should identify correct endpoint"
    
    def test_module_documentation_generation(self, generator):
        """
        Test module-specific documentation generation.
        Requirements: 4.1, 4.2, 4.3
        """
        endpoints = generator.analyze_endpoints()
        
        # Group endpoints by modules
        grouped_endpoints = generator.documenter.group_endpoints_by_modules(endpoints)
        
        # Verify we have multiple modules
        assert len(grouped_endpoints) > 0, "Should group endpoints into modules"
        
        # Test documentation generation for each module
        for module_name, module_endpoints in grouped_endpoints.items():
            if len(module_endpoints) == 0:
                continue
                
            module_doc = generator.generate_module_docs(module_name)
            
            # Verify module documentation structure
            assert hasattr(module_doc, 'name') or hasattr(module_doc, '__dict__'), "Module doc should have structure"
            
            # Verify module has endpoints
            if hasattr(module_doc, 'endpoints'):
                endpoints_list = module_doc.endpoints
            else:
                endpoints_list = getattr(module_doc, 'endpoints', [])
            
            assert len(endpoints_list) > 0, f"Module {module_name} should have endpoints documented"
    
    def test_example_generation(self, generator):
        """
        Test example generation for endpoints.
        Requirements: 5.1, 5.2, 5.4
        """
        endpoints = generator.analyze_endpoints()
        
        # Test example generation for a few endpoints
        for endpoint in endpoints[:3]:  # Test first 3 endpoints
            examples = generator.create_examples(endpoint)
            
            # Examples might be empty for some endpoints, but should be a list
            assert isinstance(examples, list), "Examples should be returned as a list"
            
            # If examples exist, verify their structure
            for example in examples:
                assert hasattr(example, 'title') or 'title' in example.__dict__, "Example should have title"
                # Other attributes might vary based on implementation
    
    def test_integration_documentation(self, generator):
        """
        Test integration documentation generation.
        Requirements: 8.1, 8.2, 8.3
        """
        integration_doc = generator.generate_integration_documentation()
        
        # Verify integration documentation was generated
        assert isinstance(integration_doc, str), "Integration doc should be a string"
        assert len(integration_doc) > 0, "Integration doc should not be empty"
        
        # Verify it contains expected sections (checking for Russian text)
        assert "Интеграции" in integration_doc or "Integration" in integration_doc or "integration" in integration_doc, "Should mention integration"
    
    def test_validation_functionality(self, generator):
        """
        Test documentation validation functionality.
        Requirements: 1.1, 1.3
        """
        # Generate documentation first
        generator.analyze_endpoints()
        documentation = generator.generate_documentation()
        
        # Test validation
        validation_result = generator.validate_documentation()
        
        # Verify validation structure
        assert 'valid' in validation_result, "Validation should have 'valid' field"
        assert 'warnings' in validation_result, "Validation should have 'warnings' field"
        assert 'errors' in validation_result, "Validation should have 'errors' field"
        
        # Verify validation results are reasonable
        assert isinstance(validation_result['valid'], bool), "Valid should be boolean"
        assert isinstance(validation_result['warnings'], list), "Warnings should be a list"
        assert isinstance(validation_result['errors'], list), "Errors should be a list"


class TestDocumentationCLIIntegration:
    """Integration tests for the CLI interface."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return DocumentationCLI()
    
    def test_cli_full_generation_process(self, cli, temp_output_dir):
        """
        Test full CLI documentation generation process.
        Requirements: 1.1, 1.2, 1.3
        """
        # Prepare CLI arguments
        args = [
            '--app', 'core.main:app',
            '--output', temp_output_dir,
            '--format', 'markdown',
            '--quiet'  # Reduce log output during testing
        ]
        
        # Mock sys.argv to avoid conflicts
        with patch('sys.argv', ['docs-generator'] + args):
            # Run CLI
            exit_code = cli.run(args)
            
            # Verify successful execution
            assert exit_code == 0, "CLI should exit successfully"
            
            # Verify output files were created
            output_path = Path(temp_output_dir)
            generated_files = list(output_path.glob('*.md'))
            
            assert len(generated_files) > 0, "Should generate markdown files"
            
            # Verify README.md exists (overview file)
            readme_file = output_path / "README.md"
            assert readme_file.exists(), "Should generate README.md overview file"
            assert readme_file.stat().st_size > 0, "README.md should not be empty"
    
    def test_cli_json_output_format(self, cli, temp_output_dir):
        """
        Test CLI JSON output format.
        Requirements: 1.1, 1.3
        """
        # Prepare CLI arguments for JSON output
        args = [
            '--app', 'core.main:app',
            '--output', temp_output_dir,
            '--format', 'json',
            '--quiet'
        ]
        
        # Run CLI
        with patch('sys.argv', ['docs-generator'] + args):
            exit_code = cli.run(args)
            
            # Verify successful execution
            assert exit_code == 0, "CLI should exit successfully"
            
            # Verify JSON file was created
            output_path = Path(temp_output_dir)
            json_files = list(output_path.glob('*.json'))
            
            assert len(json_files) > 0, "Should generate JSON file"
            
            # Verify JSON content
            json_file = json_files[0]
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verify JSON structure
            assert 'overview' in data, "JSON should have overview section"
            assert 'modules' in data, "JSON should have modules section"
            assert 'endpoints' in data, "JSON should have endpoints section"
    
    def test_cli_single_file_output(self, cli, temp_output_dir):
        """
        Test CLI single file output option.
        Requirements: 1.3
        """
        # Prepare CLI arguments for single file output
        args = [
            '--app', 'core.main:app',
            '--output', temp_output_dir,
            '--format', 'markdown',
            '--single-file',
            '--quiet'
        ]
        
        # Run CLI
        with patch('sys.argv', ['docs-generator'] + args):
            exit_code = cli.run(args)
            
            # Verify successful execution
            assert exit_code == 0, "CLI should exit successfully"
            
            # Verify single file was created
            output_path = Path(temp_output_dir)
            md_files = list(output_path.glob('*.md'))
            
            # Should have one or two markdown files (main + integration)
            assert len(md_files) >= 1, "Should generate at least one markdown file"
            assert len(md_files) <= 2, "Should generate at most two markdown files (main + integration)"
            
            # Verify file content
            md_file = md_files[0]
            assert md_file.stat().st_size > 0, "Single markdown file should not be empty"
    
    def test_cli_validation_only_mode(self, cli):
        """
        Test CLI validation-only mode.
        Requirements: 1.1, 1.3
        """
        # Prepare CLI arguments for validation only
        args = [
            '--app', 'core.main:app',
            '--validate-only',
            '--quiet'
        ]
        
        # Run CLI
        with patch('sys.argv', ['docs-generator'] + args):
            exit_code = cli.run(args)
            
            # Validation should complete successfully
            # Exit code 0 means validation passed, 1 means validation failed
            assert exit_code in [0, 1], "CLI should exit with validation result"
    
    def test_cli_dry_run_mode(self, cli):
        """
        Test CLI dry-run mode.
        Requirements: 1.1
        """
        # Prepare CLI arguments for dry run
        args = [
            '--app', 'core.main:app',
            '--dry-run',
            '--quiet'
        ]
        
        # Run CLI
        with patch('sys.argv', ['docs-generator'] + args):
            exit_code = cli.run(args)
            
            # Dry run should complete successfully
            assert exit_code == 0, "CLI dry run should exit successfully"


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    @pytest.fixture
    def generator(self):
        """Create documentation generator instance."""
        return DocumentationGenerator(app)
    
    def test_large_application_performance(self, generator):
        """
        Test performance with the full application.
        Requirements: 1.1, 1.2
        """
        import time
        
        # Measure endpoint analysis time
        start_time = time.time()
        endpoints = generator.analyze_endpoints()
        analysis_time = time.time() - start_time
        
        # Should complete analysis in reasonable time (< 30 seconds)
        assert analysis_time < 30, f"Endpoint analysis took too long: {analysis_time:.2f}s"
        
        # Measure full documentation generation time
        start_time = time.time()
        documentation = generator.generate_documentation()
        generation_time = time.time() - start_time
        
        # Should complete generation in reasonable time (< 60 seconds)
        assert generation_time < 60, f"Documentation generation took too long: {generation_time:.2f}s"
        
        # Verify reasonable number of endpoints were processed
        assert len(endpoints) > 5, "Should process a reasonable number of endpoints"
    
    def test_error_handling_with_problematic_endpoints(self, generator):
        """
        Test error handling when encountering problematic endpoints.
        Requirements: 1.1, 1.2
        """
        # This test verifies that the generator handles errors gracefully
        # and continues processing other endpoints
        
        endpoints = generator.analyze_endpoints()
        
        # Should still find endpoints even if some fail to analyze
        assert len(endpoints) > 0, "Should find some endpoints despite potential errors"
        
        # Generate documentation - should not crash
        documentation = generator.generate_documentation()
        
        # Should have basic structure even with some failures
        assert 'overview' in documentation, "Should have overview despite potential errors"
        assert 'modules' in documentation, "Should have modules despite potential errors"
    
    def test_memory_usage_with_large_documentation(self, generator):
        """
        Test memory usage doesn't grow excessively.
        Requirements: 1.1, 1.2
        """
        try:
            import psutil
            import os
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Generate documentation
            endpoints = generator.analyze_endpoints()
            documentation = generator.generate_documentation()
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 500MB)
            assert memory_increase < 500, f"Memory usage increased too much: {memory_increase:.2f}MB"
            
        except ImportError:
            # Skip test if psutil is not available
            pytest.skip("psutil not available, skipping memory usage test")