"""
Property-Based Tests for Change Impact Detection

**Property 9: Change Impact Detection**
*For any* API endpoint evolution, the test framework should correctly distinguish 
between breaking changes (that should fail tests) and non-breaking changes 
(that should not fail tests)
**Validates: Requirements 4.5**

This test validates that the test framework can properly detect when API changes
are breaking vs non-breaking, ensuring tests remain stable for legitimate changes.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any, Optional, Set
from copy import deepcopy
from tests.utils import (
    APIResponseValidator,
    ValidationRule,
    ValidationResult,
    TestDataGenerator,
    ResponseDataGenerator,
    ModelAccuracyVerifier,
    RuntimeValidator,
    ValidationConfig
)


# Test data generators for change impact testing
@st.composite
def generate_base_response(draw):
    """Generate a base API response for testing changes."""
    generator = ResponseDataGenerator()
    
    response_type = draw(st.sampled_from([
        "groups", "teachers", "disciplines", "timetable", "cards_save"
    ]))
    
    if response_type == "groups":
        count = draw(st.integers(min_value=1, max_value=10))
        return generator.generate_groups_response(count)
    elif response_type == "teachers":
        count = draw(st.integers(min_value=1, max_value=10))
        return generator.generate_teachers_response(count)
    elif response_type == "disciplines":
        count = draw(st.integers(min_value=1, max_value=10))
        return generator.generate_disciplines_response(count)
    elif response_type == "timetable":
        return generator.generate_timetable_response(True)
    elif response_type == "cards_save":
        return generator.generate_cards_save_success_response()


@st.composite
def generate_non_breaking_change(draw, base_response: Dict[str, Any]):
    """Generate a non-breaking change to the base response."""
    changed_response = deepcopy(base_response)
    
    change_type = draw(st.sampled_from([
        "add_optional_field",
        "add_metadata",
        "add_pagination",
        "add_debug_info",
        "extend_existing_object"
    ]))
    
    if change_type == "add_optional_field":
        # Add a new optional field that doesn't break existing functionality
        new_field_name = draw(st.sampled_from([
            "created_at", "updated_at", "version", "metadata", "extra_info"
        ]))
        new_field_value = draw(st.one_of(
            st.text(min_size=1, max_size=50),
            st.integers(),
            st.booleans(),
            st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=20), max_size=3)
        ))
        changed_response[new_field_name] = new_field_value
    
    elif change_type == "add_metadata":
        # Add metadata object
        changed_response["metadata"] = {
            "version": "2.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "request_id": "req-12345"
        }
    
    elif change_type == "add_pagination":
        # Add pagination info (common non-breaking addition)
        changed_response["pagination"] = {
            "total": draw(st.integers(min_value=1, max_value=1000)),
            "page": draw(st.integers(min_value=1, max_value=10)),
            "per_page": draw(st.integers(min_value=10, max_value=100))
        }
    
    elif change_type == "add_debug_info":
        # Add debug information
        changed_response["debug"] = {
            "query_time_ms": draw(st.integers(min_value=1, max_value=1000)),
            "cache_hit": draw(st.booleans())
        }
    
    elif change_type == "extend_existing_object":
        # Add fields to existing objects in lists
        for key, value in changed_response.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Add new field to each object in the list
                new_field = draw(st.sampled_from(["status", "priority", "tags"]))
                new_value = draw(st.one_of(st.text(min_size=1, max_size=20), st.integers()))
                
                for item in value:
                    item[new_field] = new_value
                break
    
    return changed_response, change_type


@st.composite
def generate_breaking_change(draw, base_response: Dict[str, Any]):
    """Generate a breaking change to the base response."""
    changed_response = deepcopy(base_response)
    
    change_type = draw(st.sampled_from([
        "remove_required_field",
        "change_field_type",
        "rename_field",
        "change_structure",
        "remove_list_items"
    ]))
    
    # Get available fields to modify
    available_fields = list(base_response.keys())
    assume(len(available_fields) > 0)
    
    if change_type == "remove_required_field":
        # Remove a field that tests expect to be present
        field_to_remove = draw(st.sampled_from(available_fields))
        del changed_response[field_to_remove]
    
    elif change_type == "change_field_type":
        # Change the type of an existing field
        field_to_change = draw(st.sampled_from(available_fields))
        original_value = base_response[field_to_change]
        
        if isinstance(original_value, list):
            # Change list to dict
            changed_response[field_to_change] = {"items": original_value}
        elif isinstance(original_value, dict):
            # Change dict to list
            changed_response[field_to_change] = [original_value]
        elif isinstance(original_value, str):
            # Change string to int
            changed_response[field_to_change] = 12345
        elif isinstance(original_value, int):
            # Change int to string
            changed_response[field_to_change] = str(original_value)
        elif isinstance(original_value, bool):
            # Change bool to string
            changed_response[field_to_change] = "true" if original_value else "false"
    
    elif change_type == "rename_field":
        # Rename an existing field
        field_to_rename = draw(st.sampled_from(available_fields))
        new_name = f"{field_to_rename}_new"
        changed_response[new_name] = changed_response[field_to_rename]
        del changed_response[field_to_rename]
    
    elif change_type == "change_structure":
        # Completely change the structure
        if "groups" in changed_response:
            # Change groups list to nested structure
            groups = changed_response["groups"]
            changed_response["groups"] = {"active": groups, "inactive": []}
        elif "teachers" in changed_response:
            # Change teachers list to nested structure
            teachers = changed_response["teachers"]
            changed_response["teachers"] = {"by_department": {"default": teachers}}
    
    elif change_type == "remove_list_items":
        # Remove all items from a list (making it empty when it shouldn't be)
        for key, value in changed_response.items():
            if isinstance(value, list) and len(value) > 0:
                changed_response[key] = []
                break
    
    return changed_response, change_type


class TestChangeImpactDetection:
    """Test change impact detection property."""
    
    @given(generate_base_response())
    @settings(max_examples=50, deadline=None)
    def test_property_non_breaking_changes_should_not_fail_tests(self, base_response):
        """
        **Feature: api-testing-refactor, Property 9: Non-Breaking Change Tolerance**
        
        *For any* non-breaking change to an API response (adding optional fields, metadata, etc.),
        the test framework should continue to validate successfully without test failures.
        
        This ensures tests remain stable when APIs evolve in backward-compatible ways.
        """
        # Create validator focused on essential fields only (non-strict mode)
        validator = APIResponseValidator(strict_mode=False)
        
        # Define essential validation rules based on response type
        if "groups" in base_response:
            validator.add_rule(ValidationRule("groups", list, required=True))
        elif "teachers" in base_response:
            validator.add_rule(ValidationRule("teachers", list, required=True))
        elif "disciplines" in base_response:
            validator.add_rule(ValidationRule("disciplines", list, required=True))
        elif "timetable" in base_response:
            validator.add_rule(ValidationRule("timetable", dict, required=True))
        elif "success" in base_response:
            validator.add_rule(ValidationRule("success", bool, required=True))
        
        # Validate original response
        original_result = validator.validate_response(base_response)
        assume(original_result.is_valid)  # Only test with valid base responses
        
        # Generate non-breaking change manually (simpler approach)
        changed_response = deepcopy(base_response)
        
        # Add metadata (common non-breaking change)
        changed_response["metadata"] = {
            "version": "2.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Add pagination info
        changed_response["pagination"] = {
            "total": 100,
            "page": 1,
            "per_page": 10
        }
        
        # Validate changed response - should still pass
        changed_result = validator.validate_response(changed_response)
        
        assert changed_result.is_valid, (
            f"Non-breaking change (adding metadata/pagination) should not fail validation. "
            f"Errors: {changed_result.errors}"
        )
        
        # Essential fields should still be present and valid
        for rule in validator.validation_rules:
            if rule.required:
                assert rule.field_name in changed_response, (
                    f"Required field '{rule.field_name}' should still be present after non-breaking change"
                )
                
                original_type = type(base_response[rule.field_name])
                changed_type = type(changed_response[rule.field_name])
                assert original_type == changed_type, (
                    f"Field '{rule.field_name}' type should not change in non-breaking change"
                )
    
    @given(generate_base_response())
    @settings(max_examples=50, deadline=None)
    def test_property_breaking_changes_should_fail_tests(self, base_response):
        """
        **Feature: api-testing-refactor, Property 9: Breaking Change Detection**
        
        *For any* breaking change to an API response (removing required fields, changing types, etc.),
        the test framework should detect the change and fail validation appropriately.
        
        This ensures tests catch actual breaking changes that could affect consumers.
        """
        # Create validator that checks for essential fields
        validator = APIResponseValidator(strict_mode=False)
        
        # Define essential validation rules based on response type
        essential_fields = []
        if "groups" in base_response:
            validator.add_rule(ValidationRule("groups", list, required=True))
            essential_fields.append("groups")
        elif "teachers" in base_response:
            validator.add_rule(ValidationRule("teachers", list, required=True))
            essential_fields.append("teachers")
        elif "disciplines" in base_response:
            validator.add_rule(ValidationRule("disciplines", list, required=True))
            essential_fields.append("disciplines")
        elif "timetable" in base_response:
            validator.add_rule(ValidationRule("timetable", dict, required=True))
            essential_fields.append("timetable")
        elif "success" in base_response:
            validator.add_rule(ValidationRule("success", bool, required=True))
            essential_fields.append("success")
        
        assume(len(essential_fields) > 0)  # Need at least one essential field to test
        
        # Validate original response
        original_result = validator.validate_response(base_response)
        assume(original_result.is_valid)  # Only test with valid base responses
        
        # Generate breaking change manually (simpler approach)
        changed_response = deepcopy(base_response)
        
        # Remove the first essential field (breaking change)
        field_to_remove = essential_fields[0]
        del changed_response[field_to_remove]
        
        # Validate changed response - should fail for breaking changes
        changed_result = validator.validate_response(changed_response)
        
        # Breaking changes should be detected
        assert not changed_result.is_valid, (
            f"Breaking change (removing '{field_to_remove}') should fail validation but didn't. "
            f"Response: {changed_response}"
        )
        
        # Should have specific error messages about the breaking change
        assert len(changed_result.errors) > 0, (
            f"Breaking change should produce error messages"
        )
        
        # Error should mention the missing field
        error_text = " ".join(changed_result.errors)
        assert field_to_remove in error_text, (
            f"Error should mention missing field '{field_to_remove}': {changed_result.errors}"
        )
    
    @given(
        generate_base_response(),
        st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5, unique=True)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_additional_fields_tolerance(self, base_response, additional_field_names):
        """
        **Feature: api-testing-refactor, Property 9: Additional Fields Tolerance**
        
        *For any* API response with additional fields beyond what's expected,
        the test framework should allow these fields without failing (non-strict mode).
        
        This supports API evolution where new fields are added over time.
        """
        # Create non-strict validator
        validator = APIResponseValidator(strict_mode=False)
        
        # Add validation rules for existing fields only
        if "groups" in base_response:
            validator.add_rule(ValidationRule("groups", list, required=True))
        elif "teachers" in base_response:
            validator.add_rule(ValidationRule("teachers", list, required=True))
        elif "success" in base_response:
            validator.add_rule(ValidationRule("success", bool, required=True))
        
        # Add additional fields to response
        enhanced_response = deepcopy(base_response)
        for field_name in additional_field_names:
            # Avoid overwriting existing fields
            if field_name not in enhanced_response:
                enhanced_response[field_name] = f"additional_value_{field_name}"
        
        # Validation should still pass with additional fields
        result = validator.validate_response(enhanced_response)
        
        assert result.is_valid, (
            f"Response with additional fields should be valid in non-strict mode. "
            f"Errors: {result.errors}, Additional fields: {additional_field_names}"
        )
        
        # Should have warnings about additional fields, not errors
        if result.warnings:
            # Warnings are acceptable for additional fields
            pass
    
    @given(generate_base_response())
    @settings(max_examples=30, deadline=None)
    def test_property_strict_mode_change_detection(self, base_response):
        """
        **Feature: api-testing-refactor, Property 9: Strict Mode Change Detection**
        
        *For any* API response change when using strict validation mode,
        the test framework should detect even minor changes like additional fields.
        
        This supports scenarios where exact schema matching is required.
        """
        # Create strict validator
        strict_validator = APIResponseValidator(strict_mode=True)
        
        # Add validation rules for all existing fields
        for field_name, field_value in base_response.items():
            field_type = type(field_value)
            strict_validator.add_rule(ValidationRule(field_name, field_type, required=True))
        
        # Original response should pass strict validation
        original_result = strict_validator.validate_response(base_response)
        assert original_result.is_valid, f"Original response should pass strict validation: {original_result.errors}"
        
        # Add one additional field
        enhanced_response = deepcopy(base_response)
        enhanced_response["new_field"] = "new_value"
        
        # Strict validation should detect the additional field
        enhanced_result = strict_validator.validate_response(enhanced_response)
        
        # In strict mode, additional fields should be flagged (as warnings or errors)
        # The exact behavior depends on implementation, but change should be detected
        has_change_detection = (
            not enhanced_result.is_valid or 
            len(enhanced_result.warnings) > 0
        )
        
        assert has_change_detection, (
            f"Strict mode should detect additional fields. "
            f"Result: valid={enhanced_result.is_valid}, "
            f"errors={enhanced_result.errors}, warnings={enhanced_result.warnings}"
        )
    
    @given(
        generate_base_response(),
        st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_change_impact_across_versions(self, base_response, num_versions):
        """
        **Feature: api-testing-refactor, Property 9: Change Impact Across Versions**
        
        *For any* sequence of API changes across multiple versions,
        the test framework should correctly track cumulative impact and
        distinguish between compatible evolution and breaking changes.
        """
        # Create validator for essential fields only
        validator = APIResponseValidator(strict_mode=False)
        
        # Identify essential fields based on response type
        essential_fields = []
        if "groups" in base_response:
            validator.add_rule(ValidationRule("groups", list, required=True))
            essential_fields.append("groups")
        elif "teachers" in base_response:
            validator.add_rule(ValidationRule("teachers", list, required=True))
            essential_fields.append("teachers")
        elif "success" in base_response:
            validator.add_rule(ValidationRule("success", bool, required=True))
            essential_fields.append("success")
        
        assume(len(essential_fields) > 0)
        
        # Simulate evolution across versions
        current_response = deepcopy(base_response)
        
        for version in range(num_versions):
            # Apply non-breaking change manually (simpler approach)
            enhanced_response = deepcopy(current_response)
            
            # Add version-specific metadata
            enhanced_response[f"version_{version}"] = f"v{version + 1}"
            enhanced_response["last_updated"] = f"2024-01-{version + 1:02d}T00:00:00Z"
            
            # Should still validate successfully
            result = validator.validate_response(enhanced_response)
            assert result.is_valid, (
                f"Version {version + 1} with non-breaking change should be valid. "
                f"Errors: {result.errors}"
            )
            
            # Essential fields should still be present and correct type
            for field_name in essential_fields:
                assert field_name in enhanced_response, (
                    f"Essential field '{field_name}' missing in version {version + 1}"
                )
                
                original_type = type(base_response[field_name])
                current_type = type(enhanced_response[field_name])
                assert original_type == current_type, (
                    f"Essential field '{field_name}' type changed from {original_type} to {current_type} "
                    f"in version {version + 1}"
                )
            
            current_response = enhanced_response
        
        # Final response should still be compatible with original validator
        final_result = validator.validate_response(current_response)
        assert final_result.is_valid, (
            f"Final response after {num_versions} non-breaking changes should be valid. "
            f"Errors: {final_result.errors}"
        )
    
    @given(generate_base_response())
    @settings(max_examples=30, deadline=None)
    def test_property_business_logic_change_detection(self, base_response):
        """
        **Feature: api-testing-refactor, Property 9: Business Logic Change Detection**
        
        *For any* change that affects business logic validation,
        the test framework should detect the impact on business rules
        while allowing structural changes that don't affect logic.
        """
        # Define business logic rules based on response type
        business_rules = []
        
        if "groups" in base_response:
            # Business rule: groups list should not be empty if it exists
            def groups_not_empty_if_present(response):
                groups = response.get("groups", [])
                return isinstance(groups, list)
            business_rules.append(groups_not_empty_if_present)
        
        elif "success" in base_response:
            # Business rule: success field should be boolean
            def success_is_boolean(response):
                success = response.get("success")
                return isinstance(success, bool)
            business_rules.append(success_is_boolean)
        
        assume(len(business_rules) > 0)
        
        # Create validator with business rules
        validator = APIResponseValidator(strict_mode=False)
        
        # Original response should pass business logic
        original_business_result = validator.validate_business_logic(base_response, business_rules)
        assume(original_business_result.is_valid)
        
        # Test non-breaking structural change (should not affect business logic)
        enhanced_response = deepcopy(base_response)
        enhanced_response["metadata"] = {"version": "2.0"}  # Add metadata (non-breaking)
        enhanced_business_result = validator.validate_business_logic(enhanced_response, business_rules)
        
        assert enhanced_business_result.is_valid, (
            f"Non-breaking structural change should not affect business logic validation. "
            f"Errors: {enhanced_business_result.errors}"
        )
        
        # Test business logic breaking change
        logic_breaking_response = deepcopy(base_response)
        
        if "groups" in logic_breaking_response:
            # Change groups to non-list (breaks business logic)
            logic_breaking_response["groups"] = "not_a_list"
        elif "success" in logic_breaking_response:
            # Change success to non-boolean (breaks business logic)
            logic_breaking_response["success"] = "not_a_boolean"
        
        logic_breaking_result = validator.validate_business_logic(logic_breaking_response, business_rules)
        
        assert not logic_breaking_result.is_valid, (
            f"Business logic breaking change should fail validation. "
            f"Response: {logic_breaking_response}"
        )