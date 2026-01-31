"""
Standalone property-based tests for business logic independence.

**Property 7: Business Logic Independence**
**Validates: Requirements 7.4, 3.2**

These tests verify that the test framework validates the correctness of business logic
independent of documentation models.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Dict, Any, List, Callable

# Import the validator directly
from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, ValidationResult


def test_business_logic_independence_basic():
    """Basic test to verify business logic validation works independently of models."""
    validator = APIResponseValidator(strict_mode=False)
    
    # Define business rules that don't depend on model structure
    business_rules = [
        lambda data: data.get("status") == "active",
        lambda data: data.get("count", 0) >= 0,
        lambda data: len(data.get("items", [])) <= 100
    ]
    
    # Test with data that satisfies business rules but has extra fields (model-independent)
    response_valid = {
        "status": "active",
        "count": 5,
        "items": [1, 2, 3],
        "extra_field": "not_in_model",  # This would break model validation but shouldn't affect business logic
        "another_extra": 42
    }
    
    result_valid = validator.validate_business_logic(response_valid, business_rules)
    assert result_valid.is_valid, f"Business logic should pass when rules are satisfied: {result_valid.errors}"
    
    # Test with data that violates business rules
    response_invalid = {
        "status": "inactive",  # Violates first rule
        "count": 5,
        "items": [1, 2, 3],
        "model_field": "present"  # Model field present but business logic still fails
    }
    
    result_invalid = validator.validate_business_logic(response_invalid, business_rules)
    assert not result_invalid.is_valid, "Business logic should fail when rules are violated"
    
    # Test with different response structure but valid business logic
    response_different_structure = {
        "status": "active",
        "count": 10,
        "items": [],
        "completely_different_field": "value",
        "nested": {"data": "structure"}
    }
    
    result_different = validator.validate_business_logic(response_different_structure, business_rules)
    assert result_different.is_valid, "Business logic should work with different response structures"
    
    print("✓ Basic business logic independence test passed")


def test_business_logic_validation_across_response_formats():
    """Test that business logic validation works consistently across different response formats."""
    validator = APIResponseValidator(strict_mode=False)
    
    # Business rule: success field should be True
    success_rule = lambda resp: resp.get("success", False) is True
    
    # Different response formats that all satisfy the business rule
    response_formats = [
        {"success": True, "data": "some_data"},
        {"success": True, "result": {"items": [1, 2, 3]}, "meta": "info"},
        {"success": True, "message": "Operation completed", "code": 200},
        {"success": True}  # Minimal response
    ]
    
    for i, response in enumerate(response_formats):
        result = validator.validate_business_logic(response, [success_rule])
        assert result.is_valid, f"Business logic should pass for response format {i}: {response}"
    
    # Response that violates business rule regardless of format
    invalid_responses = [
        {"success": False, "data": "some_data"},
        {"success": False, "error": "Something went wrong"},
        {"result": "no_success_field"}  # Missing success field
    ]
    
    for i, response in enumerate(invalid_responses):
        result = validator.validate_business_logic(response, [success_rule])
        assert not result.is_valid, f"Business logic should fail for invalid response {i}: {response}"
    
    print("✓ Business logic validation across response formats test passed")


def test_business_logic_independent_of_model_changes():
    """Test that business logic validation works when models change but business logic stays the same."""
    validator = APIResponseValidator(strict_mode=False)
    
    # Business rule: value should be positive
    positive_value_rule = lambda data: data.get("value", 0) > 0
    
    # Simulate "old model" response structure
    old_model_response = {
        "value": 42,
        "old_field": "deprecated",
        "legacy_data": "still_here"
    }
    
    # Simulate "new model" response structure
    new_model_response = {
        "value": 42,
        "new_field": "added",
        "updated_structure": {"nested": "data"},
        "version": "2.0"
    }
    
    # Business logic should work the same for both
    old_result = validator.validate_business_logic(old_model_response, [positive_value_rule])
    new_result = validator.validate_business_logic(new_model_response, [positive_value_rule])
    
    assert old_result.is_valid, "Business logic should work with old model structure"
    assert new_result.is_valid, "Business logic should work with new model structure"
    
    # Both should have the same validation result since business logic is the same
    assert old_result.is_valid == new_result.is_valid, "Business logic results should be consistent across model changes"
    
    print("✓ Business logic independence from model changes test passed")


def test_business_logic_independent_of_model_validation():
    """Test that business logic validation is independent of model validation results."""
    validator = APIResponseValidator(strict_mode=False)
    
    # Business rule that checks actual business logic
    business_rule = lambda data: data.get("operation_successful", False) is True
    
    # Response that would fail model validation (missing expected fields) but passes business logic
    response_model_invalid_business_valid = {
        "operation_successful": True,  # Business logic satisfied
        "unexpected_field": "not_in_model",
        "wrong_format": 123  # Would fail model type checking
        # Missing expected model fields like "id", "name", etc.
    }
    
    # Validate business logic only
    business_result = validator.validate_business_logic(response_model_invalid_business_valid, [business_rule])
    
    # Business logic should pass even if model validation would fail
    assert business_result.is_valid, "Business logic should pass independent of model validation failures"
    
    # Response that would pass model validation but fail business logic
    response_model_valid_business_invalid = {
        "operation_successful": False,  # Business logic fails
        "id": 123,  # Model fields present
        "name": "test",
        "status": "active"
    }
    
    business_result_2 = validator.validate_business_logic(response_model_valid_business_invalid, [business_rule])
    
    # Business logic should fail even if model validation would pass
    assert not business_result_2.is_valid, "Business logic should fail independent of model validation success"
    
    print("✓ Business logic independence from model validation test passed")


if __name__ == "__main__":
    # Run all tests
    test_business_logic_independence_basic()
    test_business_logic_validation_across_response_formats()
    test_business_logic_independent_of_model_changes()
    test_business_logic_independent_of_model_validation()
    
    print("All business logic independence property tests completed successfully!")