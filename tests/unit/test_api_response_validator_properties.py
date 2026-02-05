"""
Property-based tests for API Response Validator

These tests validate the correctness properties of the independent
test framework, ensuring it works correctly across all inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Any, List
import json

from tests.utils.api_response_validator import (
    APIResponseValidator,
    ValidationRule,
    ValidationResult,
    EndpointValidator
)


# Generators for test data
@st.composite
def valid_response_data(draw):
    """Generate valid response data structures."""
    return draw(st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'),
        values=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.booleans(),
            st.lists(st.integers(), max_size=5),
            st.lists(st.text(), max_size=5)
        ),
        min_size=1,
        max_size=10
    ))


@st.composite
def validation_rules(draw):
    """Generate validation rules."""
    field_name = draw(st.text(min_size=1, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'))
    field_type = draw(st.sampled_from([int, str, bool, float, list, dict]))
    required = draw(st.booleans())
    
    return ValidationRule(
        field_name=field_name,
        field_type=field_type,
        required=required
    )


class TestAPIResponseValidatorProperties:
    """Property-based tests for APIResponseValidator."""
    
    @given(valid_response_data(), st.lists(st.text(min_size=1, max_size=15), min_size=1, max_size=5))
    def test_property_1_test_framework_independence(self, response_data: Dict[str, Any], required_fields: List[str]):
        """
        **Property 1: Test Framework Independence**
        
        For any API endpoint and any response model change that doesn't affect actual endpoint behavior,
        the test framework should continue to validate the endpoint correctly without test failures.
        
        **Validates: Requirements 1.2, 7.1**
        """
        # Create validator that focuses on essential fields only
        validator = APIResponseValidator(strict_mode=False)
        
        # Add only essential validation rules (simulating core business logic)
        essential_fields = required_fields[:2] if len(required_fields) >= 2 else required_fields
        for field in essential_fields:
            if field in response_data:
                field_type = type(response_data[field])
                validator.add_rule(ValidationRule(field, field_type, required=True))
        
        # Validate original response
        original_result = validator.validate_response(response_data)
        
        # Simulate "response model change" by adding additional fields
        # (this represents documentation model changes that don't affect actual API behavior)
        modified_response = response_data.copy()
        modified_response.update({
            "additional_doc_field": "documentation_only",
            "model_specific_field": 42,
            "auto_generated_field": True
        })
        
        # Validate modified response
        modified_result = validator.validate_response(modified_response)
        
        # Property: Validation should remain consistent when non-essential fields are added
        # The validator should not fail due to additional fields when in non-strict mode
        if original_result.is_valid:
            assert modified_result.is_valid, (
                f"Test framework failed independence test. "
                f"Original errors: {original_result.errors}, "
                f"Modified errors: {modified_result.errors}"
            )
        
        # Essential field validation should be identical
        essential_errors = [e for e in original_result.errors if any(f in e for f in essential_fields)]
        modified_essential_errors = [e for e in modified_result.errors if any(f in e for f in essential_fields)]
        
        assert essential_errors == modified_essential_errors, (
            "Essential field validation changed when non-essential fields were added"
        )
    
    @given(valid_response_data())
    def test_property_2_direct_response_validation(self, response_data: Dict[str, Any]):
        """
        **Property 2: Direct Response Validation**
        
        For any API endpoint response, the test framework should validate actual response data structure
        and content without depending on response model validation.
        
        **Validates: Requirements 1.1, 1.3, 7.2**
        """
        # Create validator that works directly with response data
        validator = APIResponseValidator(strict_mode=False)
        
        # Extract actual field types from the response (simulating direct inspection)
        actual_fields = {}
        for field_name, field_value in response_data.items():
            actual_fields[field_name] = type(field_value)
            validator.add_rule(ValidationRule(field_name, type(field_value), required=True))
        
        # Validate using direct response inspection (no model dependency)
        result = validator.validate_response(response_data)
        
        # Property: Direct validation should succeed for actual response structure
        assert result.is_valid, f"Direct response validation failed: {result.errors}"
        
        # Property: Validator should detect type mismatches in actual data
        if response_data:  # Only test if we have data
            # Create a response with wrong types
            corrupted_response = {}
            for field_name, field_value in response_data.items():
                # Change the type of the first field to test type validation
                if field_name == list(response_data.keys())[0]:
                    if isinstance(field_value, int):
                        corrupted_response[field_name] = "not_an_int"
                    elif isinstance(field_value, str):
                        corrupted_response[field_name] = 42
                    elif isinstance(field_value, bool):
                        corrupted_response[field_name] = "not_a_bool"
                    else:
                        corrupted_response[field_name] = "wrong_type"
                else:
                    corrupted_response[field_name] = field_value
            
            # Validate corrupted response
            corrupted_result = validator.validate_response(corrupted_response)
            
            # Property: Should detect type mismatches
            if corrupted_response != response_data:  # Only if we actually changed something
                assert not corrupted_result.is_valid, (
                    "Direct validation should detect type mismatches in actual response data"
                )
    
    @given(st.lists(st.integers(min_value=200, max_value=599), min_size=1, max_size=5))
    def test_property_status_code_independence(self, expected_statuses: List[int]):
        """
        **Property 10: Status Code Independence**
        
        For any API endpoint, the test framework should validate HTTP status codes
        correctly regardless of response model definitions.
        
        **Validates: Requirements 1.4**
        """
        validator = APIResponseValidator()
        
        # Test each expected status code
        for status in expected_statuses:
            result = validator.validate_status_code(status, expected_statuses)
            assert result.is_valid, f"Status code {status} should be valid in {expected_statuses}"
        
        # Test invalid status codes
        invalid_status = max(expected_statuses) + 100  # Ensure it's not in the list
        assume(invalid_status not in expected_statuses)
        
        result = validator.validate_status_code(invalid_status, expected_statuses)
        assert not result.is_valid, f"Status code {invalid_status} should be invalid for {expected_statuses}"
    
    @given(valid_response_data(), st.lists(validation_rules(), min_size=1, max_size=5))
    def test_property_essential_field_validation(self, response_data: Dict[str, Any], rules: List[ValidationRule]):
        """
        **Property 5: Essential Field Validation**
        
        For any API response, the test framework should verify that required fields exist
        with correct types while allowing additional non-breaking fields.
        
        **Validates: Requirements 4.1, 4.3, 4.2**
        """
        validator = APIResponseValidator(strict_mode=False)  # Allow additional fields
        
        # Add rules for fields that exist in the response
        applicable_rules = []
        for rule in rules:
            if rule.field_name in response_data:
                # Adjust rule type to match actual data
                actual_type = type(response_data[rule.field_name])
                adjusted_rule = ValidationRule(
                    field_name=rule.field_name,
                    field_type=actual_type,
                    required=rule.required
                )
                validator.add_rule(adjusted_rule)
                applicable_rules.append(adjusted_rule)
        
        # Validate original response
        result = validator.validate_response(response_data)
        
        # Property: Should validate essential fields correctly
        if applicable_rules:  # Only test if we have applicable rules
            # All required fields that exist should pass validation
            required_field_errors = [
                e for e in result.errors 
                if any(rule.field_name in e for rule in applicable_rules if rule.required)
            ]
            
            # Should not have errors for fields that exist with correct types
            assert len(required_field_errors) == 0, (
                f"Essential field validation failed: {required_field_errors}"
            )
        
        # Property: Additional fields should not cause validation failure
        response_with_additional = response_data.copy()
        response_with_additional["additional_field"] = "should_be_allowed"
        response_with_additional["another_extra"] = 999
        
        additional_result = validator.validate_response(response_with_additional)
        
        # Should still be valid (allowing additional fields)
        if result.is_valid:
            assert additional_result.is_valid, (
                "Additional non-breaking fields should not cause validation failure"
            )
    
    @given(st.lists(valid_response_data(), min_size=1, max_size=3))
    def test_property_business_logic_independence(self, response_list: List[Dict[str, Any]]):
        """
        **Property 6: Business Logic Independence**
        
        For any endpoint with business logic, the test framework should validate
        the correctness of business logic independent of documentation models.
        
        **Validates: Requirements 7.4, 3.2**
        """
        # Create business rules that operate on actual response data
        def has_required_structure(response: Dict[str, Any]) -> bool:
            """Business rule: response should be a non-empty dictionary."""
            return isinstance(response, dict) and len(response) > 0
        
        def consistent_data_types(response: Dict[str, Any]) -> bool:
            """Business rule: if 'id' field exists, it should be numeric."""
            if 'id' in response:
                return isinstance(response['id'], (int, float))
            return True
        
        validator = APIResponseValidator()
        business_rules = [has_required_structure, consistent_data_types]
        
        # Test each response against business logic
        for response_data in response_list:
            result = validator.validate_business_logic(response_data, business_rules)
            
            # Property: Business logic validation should work independently
            # The validation should depend only on actual data, not on models
            
            # Check first rule
            expected_structure_valid = isinstance(response_data, dict) and len(response_data) > 0
            
            # Check second rule
            expected_id_valid = True
            if 'id' in response_data:
                expected_id_valid = isinstance(response_data['id'], (int, float))
            
            expected_valid = expected_structure_valid and expected_id_valid
            
            assert result.is_valid == expected_valid, (
                f"Business logic validation mismatch. "
                f"Expected: {expected_valid}, Got: {result.is_valid}, "
                f"Errors: {result.errors}, Response: {response_data}"
            )

    @given(valid_response_data())
    def test_property_3_model_accuracy_consistency(self, response_data: Dict[str, Any]):
        """
        **Property 3: Model Accuracy Consistency**
        
        For any response model and its corresponding endpoint, the model schema should match
        the actual data structure, field types, and field requirements returned by the endpoint.
        
        **Validates: Requirements 2.1, 2.3, 2.5**
        """
        # Simulate a response model definition based on actual response
        model_fields = {}
        for field_name, field_value in response_data.items():
            model_fields[field_name] = {
                'type': type(field_value),
                'required': True,  # Assume all fields in actual response are required
                'example': field_value
            }
        
        # Create validator based on the "model" (which matches actual response)
        validator = APIResponseValidator(strict_mode=True)
        for field_name, field_info in model_fields.items():
            validator.add_rule(ValidationRule(
                field_name=field_name,
                field_type=field_info['type'],
                required=field_info['required']
            ))
        
        # Property: Model that matches actual response should validate successfully
        result = validator.validate_response(response_data)
        assert result.is_valid, (
            f"Model accuracy test failed - model based on actual response should validate: {result.errors}"
        )
        
        # Property: Model with incorrect field types should fail validation
        if response_data:  # Only test if we have data
            # Create a model with wrong field type for the first field
            first_field = list(response_data.keys())[0]
            first_value = response_data[first_field]
            
            # Create validator with wrong type for first field
            inaccurate_validator = APIResponseValidator(strict_mode=True)
            
            # Add wrong type for first field
            wrong_type = str if not isinstance(first_value, str) else int
            inaccurate_validator.add_rule(ValidationRule(
                field_name=first_field,
                field_type=wrong_type,
                required=True
            ))
            
            # Add correct types for other fields
            for field_name, field_value in response_data.items():
                if field_name != first_field:
                    inaccurate_validator.add_rule(ValidationRule(
                        field_name=field_name,
                        field_type=type(field_value),
                        required=True
                    ))
            
            # Validate with inaccurate model
            inaccurate_result = inaccurate_validator.validate_response(response_data)
            
            # Property: Inaccurate model should fail validation
            assert not inaccurate_result.is_valid, (
                f"Inaccurate model should fail validation but passed. "
                f"Expected type mismatch for field '{first_field}'"
            )
            
            # Property: Error should specifically mention the type mismatch
            type_error_found = any(
                first_field in error and "type" in error.lower()
                for error in inaccurate_result.errors
            )
            assert type_error_found, (
                f"Should report type mismatch error for field '{first_field}'. "
                f"Errors: {inaccurate_result.errors}"
            )


class TestEndpointValidatorProperties:
    """Property-based tests for EndpointValidator."""
    
    @given(st.integers(min_value=200, max_value=599), valid_response_data())
    def test_property_multi_response_scenario_handling(self, status_code: int, response_data: Dict[str, Any]):
        """
        **Property 4: Multi-Response Scenario Handling**
        
        For any endpoint that can return different response formats or status codes,
        the system should properly handle and validate all possible response scenarios.
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        # Create endpoint validator with multiple status scenarios
        endpoint_validator = EndpointValidator("/test/endpoint", "POST")
        
        # Add validators for different status codes
        success_validator = APIResponseValidator(strict_mode=False)
        success_validator.add_rule(ValidationRule("success", bool, required=True))
        
        error_validator = APIResponseValidator(strict_mode=False)
        error_validator.add_rule(ValidationRule("error", str, required=True))
        
        endpoint_validator.add_status_validator(200, success_validator)
        endpoint_validator.add_status_validator(400, error_validator)
        endpoint_validator.add_status_validator(500, error_validator)
        
        # Property: Should handle configured status codes appropriately
        if status_code in [200, 400, 500]:
            # Prepare appropriate response data for the status code
            if status_code == 200:
                test_response = {"success": True, **response_data}
            else:  # 400 or 500
                test_response = {"error": "Test error message", **response_data}
            
            result = endpoint_validator.validate_response(status_code, test_response)
            
            # Should successfully validate configured scenarios
            assert result.is_valid, (
                f"Multi-response scenario validation failed for status {status_code}: {result.errors}"
            )
        else:
            # Should handle unconfigured status codes gracefully
            result = endpoint_validator.validate_response(status_code, response_data)
            assert not result.is_valid, (
                f"Should reject unconfigured status code {status_code}"
            )
            assert any("No validator configured" in error for error in result.errors), (
                f"Should provide clear error for unconfigured status code"
            )


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v"])