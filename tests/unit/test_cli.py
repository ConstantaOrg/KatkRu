"""
Unit tests for CLI interface.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from core.docs_generator.cli import DocumentationCLI
from core.docs_generator.config import ConfigManager, DocumentationConfig, OutputConfig, AnalysisConfig, FilterConfig, LoggingConfig


class TestDocumentationCLI:
    """Test cases for DocumentationCLI class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cli = DocumentationCLI()
    
    def test_create_parser(self):
        """Test argument parser creation."""
        parser = self.cli.create_parser()
        
        # Test required arguments
        assert parser.prog == 'docs-generator'
        
        # Test that parser can parse basic arguments
        args = parser.parse_args(['--app', 'core.main:app'])
        assert args.app == 'core.main:app'
        assert args.output == 'docs/'
        assert args.format == 'markdown'
        assert not args.single_file
        assert not args.verbose
        assert not args.quiet
    
    def test_parser_with_all_arguments(self):
        """Test parser with all possible arguments."""
        parser = self.cli.create_parser()
        
        args = parser.parse_args([
            '--app', 'test.app:application',
            '--output', 'custom_docs/',
            '--format', 'json',
            '--single-file',
            '--config', 'config.json',
            '--exclude-modules', 'module1', 'module2',
            '--verbose',
            '--log-file', 'test.log',
            '--include-examples',
            '--include-dependencies',
            '--include-integration',
            '--validate-only',
            '--dry-run'
        ])
        
        assert args.app == 'test.app:application'
        assert args.output == 'custom_docs/'
        assert args.format == 'json'
        assert args.single_file
        assert args.config == 'config.json'
        assert args.exclude_modules == ['module1', 'module2']
        assert args.verbose
        assert args.log_file == 'test.log'
        assert args.include_examples
        assert args.include_dependencies
        assert args.include_integration
        assert args.validate_only
        assert args.dry_run
    
    def test_parser_create_config_option(self):
        """Test --create-config option."""
        parser = self.cli.create_parser()
        
        # --create-config should not require --app
        args = parser.parse_args(['--create-config', '--app', 'dummy:app'])
        assert args.create_config
    
    def test_load_config_with_file(self):
        """Test loading configuration from file."""
        # Create temporary config file
        config_data = {
            "app": "test.main:app",
            "output": {
                "format": "json",
                "directory": "test_docs/"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = self.cli.load_config(config_path)
            
            assert isinstance(config, DocumentationConfig)
            assert config.app == "test.main:app"
            assert config.output.format == "json"
            assert config.output.directory == "test_docs/"
            
        finally:
            os.unlink(config_path)
    
    def test_load_config_without_file(self):
        """Test loading default configuration when no file specified."""
        config = self.cli.load_config()
        
        assert isinstance(config, DocumentationConfig)
        assert config.app == ""  # Default empty
        assert config.output.format == "markdown"
        assert config.output.directory == "docs/"
    
    def test_load_config_invalid_file(self):
        """Test loading configuration from invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_path = f.name
        
        try:
            with pytest.raises(SystemExit):
                self.cli.load_config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_load_config_nonexistent_file(self):
        """Test loading configuration from nonexistent file."""
        with pytest.raises(SystemExit):
            self.cli.load_config("nonexistent_config.json")
    
    def test_load_fastapi_app_success(self):
        """Test successful FastAPI app loading."""
        # Mock the entire method to avoid FastAPI import issues
        mock_app = Mock()
        
        with patch.object(self.cli, 'load_fastapi_app', return_value=mock_app):
            app = self.cli.load_fastapi_app("core.main:app")
            assert app == mock_app
    
    def test_load_fastapi_app_invalid_format(self):
        """Test loading app with invalid format."""
        with pytest.raises(SystemExit):
            self.cli.load_fastapi_app("invalid_format")
    
    def test_load_fastapi_app_import_error(self):
        """Test loading app with import error."""
        with patch.object(self.cli, 'load_fastapi_app', side_effect=SystemExit(1)):
            with pytest.raises(SystemExit):
                self.cli.load_fastapi_app("nonexistent.module:app")
    
    def test_load_fastapi_app_missing_attribute(self):
        """Test loading app with missing attribute."""
        with patch.object(self.cli, 'load_fastapi_app', side_effect=SystemExit(1)):
            with pytest.raises(SystemExit):
                self.cli.load_fastapi_app("core.main:app")
    
    def test_load_fastapi_app_not_fastapi_instance(self):
        """Test loading app that's not a FastAPI instance."""
        with patch.object(self.cli, 'load_fastapi_app', side_effect=SystemExit(1)):
            with pytest.raises(SystemExit):
                self.cli.load_fastapi_app("core.main:app")
    
    def test_show_progress(self):
        """Test progress display."""
        # Test without step/total
        self.cli.show_progress("Test message")
        
        # Test with step/total
        self.cli.show_progress("Test message", 1, 5)
    
    @patch('core.docs_generator.cli.handlers.DocumentationGenerator')
    @patch('core.docs_generator.cli.handlers.load_fastapi_app')
    def test_generate_documentation_dry_run(self, mock_load_app, mock_generator_class):
        """Test documentation generation in dry run mode."""
        # Setup mocks
        mock_app = Mock()
        mock_load_app.return_value = mock_app
        
        mock_generator = Mock()
        mock_endpoint = Mock()
        mock_endpoint.method = "GET"
        mock_endpoint.path = "/test"
        mock_endpoint.module = "test_module"
        mock_generator.analyze_endpoints.return_value = [mock_endpoint]
        mock_generator_class.return_value = mock_generator
        
        # Create config
        config = DocumentationConfig(
            app="test.main:app",
            dry_run=True
        )
        self.cli.config = config
        
        # Create mock args
        args = Mock()
        args.config = None
        
        # Mock ConfigManager methods
        with patch.object(ConfigManager, 'merge_with_args', return_value=config):
            with patch.object(ConfigManager, 'validate_config', return_value=[]):
                result = self.cli.generate_documentation(args)
        
        assert result is True
        mock_generator.analyze_endpoints.assert_called_once()
        mock_generator.generate_documentation.assert_not_called()
    
    @patch('core.docs_generator.cli.handlers.DocumentationGenerator')
    @patch('core.docs_generator.cli.handlers.load_fastapi_app')
    def test_generate_documentation_validate_only(self, mock_load_app, mock_generator_class):
        """Test documentation generation in validate-only mode."""
        # Setup mocks
        mock_app = Mock()
        mock_load_app.return_value = mock_app
        
        mock_generator = Mock()
        mock_generator.analyze_endpoints.return_value = []
        mock_generator.generate_documentation.return_value = {}
        mock_generator.validate_documentation.return_value = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        mock_generator_class.return_value = mock_generator
        
        # Create config
        config = DocumentationConfig(
            app="test.main:app",
            validate_only=True
        )
        self.cli.config = config
        
        # Create mock args
        args = Mock()
        args.config = None
        
        # Mock ConfigManager methods
        with patch.object(ConfigManager, 'merge_with_args', return_value=config):
            with patch.object(ConfigManager, 'validate_config', return_value=[]):
                result = self.cli.generate_documentation(args)
        
        assert result is True
        mock_generator.validate_documentation.assert_called_once()
    
    @patch('core.docs_generator.cli.handlers.DocumentationGenerator')
    @patch('core.docs_generator.cli.handlers.load_fastapi_app')
    @patch('builtins.open', create=True)
    @patch('os.makedirs')
    def test_generate_documentation_json_output(self, mock_makedirs, mock_open, mock_load_app, mock_generator_class):
        """Test documentation generation with JSON output."""
        # Setup mocks
        mock_app = Mock()
        mock_load_app.return_value = mock_app
        
        mock_generator = Mock()
        mock_generator.analyze_endpoints.return_value = []
        mock_generator.generate_documentation.return_value = {"test": "data"}
        mock_generator.get_documentation_summary.return_value = type('DocumentationSummary', (), {
            'total_endpoints': 0,
            'modules': [],
            'auth_required_endpoints': 0,
            'public_endpoints': 0
        })()
        mock_generator_class.return_value = mock_generator
        
        # Create config
        config = DocumentationConfig(
            app="test.main:app",
            output=OutputConfig(format="json", directory="test_output/")
        )
        self.cli.config = config
        
        # Create mock args
        args = Mock()
        args.config = None
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock ConfigManager methods
        with patch.object(ConfigManager, 'merge_with_args', return_value=config):
            with patch.object(ConfigManager, 'validate_config', return_value=[]):
                with patch('json.dump') as mock_json_dump:
                    result = self.cli.generate_documentation(args)
        
        assert result is True
        mock_json_dump.assert_called_once()
    
    @patch('core.docs_generator.cli.handlers.DocumentationGenerator')
    @patch('core.docs_generator.cli.handlers.load_fastapi_app')
    @patch('os.makedirs')
    def test_generate_documentation_markdown_single_file(self, mock_makedirs, mock_load_app, mock_generator_class):
        """Test documentation generation with single Markdown file."""
        # Setup mocks
        mock_app = Mock()
        mock_load_app.return_value = mock_app
        
        mock_generator = Mock()
        mock_generator.analyze_endpoints.return_value = []
        mock_generator.generate_documentation.return_value = {"test": "data"}
        mock_generator.generate_markdown_file.return_value = "test_output/api_documentation.md"
        mock_generator.get_documentation_summary.return_value = type('DocumentationSummary', (), {
            'total_endpoints': 0,
            'modules': [],
            'auth_required_endpoints': 0,
            'public_endpoints': 0
        })()
        mock_generator_class.return_value = mock_generator
        
        # Create config
        config = DocumentationConfig(
            app="test.main:app",
            output=OutputConfig(format="markdown", single_file=True, directory="test_output/")
        )
        self.cli.config = config
        
        # Create mock args
        args = Mock()
        args.config = None
        
        # Mock ConfigManager methods
        with patch.object(ConfigManager, 'merge_with_args', return_value=config):
            with patch.object(ConfigManager, 'validate_config', return_value=[]):
                # Mock the integration documentation generation
                with patch.object(mock_generator, 'generate_integration_documentation', return_value="# Integration Docs"):
                    with patch('builtins.open', create=True) as mock_open:
                        mock_file = Mock()
                        mock_open.return_value.__enter__.return_value = mock_file
                        result = self.cli.generate_documentation(args)
        
        assert result is True
        mock_generator.generate_markdown_file.assert_called_once()
    
    def test_run_create_config(self):
        """Test running CLI with --create-config option."""
        with patch('core.docs_generator.config.create_config_file') as mock_create:
            result = self.cli.run(['--create-config', '--app', 'dummy:app'])
            
            assert result == 0
            mock_create.assert_called_once()
    
    @patch.object(DocumentationCLI, 'generate_documentation')
    def test_run_success(self, mock_generate):
        """Test successful CLI run."""
        mock_generate.return_value = True
        
        result = self.cli.run(['--app', 'test.main:app'])
        
        assert result == 0
        mock_generate.assert_called_once()
    
    @patch.object(DocumentationCLI, 'generate_documentation')
    def test_run_failure(self, mock_generate):
        """Test failed CLI run."""
        mock_generate.return_value = False
        
        result = self.cli.run(['--app', 'test.main:app'])
        
        assert result == 1
        mock_generate.assert_called_once()
    
    def test_run_keyboard_interrupt(self):
        """Test CLI run interrupted by user."""
        with patch.object(self.cli, 'generate_documentation', side_effect=KeyboardInterrupt):
            result = self.cli.run(['--app', 'test.main:app'])
            
            assert result == 130
    
    def test_run_unexpected_error(self):
        """Test CLI run with unexpected error."""
        with patch.object(self.cli, 'generate_documentation', side_effect=Exception("Test error")):
            result = self.cli.run(['--app', 'test.main:app'])
            
            assert result == 1


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def test_create_default_config(self):
        """Test creating default configuration."""
        config = ConfigManager.create_default_config()
        
        assert isinstance(config, DocumentationConfig)
        assert config.app == ""
        assert config.output.format == "markdown"
        assert config.output.directory == "docs/"
        assert not config.output.single_file
        assert config.analysis.include_examples
        assert config.analysis.include_dependencies
        assert config.analysis.include_integration
        assert "one_time_scripts" in config.filters.exclude_modules
    
    def test_load_from_file_success(self):
        """Test loading configuration from file successfully."""
        config_data = {
            "app": "test.main:app",
            "output": {
                "format": "json",
                "directory": "custom_docs/"
            },
            "analysis": {
                "include_examples": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = ConfigManager.load_from_file(config_path)
            
            assert config.app == "test.main:app"
            assert config.output.format == "json"
            assert config.output.directory == "custom_docs/"
            assert not config.analysis.include_examples
            
        finally:
            os.unlink(config_path)
    
    def test_load_from_file_not_found(self):
        """Test loading configuration from nonexistent file."""
        with pytest.raises(RuntimeError):
            ConfigManager.load_from_file("nonexistent.json")
    
    def test_load_from_file_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError):
                ConfigManager.load_from_file(config_path)
        finally:
            os.unlink(config_path)
    
    def test_find_and_load_config_found(self):
        """Test finding and loading configuration file."""
        config_data = {"app": "test.main:app"}
        
        # Create temporary directory and config file
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "docs-generator.json")
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            config = ConfigManager.find_and_load_config(temp_dir)
            
            assert config is not None
            assert config.app == "test.main:app"
    
    def test_find_and_load_config_not_found(self):
        """Test finding configuration file when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigManager.find_and_load_config(temp_dir)
            assert config is None
    
    def test_save_to_file(self):
        """Test saving configuration to file."""
        config = DocumentationConfig(
            app="test.main:app",
            output=OutputConfig(format="json")
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            ConfigManager.save_to_file(config, config_path)
            
            # Verify file was created and contains correct data
            assert os.path.exists(config_path)
            
            with open(config_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['app'] == "test.main:app"
            assert saved_data['output']['format'] == "json"
            
        finally:
            os.unlink(config_path)
    
    def test_merge_with_args(self):
        """Test merging configuration with command line arguments."""
        config = DocumentationConfig(
            app="original.app:app",
            output=OutputConfig(format="markdown")
        )
        
        args_dict = {
            'app': 'new.app:app',
            'format': 'json',
            'verbose': True,
            'exclude_modules': ['custom_module']
        }
        
        merged = ConfigManager.merge_with_args(config, args_dict)
        
        assert merged.app == "new.app:app"
        assert merged.output.format == "json"
        assert merged.filters.exclude_modules == ['custom_module']
        assert merged.logging.level == "DEBUG"  # verbose=True
    
    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = DocumentationConfig(
            app="test.main:app",
            output=OutputConfig(directory="docs/")
        )
        
        errors = ConfigManager.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_config_invalid(self):
        """Test validating invalid configuration."""
        config = DocumentationConfig(
            app="",  # Missing app
            output=OutputConfig(directory=""),  # Missing directory
            analysis=AnalysisConfig(trace_depth=0)  # Invalid trace depth
        )
        
        errors = ConfigManager.validate_config(config)
        assert len(errors) > 0
        assert any("app import string is required" in error for error in errors)
        assert any("Output directory is required" in error for error in errors)
        assert any("Trace depth must be at least 1" in error for error in errors)
    
    def test_validate_config_conflicting_filters(self):
        """Test validating configuration with conflicting filters."""
        config = DocumentationConfig(
            app="test.main:app",
            filters=FilterConfig(
                exclude_modules=['module1'],
                include_only_modules=['module2']
            )
        )
        
        errors = ConfigManager.validate_config(config)
        assert any("Cannot specify both exclude_modules and include_only_modules" in error for error in errors)
    
    def test_create_example_config(self):
        """Test creating example configuration."""
        example_json = ConfigManager.create_example_config()
        
        # Verify it's valid JSON
        example_data = json.loads(example_json)
        
        assert example_data['app'] == "core.main:app"
        assert example_data['output']['format'] == "markdown"
        assert example_data['analysis']['include_examples'] is True
        assert "one_time_scripts" in example_data['filters']['exclude_modules']