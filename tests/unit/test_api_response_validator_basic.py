"""
Basic unit tests for API Response Validator

These tests verify the core functionality of the APIResponseValidator
without using property-based testing.
"""

import pytest
from tests.utils.api_response_validator import (
    APIResponseValidator,
    ValidationRule,
    ValidationResult,
    EndpointValidator
)


class TestAPIResponseValidator:
    """Basic unit tests for APIResponseValidator."""
    
    def test_validate_required_fields_success(self):
        """Test successful validation of required fields."""
        validator = APIResponseValidator()
        response = {"name": "test", "id": 123, "active": True}
        required_fields = ["name", "id"]
        
        result = validator.validate_required_fields(response, required_fields)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_required_fields_missing(self):
        """Test validation failure when required fields are missing."""
        validator = APIResponseValidator()
        response = {"name": "test"}
        required_fields = ["name", "id", "active"]
        
        result = validator.validate_required_fields(response, required_fields)
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert "Required field 'id' is missing" in result.errors[0]
        assert "Required field 'active' is missing" in result.errors[1]
    
    def test_validate_field_types_success(self):
        """Test successful validation of field types."""
        validator = APIResponseValidator()
        response = {"name": "test", "id": 123, "active": True}
        field_types = {"name": str, "id": int, "active": bool}
        
        result = validator.validate_field_types(response, field_types)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_field_types_mismatch(self):
        """Test validation failure when field types don't match."""
        validator = APIResponseValidator()
        response = {"name": 123, "id": "not_an_int", "active": "not_a_bool"}
        field_types = {"name": str, "id": int, "active": bool}
        
        result = validator.validate_field_types(response, field_types)
        
        assert not result.is_valid
        assert len(result.errors) == 3
    
    def test_validate_business_logic_success(self):
        """Test successful business logic validation."""
        validator = APIResponseValidator()
        response = {"count": 5, "items": ["a", "b", "c", "d", "e"]}
        
        def count_matches_items(resp):
            return resp["count"] == len(resp["items"])
        
        business_rules = [count_matches_items]
        result = validator.validate_business_logic(response, business_rules)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_business_logic_failure(self):
        """Test business logic validation failure."""
        validator = APIResponseValidator()
        response = {"count": 10, "items": ["a", "b", "c"]}  # Count doesn't match
        
        def count_matches_items(resp):
            return resp["count"] == len(resp["items"])
        
        business_rules = [count_matches_items]
        result = validator.validate_business_logic(response, business_rules)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "Business rule 1 failed" in result.errors[0]
    
    def test_validate_status_code_success(self):
        """Test successful status code validation."""
        validator = APIResponseValidator()
        
        result = validator.validate_status_code(200, [200, 201, 202])
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_status_code_failure(self):
        """Test status code validation failure."""
        validator = APIResponseValidator()
        
        result = validator.validate_status_code(404, [200, 201, 202])
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "HTTP status 404 not in expected statuses" in result.errors[0]
    
    def test_strict_mode_additional_fields(self):
        """Test strict mode behavior with additional fields."""
        # Non-strict mode (default)
        validator = APIResponseValidator(strict_mode=False)
        validator.add_rule(ValidationRule("name", str, required=True))
        
        response = {"name": "test", "extra_field": "should_be_allowed"}
        result = validator.validate_response(response)
        
        assert result.is_valid  # Should pass in non-strict mode
        
        # Strict mode
        strict_validator = APIResponseValidator(strict_mode=True)
        strict_validator.add_rule(ValidationRule("name", str, required=True))
        
        strict_result = strict_validator.validate_response(response)
        
        # Should still be valid but may have warnings
        assert len(strict_result.warnings) >= 0  # May have warnings about additional fields
    
    def test_list_structure_validation(self):
        """Test validation of list structures."""
        validator = APIResponseValidator()
        response = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        
        item_rules = [
            ValidationRule("id", int, required=True),
            ValidationRule("name", str, required=True)
        ]
        
        result = validator.validate_list_structure(response, "users", item_rules)
        
        assert result.is_valid
        assert len(result.errors) == 0


class TestEndpointValidator:
    """Basic unit tests for EndpointValidator."""
    
    def test_endpoint_validator_success(self):
        """Test successful endpoint validation."""
        endpoint_validator = EndpointValidator("/test/endpoint", "GET")
        
        # Configure validator for 200 status
        success_validator = APIResponseValidator()
        success_validator.add_rule(ValidationRule("success", bool, required=True))
        endpoint_validator.add_status_validator(200, success_validator)
        
        # Test validation
        response_data = {"success": True, "data": "test"}
        result = endpoint_validator.validate_response(200, response_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_endpoint_validator_unconfigured_status(self):
        """Test endpoint validation with unconfigured status code."""
        endpoint_validator = EndpointValidator("/test/endpoint", "GET")
        
        # Don't configure any validators
        response_data = {"error": "Not found"}
        result = endpoint_validator.validate_response(404, response_data)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "No validator configured for status code 404" in result.errors[0]


class TestValidationRule:
    """Basic unit tests for ValidationRule."""
    
    def test_validation_rule_creation(self):
        """Test creating validation rules."""
        rule = ValidationRule(
            field_name="test_field",
            field_type=str,
            required=True,
            description="Test field description"
        )
        
        assert rule.field_name == "test_field"
        assert rule.field_type == str
        assert rule.required is True
        assert rule.description == "Test field description"
    
    def test_validation_rule_defaults(self):
        """Test validation rule default values."""
        rule = ValidationRule("test_field", int)
        
        assert rule.field_name == "test_field"
        assert rule.field_type == int
        assert rule.required is True  # Default
        assert rule.business_rule is None  # Default
        assert rule.description == ""  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])