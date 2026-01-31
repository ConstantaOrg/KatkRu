"""
Property-based tests for business logic independence.

**Property 7: Business Logic Independence**
**Validates: Requirements 7.4, 3.2**

These tests verify that the test framework validates the correctness of business logic
independent of documentation models.
"""

import pytest
from hypothesis import given, strategies as st
from typing import Dict, Any, List, Callable

from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, ValidationResult


class TestBusinessLogicIndependenceProperties:
    """Property-based tests for business logic independence functionality."""

    @given(
        business_rules=st.lists(
            st.sampled_from([
                lambda data: data.get("status") == "active",
                lambda data: data.get("count", 0) >= 0,
                lambda data: len(data.get("items", [])) <= 100,
                lambda data: data.get("timestamp") is not None,
                lambda data: isinstance(data.get("id"), (int, type(None)))
            ]),
            min_size=1,
            max_size=3
        ),
        response_data=st.fixed_dictionaries({}, optional={
            "status": st.sampled_from(["active", "inactive", "pending", "error"]),
            "count": st.integers(min_value=0, max_value=1000),
            "items": st.lists(st.integers(), max_size=100),
            "timestamp": st.one_of(st.none(), st.text(min_size=1, max_size=30)),
            "id": st.one_of(st.none(), st.integers(min_value=1, max_value=1000)),
            "extra_field": st.one_of(st.text(max_size=20), st.integers(), st.booleans())
        })
    )
    def test_business_logic_validation_independent_of_models(
        self, 
        business_rules: List[Callable[[Dict[str, Any]], bool]], 
        response_data: Dict[str, Any]
    ):
        """
        **Feature: api-testing-refactor, Property 7: Business Logic Independence**
        
        For any endpoint with business logic, the test framework should validate the correctness 
        of business logic independent of documentation models.
        """
        # Create validator that focuses on business logic, not model structure
        validator = APIResponseValidator(strict_mode=False)
        
        # Validate business logic directly using business rules
        result = validator.validate_business_logic(response_data, business_rules)
        
        # Property: Business logic validation should work regardless of response structure
        # The validation should depend only on the business rules, not on any predefined model
        
        # Check if all business rules pass for the given data
        expected_validity = all(rule(response_data) for rule in business_rules)
        
        # Property: Business logic validation result should match expected validity
        assert result.is_valid == expected_validity, (
            f"Business logic validation should match expected validity. "
            f"Expected: {expected_validity}, Got: {result.is_valid}, "
            f"Errors: {result.errors}, Data: {response_data}"
        )
        
        # Property: If validation fails, it should be due to business rule violations, not model issues
        if not result.is_valid:
            business_rule_errors = [error for error in result.errors if "Business rule" in error]
            assert len(business_rule_errors) > 0, "Failed validation should report business rule violations"

    @given(
        endpoint_responses=st.lists(
            st.dictionaries(
                st.sampled_from(["success", "data", "error", "message", "code"]),
                st.one_of(
                    st.booleans(),
                    st.text(max_size=50),
                    st.integers(min_value=100, max_value=599),
                    st.lists(st.dictionaries(st.text(max_size=10), st.text(max_size=20)), max_size=3)
                ),
                min_size=1,
                max_size=5
            ),
            min_size=1,
            max_size=5
        ),
        business_logic_function=st.sampled_from([
            lambda resp: resp.get("success", False) is True,
            lambda resp: resp.get("code", 500) < 400,
            lambda resp: len(resp.get("data", [])) > 0 if isinstance(resp.get("data"), list) else True,
            lambda resp: resp.get("error") is None or resp.get("error") == "",
        ])
    )
    def test_business_logic_validation_across_different_response_formats(
        self, 
        endpoint_responses: List[Dict[str, Any]], 
        business_logic_function: Callable[[Dict[str, Any]], bool]
    ):
        """
        **Feature: api-testing-refactor, Property 7: Business Logic Independence**
        
        For any set of endpoint responses with different formats, the test framework should 
        validate business logic consistently regardless of response structure variations.
        """
        validator = APIResponseValidator(strict_mode=False)
        
        # Property: Business logic validation should work consistently across different response formats
        for response in endpoint_responses:
            # Validate business logic for each response
            result = validator.validate_business_logic(response, [business_logic_function])
            
            # Check expected result based on business logic function
            expected_result = business_logic_function(response)
            
            # Property: Business logic validation should match expected result regardless of response format
            assert result.is_valid == expected_result, (
                f"Business logic validation should be consistent across response formats. "
                f"Response: {response}, Expected: {expected_result}, Got: {result.is_valid}"
            )

    @given(
        model_fields=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=4,
            unique=True
        ),
        actual_response_fields=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=6,
            unique=True
        ),
        business_value=st.integers(min_value=1, max_value=100)
    )
    def test_business_logic_validation_independent_of_model_changes(
        self, 
        model_fields: List[str], 
        actual_response_fields: List[str],
        business_value: int
    ):
        """
        **Feature: api-testing-refactor, Property 7: Business Logic Independence**
        
        For any endpoint, when response models change but business logic remains the same,
        the test framework should continue to validate business logic correctly.
        """
        # Create a business rule that depends on actual business logic, not model structure
        business_rule = lambda data: data.get("value", 0) == business_value
        
        # Create response with actual fields (may differ from model fields)
        actual_response = {}
        for field in actual_response_fields:
            if field == "value":
                actual_response[field] = business_value  # Satisfy business rule
            else:
                actual_response[field] = f"data_for_{field}"
        
        # Create validator that doesn't depend on model structure
        validator = APIResponseValidator(strict_mode=False)
        
        # Validate business logic
        result = validator.validate_business_logic(actual_response, [business_rule])
        
        # Property: Business logic validation should succeed when business rule is satisfied,
        # regardless of whether response fields match model fields
        if "value" in actual_response_fields:
            assert result.is_valid, (
                f"Business logic validation should pass when business rule is satisfied, "
                f"regardless of model field differences. Response: {actual_response}"
            )
        else:
            # If the required field for business logic is missing, validation should fail
            # but this is a business logic failure, not a model compliance failure
            assert not result.is_valid, "Business logic should fail when required data is missing"

    @given(
        endpoint_data=st.dictionaries(
            st.sampled_from(["user_id", "action", "timestamp", "result", "metadata"]),
            st.one_of(
                st.integers(min_value=1, max_value=1000),
                st.text(min_size=1, max_size=30),
                st.booleans()
            ),
            min_size=2,
            max_size=5
        ),
        model_validation_result=st.booleans(),
        business_logic_result=st.booleans()
    )
    def test_business_logic_validation_independent_of_model_validation_results(
        self, 
        endpoint_data: Dict[str, Any], 
        model_validation_result: bool,
        business_logic_result: bool
    ):
        """
        **Feature: api-testing-refactor, Property 7: Business Logic Independence**
        
        For any endpoint response, business logic validation results should be independent
        of model validation results - business logic can be correct even if model validation fails.
        """
        # Create a business rule that simulates the given business logic result
        business_rule = lambda data: business_logic_result  # Simulated business logic
        
        validator = APIResponseValidator(strict_mode=False)
        
        # Validate business logic independently
        business_result = validator.validate_business_logic(endpoint_data, [business_rule])
        
        # Property: Business logic validation result should match expected business logic result,
        # regardless of what model validation would return
        assert business_result.is_valid == business_logic_result, (
            f"Business logic validation should be independent of model validation. "
            f"Expected business result: {business_logic_result}, "
            f"Got: {business_result.is_valid}, "
            f"Model validation would be: {model_validation_result}"
        )
        
        # Property: Business logic validation should not be affected by model validation concerns
        # This test ensures that business logic validation works independently


if __name__ == "__main__":
    pytest.main([__file__])