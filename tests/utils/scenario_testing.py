"""
Scenario Testing Utilities for Multi-Response Endpoints

This module provides utilities for testing endpoints that can return different
response formats based on business logic, status codes, or @overload patterns.
"""

from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, ValidationResult
from tests.utils.validation_patterns import ValidationPattern, MultiResponseValidator
from tests.utils.test_data_generators import OverloadResponseGenerator


class ResponseScenario(Enum):
    """Enumeration of common response scenarios."""
    SUCCESS = "success"
    CONFLICT = "conflict"
    ERROR = "error"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    EMPTY_RESULT = "empty_result"


@dataclass
class ScenarioTest:
    """Represents a test scenario for an endpoint."""
    name: str
    description: str
    scenario: ResponseScenario
    expected_status_codes: List[int]
    validation_pattern: ValidationPattern
    test_data_generator: Optional[Callable[[], Dict[str, Any]]] = None
    business_logic_validator: Optional[Callable[[Dict[str, Any]], bool]] = None


class ScenarioTestRunner:
    """
    Runs multiple test scenarios for endpoints with different response patterns.
    """
    
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.scenarios: Dict[str, ScenarioTest] = {}
    
    def add_scenario(self, scenario: ScenarioTest) -> None:
        """Add a test scenario."""
        self.scenarios[scenario.name] = scenario
    
    def run_scenario(self, scenario_name: str, actual_status: int, 
                    actual_response: Dict[str, Any]) -> ValidationResult:
        """
        Run a specific scenario test.
        
        Args:
            scenario_name: Name of the scenario to test
            actual_status: Actual HTTP status code
            actual_response: Actual response data
            
        Returns:
            ValidationResult with test results
        """
        if scenario_name not in self.scenarios:
            return ValidationResult(
                is_valid=False,
                errors=[f"Scenario '{scenario_name}' not found"],
                warnings=[]
            )
        
        scenario = self.scenarios[scenario_name]
        errors = []
        warnings = []
        
        # Validate status code
        if actual_status not in scenario.expected_status_codes:
            errors.append(
                f"Status code {actual_status} not in expected codes "
                f"{scenario.expected_status_codes} for scenario '{scenario_name}'"
            )
        
        # Validate response structure using pattern
        validator = scenario.validation_pattern.create_validator(strict_mode=False)
        structure_result = validator.validate_response(actual_response)
        errors.extend(structure_result.errors)
        warnings.extend(structure_result.warnings)
        
        # Validate business logic
        if scenario.validation_pattern.business_rules:
            business_result = validator.validate_business_logic(
                actual_response, scenario.validation_pattern.business_rules
            )
            errors.extend(business_result.errors)
            warnings.extend(business_result.warnings)
        
        # Additional business logic validation
        if scenario.business_logic_validator:
            try:
                if not scenario.business_logic_validator(actual_response):
                    errors.append(f"Custom business logic validation failed for scenario '{scenario_name}'")
            except Exception as e:
                errors.append(f"Business logic validator error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def run_all_scenarios(self, test_results: List[Tuple[str, int, Dict[str, Any]]]) -> Dict[str, ValidationResult]:
        """
        Run all scenarios against provided test results.
        
        Args:
            test_results: List of (scenario_name, status_code, response_data) tuples
            
        Returns:
            Dictionary mapping scenario names to validation results
        """
        results = {}
        
        for scenario_name, status_code, response_data in test_results:
            results[scenario_name] = self.run_scenario(scenario_name, status_code, response_data)
        
        return results


class OverloadScenarioTester:
    """
    Specialized tester for @overload response model scenarios.
    
    This tester validates that @overload responses produce clean JSON
    without null field pollution and maintain proper type safety.
    """
    
    def __init__(self):
        self.generator = OverloadResponseGenerator()
    
    def test_clean_json_output(self, response: Dict[str, Any]) -> ValidationResult:
        """
        Test that response produces clean JSON without null fields.
        
        This validates the core benefit of @overload response models:
        no null field pollution in the JSON output.
        """
        errors = []
        warnings = []
        
        # Check for null values
        if not self.generator.validate_clean_json(response):
            errors.append("Response contains null fields (violates @overload clean JSON principle)")
        
        # Validate JSON serializability
        try:
            json.dumps(response)
        except (TypeError, ValueError) as e:
            errors.append(f"Response is not JSON serializable: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def test_type_safety(self, response: Dict[str, Any], expected_schema: Dict[str, type]) -> ValidationResult:
        """
        Test that @overload response maintains type safety.
        
        Args:
            response: Actual response data
            expected_schema: Expected field types
        """
        validator = APIResponseValidator(strict_mode=False)
        return validator.validate_field_types(response, expected_schema)
    
    def test_scenario_completeness(self, success_response: Dict[str, Any], 
                                 conflict_response: Dict[str, Any]) -> ValidationResult:
        """
        Test that @overload scenarios are complete and non-overlapping.
        
        Success and conflict responses should have different structures
        and both should be clean.
        """
        errors = []
        warnings = []
        
        # Both should be clean
        success_clean = self.test_clean_json_output(success_response)
        conflict_clean = self.test_clean_json_output(conflict_response)
        
        errors.extend(success_clean.errors)
        errors.extend(conflict_clean.errors)
        
        # They should have different structures (non-overlapping)
        success_fields = set(success_response.keys())
        conflict_fields = set(conflict_response.keys())
        
        # Both should have 'success' field but different additional fields
        if "success" not in success_fields or "success" not in conflict_fields:
            errors.append("Both success and conflict responses should have 'success' field")
        
        # Success should be True in success response, False in conflict
        if success_response.get("success") is not True:
            errors.append("Success response should have success=True")
        
        if conflict_response.get("success") is not False:
            errors.append("Conflict response should have success=False")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


def create_cards_save_scenarios() -> ScenarioTestRunner:
    """Create scenario runner for cards/save endpoint."""
    runner = ScenarioTestRunner("cards_save")
    
    # Success scenario
    success_pattern = ValidationPattern(
        name="cards_save_success",
        description="Successful card save",
        rules=[
            ValidationRule("success", bool, required=True),
            ValidationRule("new_card_hist_id", int, required=False)
        ],
        business_rules=[
            lambda r: r.get("success") is True,
            lambda r: "new_card_hist_id" in r if r.get("success") else True
        ]
    )
    
    success_scenario = ScenarioTest(
        name="success",
        description="Card saved successfully without conflicts",
        scenario=ResponseScenario.SUCCESS,
        expected_status_codes=[200],
        validation_pattern=success_pattern,
        business_logic_validator=lambda r: r.get("success") is True and "new_card_hist_id" in r
    )
    
    # Conflict scenario
    conflict_pattern = ValidationPattern(
        name="cards_save_conflict",
        description="Card save with conflicts",
        rules=[
            ValidationRule("success", bool, required=True),
            ValidationRule("conflicts", dict, required=False)
        ],
        business_rules=[
            lambda r: r.get("success") is False,
            lambda r: "conflicts" in r if r.get("success") is False else True
        ]
    )
    
    conflict_scenario = ScenarioTest(
        name="conflict",
        description="Card save failed due to conflicts",
        scenario=ResponseScenario.CONFLICT,
        expected_status_codes=[200],  # Still 200, but success=False
        validation_pattern=conflict_pattern,
        business_logic_validator=lambda r: r.get("success") is False and "conflicts" in r
    )
    
    runner.add_scenario(success_scenario)
    runner.add_scenario(conflict_scenario)
    
    return runner


def create_ttable_versions_scenarios() -> ScenarioTestRunner:
    """Create scenario runner for ttable versions endpoints."""
    runner = ScenarioTestRunner("ttable_versions")
    
    # Success scenario (200)
    success_pattern = ValidationPattern(
        name="ttable_success",
        description="Successful ttable operation",
        rules=[ValidationRule("success", bool, required=True)],
        business_rules=[lambda r: r.get("success") is True]
    )
    
    success_scenario = ScenarioTest(
        name="success",
        description="Ttable operation completed successfully",
        scenario=ResponseScenario.SUCCESS,
        expected_status_codes=[200],
        validation_pattern=success_pattern
    )
    
    # Conflict scenario (202)
    conflict_pattern = ValidationPattern(
        name="ttable_conflict",
        description="Ttable operation with conflicts",
        rules=[
            ValidationRule("success", bool, required=True),
            ValidationRule("conflicts", dict, required=False)
        ],
        business_rules=[lambda r: r.get("success") is False]
    )
    
    conflict_scenario = ScenarioTest(
        name="conflict",
        description="Ttable operation has conflicts",
        scenario=ResponseScenario.CONFLICT,
        expected_status_codes=[202],
        validation_pattern=conflict_pattern
    )
    
    runner.add_scenario(success_scenario)
    runner.add_scenario(conflict_scenario)
    
    return runner


def create_generic_crud_scenarios(entity_name: str) -> ScenarioTestRunner:
    """Create generic CRUD operation scenarios."""
    runner = ScenarioTestRunner(f"{entity_name}_crud")
    
    # Success scenario
    success_pattern = ValidationPattern(
        name=f"{entity_name}_success",
        description=f"Successful {entity_name} operation",
        rules=[ValidationRule("success", bool, required=True)],
        business_rules=[lambda r: r.get("success") is True]
    )
    
    success_scenario = ScenarioTest(
        name="success",
        description=f"{entity_name} operation successful",
        scenario=ResponseScenario.SUCCESS,
        expected_status_codes=[200, 201],
        validation_pattern=success_pattern
    )
    
    # Not found scenario
    not_found_pattern = ValidationPattern(
        name=f"{entity_name}_not_found",
        description=f"{entity_name} not found",
        rules=[
            ValidationRule("error", str, required=False),
            ValidationRule("message", str, required=False)
        ],
        business_rules=[lambda r: bool(r.get("error") or r.get("message"))]
    )
    
    not_found_scenario = ScenarioTest(
        name="not_found",
        description=f"{entity_name} not found",
        scenario=ResponseScenario.NOT_FOUND,
        expected_status_codes=[404],
        validation_pattern=not_found_pattern
    )
    
    # Validation error scenario
    validation_error_pattern = ValidationPattern(
        name=f"{entity_name}_validation_error",
        description=f"{entity_name} validation error",
        rules=[
            ValidationRule("error", str, required=False),
            ValidationRule("details", dict, required=False)
        ],
        business_rules=[lambda r: bool(r.get("error"))]
    )
    
    validation_error_scenario = ScenarioTest(
        name="validation_error",
        description=f"{entity_name} validation failed",
        scenario=ResponseScenario.VALIDATION_ERROR,
        expected_status_codes=[400, 422],
        validation_pattern=validation_error_pattern
    )
    
    runner.add_scenario(success_scenario)
    runner.add_scenario(not_found_scenario)
    runner.add_scenario(validation_error_scenario)
    
    return runner