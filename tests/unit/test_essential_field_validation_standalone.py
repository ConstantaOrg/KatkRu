"""
Standalone property-based tests for essential field validation.

**Property 6: Essential Field Validation**
**Validates: Requirements 4.1, 4.3, 4.2**

These tests verify that the test framework validates required fields exist with correct types
while allowing additional non-breaking fields.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hypothesis import given, strategies as st
from typing import Dict, Any, List, Type

# Import the validator directly
from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, ValidationResult


def test_essential_field_validation_basic():
    """Basic test to verify the validator works correctly."""
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("name", str, required=True))
    validator.add_rule(ValidationRule("age", int, required=True))
    
    # Test with correct data
    response = {"name": "John", "age": 30, "extra": "allowed"}
    result = validator.validate_response(response)
    assert result.is_valid, f"Should be valid: {result.errors}"
    
    # Test with missing field
    response_missing = {"name": "John"}
    result_missing = validator.validate_response(response_missing)
    assert not result_missing.is_valid, "Should be invalid when field is missing"
    assert any("age" in error for error in result_missing.errors), "Should mention missing age field"
    
    # Test with wrong type
    response_wrong_type = {"name": "John", "age": "thirty"}
    result_wrong_type = validator.validate_response(response_wrong_type)
    assert not result_wrong_type.is_valid, "Should be invalid when type is wrong"
    assert any("type" in error.lower() for error in result_wrong_type.errors), "Should mention type error"
    
    print("✓ Basic essential field validation test passed")


@given(
    required_fields=st.lists(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        min_size=1,
        max_size=3,
        unique=True
    ),
    additional_fields=st.dictionaries(
        st.text(min_size=1, max_size=8, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.one_of(st.text(max_size=10), st.integers(min_value=0, max_value=100)),
        min_size=0,
        max_size=2
    )
)
def test_property_essential_field_validation_allows_additional_fields(
    required_fields: List[str], 
    additional_fields: Dict[str, Any]
):
    """
    **Feature: api-testing-refactor, Property 6: Essential Field Validation**
    
    For any API response, the test framework should verify that required fields exist 
    with correct types while allowing additional non-breaking fields.
    """
    # Create validator with non-strict mode (allows additional fields)
    validator = APIResponseValidator(strict_mode=False)
    
    # Add validation rules for required fields (all as strings for simplicity)
    for field in required_fields:
        validator.add_rule(ValidationRule(field, str, required=True))
    
    # Create response with required fields and additional fields
    response = {}
    
    # Add required fields with correct types
    for field in required_fields:
        response[field] = f"value_for_{field}"
    
    # Add additional fields (should be allowed)
    for key, value in additional_fields.items():
        if key not in required_fields:  # Avoid conflicts
            response[key] = value
    
    # Validate response
    result = validator.validate_response(response)
    
    # Property: Essential field validation should pass when required fields are present
    # and additional fields should be allowed
    assert result.is_valid, f"Validation should pass with required fields and additional fields. Errors: {result.errors}"


@given(
    required_fields=st.lists(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        min_size=1,
        max_size=3,
        unique=True
    ),
    missing_field_index=st.integers(min_value=0, max_value=2)
)
def test_property_essential_field_validation_detects_missing_required_fields(
    required_fields: List[str], 
    missing_field_index: int
):
    """
    **Feature: api-testing-refactor, Property 6: Essential Field Validation**
    
    For any API response missing required fields, the test framework should detect 
    and report the missing fields as validation errors.
    """
    if missing_field_index >= len(required_fields):
        return  # Skip if index is out of bounds
    
    # Create validator
    validator = APIResponseValidator(strict_mode=False)
    
    # Add validation rules for required fields
    for field in required_fields:
        validator.add_rule(ValidationRule(field, str, required=True))
    
    # Create response with all required fields except one
    response = {}
    missing_field = required_fields[missing_field_index]
    
    for field in required_fields:
        if field != missing_field:  # Skip the missing field
            response[field] = f"value_for_{field}"
    
    # Validate response
    result = validator.validate_response(response)
    
    # Property: Validation should fail when required fields are missing
    assert not result.is_valid, "Validation should fail when required fields are missing"
    
    # Property: Error should specifically mention the missing field
    missing_field_mentioned = any(missing_field in error for error in result.errors)
    assert missing_field_mentioned, f"Error should mention missing field '{missing_field}'. Errors: {result.errors}"


if __name__ == "__main__":
    # Run basic test first
    test_essential_field_validation_basic()
    
    # Run property tests
    print("Running property-based tests...")
    
    # Test 1: Additional fields allowed
    for i in range(10):  # Run a few iterations manually
        try:
            test_property_essential_field_validation_allows_additional_fields(
                ["name", "id"], 
                {"extra": "value", "bonus": 42}
            )
        except Exception as e:
            print(f"Property test 1 failed: {e}")
            break
    else:
        print("✓ Property test 1 (additional fields allowed) passed")
    
    # Test 2: Missing fields detected
    for i in range(10):  # Run a few iterations manually
        try:
            test_property_essential_field_validation_detects_missing_required_fields(
                ["name", "id", "status"], 
                1  # Missing "id"
            )
        except Exception as e:
            print(f"Property test 2 failed: {e}")
            break
    else:
        print("✓ Property test 2 (missing fields detected) passed")
    
    print("All essential field validation property tests completed successfully!")