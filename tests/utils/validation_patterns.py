"""
Common Validation Patterns for API Testing

This module provides pre-configured validation patterns for common API response
scenarios, making it easier to write consistent tests across the application.
"""

from typing import Dict, List, Any, Callable, Optional, Union
from dataclasses import dataclass
from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, ValidationResult


@dataclass
class ValidationPattern:
    """Represents a reusable validation pattern."""
    name: str
    description: str
    rules: List[ValidationRule]
    business_rules: List[Callable[[Dict[str, Any]], bool]]
    
    def create_validator(self, strict_mode: bool = False) -> APIResponseValidator:
        """Create a validator with this pattern's rules."""
        validator = APIResponseValidator(strict_mode=strict_mode)
        for rule in self.rules:
            validator.add_rule(rule)
        return validator


class CommonValidationPatterns:
    """Collection of common validation patterns used across the API."""
    
    @staticmethod
    def paginated_list_response(list_field: str = "items") -> ValidationPattern:
        """Pattern for paginated list responses."""
        def has_valid_pagination(response):
            if "pagination" in response:
                pagination = response["pagination"]
                return (
                    isinstance(pagination.get("total"), int) and
                    isinstance(pagination.get("page"), int) and
                    pagination.get("total", 0) >= 0 and
                    pagination.get("page", 1) >= 1
                )
            return True  # Pagination is optional
        
        def list_is_valid(response):
            items = response.get(list_field, [])
            return isinstance(items, list)
        
        return ValidationPattern(
            name="paginated_list",
            description=f"Paginated list response with {list_field} field",
            rules=[
                ValidationRule(list_field, list, required=True),
                ValidationRule("pagination", dict, required=False)
            ],
            business_rules=[has_valid_pagination, list_is_valid]
        )
    
    @staticmethod
    def success_response() -> ValidationPattern:
        """Pattern for simple success/failure responses."""
        def success_is_boolean(response):
            success = response.get("success")
            return isinstance(success, bool)
        
        return ValidationPattern(
            name="success_response",
            description="Simple success/failure response",
            rules=[
                ValidationRule("success", bool, required=True)
            ],
            business_rules=[success_is_boolean]
        )
    
    @staticmethod
    def error_response() -> ValidationPattern:
        """Pattern for error responses."""
        def error_message_exists(response):
            return bool(response.get("error") or response.get("message"))
        
        return ValidationPattern(
            name="error_response",
            description="Error response with message",
            rules=[
                ValidationRule("error", str, required=False),
                ValidationRule("message", str, required=False),
                ValidationRule("detail", str, required=False)
            ],
            business_rules=[error_message_exists]
        )
    
    @staticmethod
    def groups_response() -> ValidationPattern:
        """Pattern for groups endpoint responses."""
        def groups_have_names(response):
            groups = response.get("groups", [])
            if groups:
                return all(isinstance(group.get("name"), str) for group in groups)
            return True
        
        def groups_have_ids(response):
            groups = response.get("groups", [])
            if groups:
                return all(isinstance(group.get("id"), int) for group in groups)
            return True
        
        return ValidationPattern(
            name="groups_response",
            description="Groups endpoint response",
            rules=[
                ValidationRule("groups", list, required=True)
            ],
            business_rules=[groups_have_names, groups_have_ids]
        )
    
    @staticmethod
    def teachers_response() -> ValidationPattern:
        """Pattern for teachers endpoint responses."""
        def teachers_have_names(response):
            teachers = response.get("teachers", [])
            if teachers:
                return all(isinstance(teacher.get("name"), str) for teacher in teachers)
            return True
        
        return ValidationPattern(
            name="teachers_response",
            description="Teachers endpoint response",
            rules=[
                ValidationRule("teachers", list, required=True)
            ],
            business_rules=[teachers_have_names]
        )
    
    @staticmethod
    def disciplines_response() -> ValidationPattern:
        """Pattern for disciplines endpoint responses."""
        def disciplines_have_names(response):
            disciplines = response.get("disciplines", [])
            if disciplines:
                return all(isinstance(disc.get("name"), str) for disc in disciplines)
            return True
        
        return ValidationPattern(
            name="disciplines_response",
            description="Disciplines endpoint response",
            rules=[
                ValidationRule("disciplines", list, required=True)
            ],
            business_rules=[disciplines_have_names]
        )
    
    @staticmethod
    def timetable_response() -> ValidationPattern:
        """Pattern for timetable endpoint responses."""
        def timetable_has_valid_structure(response):
            timetable = response.get("timetable", {})
            if timetable:
                # Timetable should have days or be empty dict
                return isinstance(timetable, dict)
            return True
        
        return ValidationPattern(
            name="timetable_response",
            description="Timetable endpoint response",
            rules=[
                ValidationRule("timetable", dict, required=True)
            ],
            business_rules=[timetable_has_valid_structure]
        )
    
    @staticmethod
    def cards_save_success() -> ValidationPattern:
        """Pattern for successful cards save response."""
        def has_new_card_id(response):
            if response.get("success") is True:
                return "new_card_hist_id" in response
            return True
        
        return ValidationPattern(
            name="cards_save_success",
            description="Successful cards save response",
            rules=[
                ValidationRule("success", bool, required=True),
                ValidationRule("new_card_hist_id", int, required=False)
            ],
            business_rules=[has_new_card_id]
        )
    
    @staticmethod
    def cards_save_conflict() -> ValidationPattern:
        """Pattern for cards save conflict response."""
        def has_conflicts_when_failed(response):
            if response.get("success") is False:
                return "conflicts" in response
            return True
        
        return ValidationPattern(
            name="cards_save_conflict",
            description="Cards save conflict response",
            rules=[
                ValidationRule("success", bool, required=True),
                ValidationRule("conflicts", dict, required=False)
            ],
            business_rules=[has_conflicts_when_failed]
        )


class MultiResponseValidator:
    """
    Validator for endpoints that can return different response formats
    based on business logic or status codes.
    """
    
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.patterns: Dict[str, ValidationPattern] = {}
        self.status_patterns: Dict[int, str] = {}  # status_code -> pattern_name
    
    def add_pattern(self, pattern_name: str, pattern: ValidationPattern) -> None:
        """Add a validation pattern."""
        self.patterns[pattern_name] = pattern
    
    def add_status_pattern(self, status_code: int, pattern_name: str) -> None:
        """Associate a status code with a pattern."""
        self.status_patterns[status_code] = pattern_name
    
    def validate_response(self, status_code: int, response_data: Dict[str, Any], 
                         pattern_name: Optional[str] = None) -> ValidationResult:
        """
        Validate response using appropriate pattern.
        
        Args:
            status_code: HTTP status code
            response_data: Response data
            pattern_name: Specific pattern to use (if None, uses status code mapping)
        """
        # Determine which pattern to use
        if pattern_name is None:
            if status_code in self.status_patterns:
                pattern_name = self.status_patterns[status_code]
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"No pattern configured for status code {status_code}"],
                    warnings=[]
                )
        
        if pattern_name not in self.patterns:
            return ValidationResult(
                is_valid=False,
                errors=[f"Pattern '{pattern_name}' not found"],
                warnings=[]
            )
        
        # Create validator and validate
        pattern = self.patterns[pattern_name]
        validator = pattern.create_validator(strict_mode=False)
        
        # Validate structure
        structure_result = validator.validate_response(response_data)
        
        # Validate business rules
        business_result = validator.validate_business_logic(response_data, pattern.business_rules)
        
        # Combine results
        all_errors = structure_result.errors + business_result.errors
        all_warnings = structure_result.warnings + business_result.warnings
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )


def create_cards_save_validator() -> MultiResponseValidator:
    """Create a multi-response validator for cards/save endpoint."""
    validator = MultiResponseValidator("cards_save")
    
    # Add patterns for different scenarios
    validator.add_pattern("success", CommonValidationPatterns.cards_save_success())
    validator.add_pattern("conflict", CommonValidationPatterns.cards_save_conflict())
    
    # Both success and conflict return 200, so we need to check response content
    validator.add_status_pattern(200, "success")  # Default to success pattern
    
    return validator


def create_ttable_versions_validator() -> MultiResponseValidator:
    """Create a multi-response validator for ttable versions endpoints."""
    validator = MultiResponseValidator("ttable_versions")
    
    # Success pattern (200)
    success_pattern = ValidationPattern(
        name="ttable_success",
        description="Successful ttable operation",
        rules=[ValidationRule("success", bool, required=True)],
        business_rules=[lambda r: r.get("success") is True]
    )
    
    # Conflict pattern (202)
    conflict_pattern = ValidationPattern(
        name="ttable_conflict",
        description="Ttable operation conflict",
        rules=[
            ValidationRule("success", bool, required=True),
            ValidationRule("conflicts", dict, required=False)
        ],
        business_rules=[lambda r: r.get("success") is False]
    )
    
    validator.add_pattern("success", success_pattern)
    validator.add_pattern("conflict", conflict_pattern)
    validator.add_status_pattern(200, "success")
    validator.add_status_pattern(202, "conflict")
    
    return validator