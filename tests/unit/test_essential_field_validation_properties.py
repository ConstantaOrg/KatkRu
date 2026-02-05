"""
Property-based tests for essential field validation.

**Property 6: Essential Field Validation**
**Validates: Requirements 4.1, 4.3, 4.2**

These tests verify that the test framework validates required fields exist with correct types
while allowing additional non-breaking fields.
"""

import pytest
from hypothesis import given, strategies as st
from typing import Dict, Any, List, Type

from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, ValidationResult


class TestEssentialFieldValidationProperties:
    """Property-based tests for essential field validation functionality."""

    @given(
        required_fields=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=5,
            unique=True
        ),
        field_types=st.sampled_from([str, int, bool, list, dict]),
        additional_fields=st.dictionaries(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            st.one_of(st.text(), st.integers(), st.booleans(), st.lists(st.integers()), st.dictionaries(st.text(), st.text())),
            min_size=0,
            max_size=3
        )
    )
    def test_essential_field_validation_allows_additional_fields(
        self, 
        required_fields: List[str], 
        field_types: Type,
        additional_fields: Dict[str, Any]
    ):
        """
        **Feature: api-testing-refactor, Property 6: Essential Field Validation**
        
        For any API response, the test framework should verify that required fields exist 
        with correct types while allowing additional non-breaking fields.
        """
        # Create validator with non-strict mode (allows additional fields)
        validator = APIResponseValidator(strict_mode=False)
        
        # Add validation rules for required fields
        for field in required_fields:
            validator.add_rule(ValidationRule(field, field_types, required=True))
        
        # Create response with required fields and additional fields
        response = {}
        
        # Add required fields with correct types
        for field in required_fields:
            if field_types == str:
                response[field] = "test_value"
            elif field_types == int:
                response[field] = 42
            elif field_types == bool:
                response[field] = True
            elif field_types == list:
                response[field] = [1, 2, 3]
            elif field_types == dict:
                response[field] = {"key": "value"}
        
        # Add additional fields (should be allowed)
        for key, value in additional_fields.items():
            if key not in required_fields:  # Avoid conflicts
                response[key] = value
        
        # Validate response
        result = validator.validate_response(response)
        
        # Property: Essential field validation should pass when required fields are present
        # and additional fields should be allowed
        assert result.is_valid, f"Validation should pass with required fields and additional fields. Errors: {result.errors}"
        
        # Property: No errors should be reported for additional fields in non-strict mode
        additional_field_errors = [error for error in result.errors if "additional" in error.lower()]
        assert len(additional_field_errors) == 0, "No errors should be reported for additional fields in non-strict mode"

    @given(
        required_fields=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=5,
            unique=True
        ),
        field_types=st.sampled_from([str, int, bool, list, dict]),
        missing_field_index=st.integers(min_value=0, max_value=4)
    )
    def test_essential_field_validation_detects_missing_required_fields(
        self, 
        required_fields: List[str], 
        field_types: Type,
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
            validator.add_rule(ValidationRule(field, field_types, required=True))
        
        # Create response with all required fields except one
        response = {}
        missing_field = required_fields[missing_field_index]
        
        for field in required_fields:
            if field != missing_field:  # Skip the missing field
                if field_types == str:
                    response[field] = "test_value"
                elif field_types == int:
                    response[field] = 42
                elif field_types == bool:
                    response[field] = True
                elif field_types == list:
                    response[field] = [1, 2, 3]
                elif field_types == dict:
                    response[field] = {"key": "value"}
        
        # Validate response
        result = validator.validate_response(response)
        
        # Property: Validation should fail when required fields are missing
        assert not result.is_valid, "Validation should fail when required fields are missing"
        
        # Property: Error should specifically mention the missing field
        missing_field_mentioned = any(missing_field in error for error in result.errors)
        assert missing_field_mentioned, f"Error should mention missing field '{missing_field}'. Errors: {result.errors}"

    @given(
        required_fields=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=5,
            unique=True
        ),
        correct_type=st.sampled_from([str, int, bool, list, dict]),
        wrong_type=st.sampled_from([str, int, bool, list, dict]),
        field_index=st.integers(min_value=0, max_value=4)
    )
    def test_essential_field_validation_detects_wrong_types(
        self, 
        required_fields: List[str], 
        correct_type: Type,
        wrong_type: Type,
        field_index: int
    ):
        """
        **Feature: api-testing-refactor, Property 6: Essential Field Validation**
        
        For any API response with fields of incorrect types, the test framework should detect 
        and report type mismatches as validation errors.
        """
        # Skip if index is out of bounds or types are the same
        if field_index >= len(required_fields) or correct_type == wrong_type:
            return
        
        # Skip edge cases that might cause ambiguity in type checking
        # These are legitimate type relationships that shouldn't be tested as "wrong"
        if (correct_type == int and wrong_type == bool) or (correct_type == bool and wrong_type == int):
            # bool is a subclass of int in Python, but our validator should distinguish them
            pass  # Continue with the test - this is exactly what we want to test
        elif (correct_type == float and wrong_type in [int, bool]) or (wrong_type == float and correct_type in [int, bool]):
            # Skip float/int/bool combinations as they have complex relationships
            return
        
        # Create validator
        validator = APIResponseValidator(strict_mode=False)
        
        # Add validation rules for required fields
        for field in required_fields:
            validator.add_rule(ValidationRule(field, correct_type, required=True))
        
        # Create response with correct types for all fields except one
        response = {}
        wrong_type_field = required_fields[field_index]
        
        # Helper function to create values of specific types
        def create_value_of_type(value_type: Type, is_wrong_type: bool = False):
            if value_type == str:
                return "wrong_value" if is_wrong_type else "correct_value"
            elif value_type == int:
                return 999 if is_wrong_type else 42
            elif value_type == bool:
                return False if is_wrong_type else True
            elif value_type == list:
                return [9, 8, 7] if is_wrong_type else [1, 2, 3]
            elif value_type == dict:
                return {"wrong": "type"} if is_wrong_type else {"correct": "type"}
            else:
                raise ValueError(f"Unsupported type: {value_type}")
        
        for field in required_fields:
            if field == wrong_type_field:
                # Use wrong type for this field
                response[field] = create_value_of_type(wrong_type, is_wrong_type=True)
            else:
                # Use correct type for other fields
                response[field] = create_value_of_type(correct_type, is_wrong_type=False)
        
        # Validate response
        result = validator.validate_response(response)
        
        # Property: Validation should fail when field types are incorrect
        assert not result.is_valid, (
            f"Validation should fail when field types are incorrect. "
            f"Expected type: {correct_type.__name__}, Wrong type: {wrong_type.__name__}, "
            f"Field '{wrong_type_field}' value: {response[wrong_type_field]} (type: {type(response[wrong_type_field]).__name__}), "
            f"Validation errors: {result.errors}"
        )
        
        # Property: Error should specifically mention the type mismatch
        type_error_mentioned = any(
            wrong_type_field in error and "type" in error.lower() 
            for error in result.errors
        )
        assert type_error_mentioned, (
            f"Error should mention type mismatch for field '{wrong_type_field}'. "
            f"Expected: {correct_type.__name__}, Got: {wrong_type.__name__}, "
            f"Errors: {result.errors}"
        )

    @given(
        list_field_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        item_fields=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=3,
            unique=True
        ),
        item_count=st.integers(min_value=1, max_value=5),
        additional_item_fields=st.dictionaries(
            st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            st.one_of(st.text(), st.integers()),
            min_size=0,
            max_size=2
        )
    )
    def test_essential_field_validation_handles_list_structures_with_additional_fields(
        self, 
        list_field_name: str, 
        item_fields: List[str],
        item_count: int,
        additional_item_fields: Dict[str, Any]
    ):
        """
        **Feature: api-testing-refactor, Property 6: Essential Field Validation**
        
        For any API response containing lists, the test framework should validate essential 
        fields in list items while allowing additional fields in each item.
        """
        # Create validator
        validator = APIResponseValidator(strict_mode=False)
        
        # Create validation rules for list items
        item_rules = []
        for field in item_fields:
            item_rules.append(ValidationRule(field, str, required=True))
        
        # Create response with list containing items with required and additional fields
        list_items = []
        for i in range(item_count):
            item = {}
            
            # Add required fields
            for field in item_fields:
                item[field] = f"value_{field}_{i}"
            
            # Add additional fields (should be allowed)
            for key, value in additional_item_fields.items():
                if key not in item_fields:  # Avoid conflicts
                    item[key] = value
            
            list_items.append(item)
        
        response = {list_field_name: list_items}
        
        # Validate list structure
        result = validator.validate_list_structure(response, list_field_name, item_rules)
        
        # Property: List validation should pass when required fields are present in items
        # and additional fields should be allowed
        assert result.is_valid, f"List validation should pass with required fields and additional fields. Errors: {result.errors}"
        
        # Property: All items should be validated successfully
        item_specific_errors = [error for error in result.errors if "Item" in error]
        assert len(item_specific_errors) == 0, f"No item-specific errors should occur. Errors: {result.errors}"


if __name__ == "__main__":
    pytest.main([__file__])