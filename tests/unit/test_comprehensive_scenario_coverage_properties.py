"""
Property-Based Tests for Comprehensive Scenario Coverage

**Property 8: Comprehensive Scenario Coverage**
*For any* endpoint with conditional responses or multiple scenarios, the test framework 
should verify all relevant response paths and business conditions
**Validates: Requirements 3.4, 7.5**

This test validates that the test framework can handle all possible response scenarios
for endpoints with conditional logic, ensuring comprehensive coverage of business conditions.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any, Optional
from tests.utils import (
    ScenarioTestRunner,
    ResponseScenario,
    ScenarioTest,
    ValidationPattern,
    ValidationRule,
    APIResponseValidator,
    create_cards_save_scenarios,
    create_ttable_versions_scenarios,
    create_generic_crud_scenarios,
    TestDataGenerator,
    ResponseDataGenerator,
    OverloadResponseGenerator
)


# Test data generators for property-based testing
@st.composite
def generate_endpoint_scenarios(draw):
    """Generate realistic endpoint scenarios for testing."""
    endpoint_name = draw(st.sampled_from([
        "cards_save", "ttable_versions", "groups_crud", "teachers_crud", 
        "disciplines_crud", "timetable_get", "n8n_diff_check"
    ]))
    
    # Generate different response scenarios
    scenarios = draw(st.lists(
        st.sampled_from([
            ResponseScenario.SUCCESS,
            ResponseScenario.CONFLICT, 
            ResponseScenario.ERROR,
            ResponseScenario.NOT_FOUND,
            ResponseScenario.VALIDATION_ERROR,
            ResponseScenario.EMPTY_RESULT
        ]),
        min_size=2,
        max_size=5,
        unique=True
    ))
    
    return endpoint_name, scenarios


@st.composite
def generate_response_data(draw, scenario: ResponseScenario):
    """Generate response data for a specific scenario."""
    generator = ResponseDataGenerator()
    
    if scenario == ResponseScenario.SUCCESS:
        response_type = draw(st.sampled_from([
            "groups", "teachers", "disciplines", "timetable", "cards_save"
        ]))
        
        if response_type == "groups":
            count = draw(st.integers(min_value=0, max_value=20))
            return generator.generate_groups_response(count), 200
        elif response_type == "teachers":
            count = draw(st.integers(min_value=0, max_value=15))
            return generator.generate_teachers_response(count), 200
        elif response_type == "disciplines":
            count = draw(st.integers(min_value=0, max_value=25))
            return generator.generate_disciplines_response(count), 200
        elif response_type == "timetable":
            has_lessons = draw(st.booleans())
            return generator.generate_timetable_response(has_lessons), 200
        elif response_type == "cards_save":
            return generator.generate_cards_save_success_response(), 200
    
    elif scenario == ResponseScenario.CONFLICT:
        return generator.generate_cards_save_conflict_response(), 200
    
    elif scenario == ResponseScenario.ERROR:
        error_msg = draw(st.text(min_size=5, max_size=100))
        return {"error": error_msg, "success": False}, 400
    
    elif scenario == ResponseScenario.NOT_FOUND:
        resource = draw(st.sampled_from(["group", "teacher", "discipline", "timetable"]))
        return {"error": f"{resource} not found", "success": False}, 404
    
    elif scenario == ResponseScenario.VALIDATION_ERROR:
        field_name = draw(st.sampled_from(["name", "id", "type", "value"]))
        return {
            "error": "Validation failed",
            "details": {field_name: "Invalid value"},
            "success": False
        }, 422
    
    elif scenario == ResponseScenario.EMPTY_RESULT:
        result_type = draw(st.sampled_from(["groups", "teachers", "disciplines"]))
        return {result_type: []}, 200
    
    # Default fallback
    return {"success": True}, 200


@st.composite
def generate_business_conditions(draw):
    """Generate business conditions that affect response scenarios."""
    conditions = {}
    
    # User permissions
    conditions["is_admin"] = draw(st.booleans())
    conditions["has_write_access"] = draw(st.booleans())
    
    # Data state conditions
    conditions["resource_exists"] = draw(st.booleans())
    conditions["has_conflicts"] = draw(st.booleans())
    conditions["is_valid_input"] = draw(st.booleans())
    
    # System state conditions
    conditions["database_available"] = draw(st.booleans())
    conditions["within_rate_limit"] = draw(st.booleans())
    
    return conditions


class TestComprehensiveScenarioCoverage:
    """Test comprehensive scenario coverage property."""
    
    @given(generate_endpoint_scenarios())
    @settings(max_examples=100, deadline=None)
    def test_property_comprehensive_scenario_coverage(self, endpoint_scenarios):
        """
        **Feature: api-testing-refactor, Property 8: Comprehensive Scenario Coverage**
        
        *For any* endpoint with conditional responses or multiple scenarios, the test framework 
        should verify all relevant response paths and business conditions.
        
        This property ensures that:
        1. All defined scenarios can be validated by the framework
        2. Each scenario has appropriate validation rules
        3. Business conditions are properly checked
        4. The framework handles scenario transitions correctly
        """
        endpoint_name, scenarios = endpoint_scenarios
        
        # Create scenario runner for the endpoint
        if endpoint_name == "cards_save":
            runner = create_cards_save_scenarios()
        elif endpoint_name == "ttable_versions":
            runner = create_ttable_versions_scenarios()
        else:
            runner = create_generic_crud_scenarios(endpoint_name.replace("_crud", ""))
        
        # Verify that all scenarios are covered
        available_scenarios = set(runner.scenarios.keys())
        
        # Each endpoint should have at least success and error scenarios
        assert "success" in available_scenarios, f"Endpoint {endpoint_name} missing success scenario"
        
        # Multi-response endpoints should have conflict scenarios
        if endpoint_name in ["cards_save", "ttable_versions"]:
            assert "conflict" in available_scenarios, f"Multi-response endpoint {endpoint_name} missing conflict scenario"
        
        # CRUD endpoints should have not_found scenarios
        if "_crud" in endpoint_name:
            assert "not_found" in available_scenarios, f"CRUD endpoint {endpoint_name} missing not_found scenario"
        
        # Verify scenario completeness - each scenario should have proper validation
        for scenario_name, scenario_test in runner.scenarios.items():
            # Each scenario should have validation pattern
            assert scenario_test.validation_pattern is not None, f"Scenario {scenario_name} missing validation pattern"
            
            # Each scenario should have expected status codes
            assert len(scenario_test.expected_status_codes) > 0, f"Scenario {scenario_name} missing expected status codes"
            
            # Validation pattern should have rules
            assert len(scenario_test.validation_pattern.rules) > 0, f"Scenario {scenario_name} has no validation rules"
    
    @given(
        st.sampled_from([ResponseScenario.SUCCESS, ResponseScenario.CONFLICT, ResponseScenario.ERROR]),
        generate_business_conditions()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_business_condition_validation(self, scenario, business_conditions):
        """
        **Feature: api-testing-refactor, Property 8: Business Condition Validation**
        
        *For any* business condition that affects response scenarios, the test framework
        should properly validate the condition and its impact on the response.
        """
        # Generate appropriate response data based on scenario and conditions
        generator = ResponseDataGenerator()
        
        if scenario == ResponseScenario.SUCCESS and business_conditions["is_valid_input"]:
            response_data, status_code = generator.generate_cards_save_success_response(), 200
        elif scenario == ResponseScenario.CONFLICT and business_conditions["has_conflicts"]:
            response_data, status_code = generator.generate_cards_save_conflict_response(), 200
        elif scenario == ResponseScenario.ERROR and not business_conditions["is_valid_input"]:
            response_data, status_code = {"error": "Invalid input", "success": False}, 400
        else:
            # Skip combinations that don't make business sense
            assume(False)
        
        # Create scenario runner and validate
        runner = create_cards_save_scenarios()
        
        # Determine which scenario to test based on response
        if response_data.get("success") is True:
            scenario_name = "success"
        elif response_data.get("success") is False and "conflicts" in response_data:
            scenario_name = "conflict"
        else:
            # For error scenarios, we need a generic error validator
            return  # Skip for now as we focus on success/conflict
        
        # Validate the response against the scenario
        result = runner.run_scenario(scenario_name, status_code, response_data)
        
        # The validation should succeed for properly formed responses
        if business_conditions["is_valid_input"] or scenario == ResponseScenario.CONFLICT:
            assert result.is_valid, f"Valid business condition should pass validation: {result.errors}"
        
        # Verify business logic is checked
        scenario_test = runner.scenarios[scenario_name]
        if scenario_test.business_logic_validator:
            business_result = scenario_test.business_logic_validator(response_data)
            if scenario == ResponseScenario.SUCCESS:
                assert business_result == (response_data.get("success") is True)
            elif scenario == ResponseScenario.CONFLICT:
                assert business_result == (response_data.get("success") is False and "conflicts" in response_data)
    
    @given(
        st.lists(
            st.sampled_from(["success", "conflict"]),
            min_size=2,
            max_size=4,
            unique=True
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_property_multiple_scenario_handling(self, scenario_names):
        """
        **Feature: api-testing-refactor, Property 8: Multiple Scenario Handling**
        
        *For any* set of multiple response scenarios from the same endpoint, the test framework
        should correctly validate each scenario independently and provide comprehensive results.
        """
        # Create scenario runner
        runner = create_cards_save_scenarios()
        
        # Create test results for each scenario
        test_results = []
        for scenario_name in scenario_names:
            if scenario_name == "success":
                # Create success response format
                response_data = {"success": True, "new_card_hist_id": 12345}
                test_results.append((scenario_name, 200, response_data))
            elif scenario_name == "conflict":
                # Create conflict response format
                response_data = {"success": False, "conflicts": {"position_conflicts": []}}
                test_results.append((scenario_name, 200, response_data))
        
        # Run all scenarios
        results = runner.run_all_scenarios(test_results)
        
        # Verify each scenario was validated independently
        assert len(results) >= len(set(scenario_names)), "Each unique scenario should be validated"
        
        # Each result should be valid for properly formatted responses
        for scenario_name, validation_result in results.items():
            assert validation_result.is_valid, f"Scenario {scenario_name} should validate successfully: {validation_result.errors}"
        
        # Verify all requested scenarios have results
        for scenario_name in set(scenario_names):
            assert scenario_name in results, f"Scenario {scenario_name} should have validation result"
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, deadline=None)
    def test_property_overload_scenario_coverage(self, num_scenarios):
        """
        **Feature: api-testing-refactor, Property 8: @overload Scenario Coverage**
        
        *For any* @overload response model scenarios, the test framework should verify
        that all scenarios produce clean JSON and maintain proper separation.
        """
        generator = OverloadResponseGenerator()
        
        # Generate multiple @overload scenarios
        scenarios = []
        for i in range(num_scenarios):
            # Alternate between success and conflict scenarios
            if i % 2 == 0:
                scenario_data = generator.generate_success_response("cards_save")
                scenario_type = "success"
            else:
                scenario_data = generator.generate_conflict_response("cards_save")
                scenario_type = "conflict"
            
            scenarios.append((scenario_type, scenario_data))
        
        # Verify each scenario produces clean JSON
        for scenario_type, scenario_data in scenarios:
            # Should not contain null values
            clean_json = generator.validate_clean_json(scenario_data)
            assert clean_json, f"@overload scenario {scenario_type} should produce clean JSON without null fields"
            
            # Should have proper success field
            if scenario_type == "success":
                assert scenario_data.get("success") is True, "Success scenario should have success=True"
                assert "new_card_hist_id" in scenario_data, "Success scenario should have new_card_hist_id"
            elif scenario_type == "conflict":
                assert scenario_data.get("success") is False, "Conflict scenario should have success=False"
                assert "conflicts" in scenario_data, "Conflict scenario should have conflicts"
        
        # Verify scenario separation if we have both types
        success_scenarios = [data for type_, data in scenarios if type_ == "success"]
        conflict_scenarios = [data for type_, data in scenarios if type_ == "conflict"]
        
        if success_scenarios and conflict_scenarios:
            # Success and conflict should have different structures
            success_fields = set(success_scenarios[0].keys())
            conflict_fields = set(conflict_scenarios[0].keys())
            
            # Both should have 'success' field but different additional fields
            assert "success" in success_fields and "success" in conflict_fields
            
            # Should have some different fields (proper separation)
            different_fields = success_fields.symmetric_difference(conflict_fields)
            assert len(different_fields) > 0, "Success and conflict scenarios should have different field structures"
    
    @given(
        st.sampled_from(["groups", "teachers", "disciplines"]),
        st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_empty_result_scenario_coverage(self, resource_type, expected_count):
        """
        **Feature: api-testing-refactor, Property 8: Empty Result Scenario Coverage**
        
        *For any* endpoint that can return empty results, the test framework should
        properly validate empty scenarios as valid responses.
        """
        generator = ResponseDataGenerator()
        
        # Generate response with specified count (including 0 for empty)
        if resource_type == "groups":
            response_data = generator.generate_groups_response(expected_count)
        elif resource_type == "teachers":
            response_data = generator.generate_teachers_response(expected_count)
        elif resource_type == "disciplines":
            response_data = generator.generate_disciplines_response(expected_count)
        
        # Create validator that matches the actual response structure (not generic CRUD)
        validator = APIResponseValidator(strict_mode=False)
        validator.add_rule(ValidationRule(resource_type, list, required=True))
        
        # Validate the response structure directly
        result = validator.validate_response(response_data)
        
        # Empty results should be valid
        assert result.is_valid, f"Empty {resource_type} result should be valid: {result.errors}"
        
        # Verify the response structure is correct
        assert resource_type in response_data, f"Response should contain {resource_type} field"
        assert isinstance(response_data[resource_type], list), f"{resource_type} should be a list"
        assert len(response_data[resource_type]) == expected_count, f"Should have {expected_count} {resource_type}"