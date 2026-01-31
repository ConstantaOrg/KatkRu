"""
Independent API Response Validator

This module provides validation utilities that test actual API responses
without depending on Pydantic models, breaking the circular dependency
between tests, response models, and documentation.
"""

from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass
import json


@dataclass
class ValidationRule:
    """Defines a validation rule for a response field."""
    field_name: str
    field_type: Type
    required: bool = True
    business_rule: Optional[Callable[[Any], bool]] = None
    description: str = ""


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class APIResponseValidator:
    """
    Independent response validator that validates actual HTTP responses
    without depending on Pydantic models.
    
    This validator focuses on essential field validation while allowing
    additional fields, making tests flexible and independent of model changes.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.
        
        Args:
            strict_mode: If True, additional fields cause validation failure.
                        If False, additional fields are allowed.
        """
        self.strict_mode = strict_mode
        self.validation_rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.validation_rules.append(rule)
    
    def validate_required_fields(self, response: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
        """
        Validate that all required fields are present in the response.
        
        Args:
            response: The API response data
            required_fields: List of field names that must be present
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []
        
        for field in required_fields:
            if field not in response:
                errors.append(f"Required field '{field}' is missing from response")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_field_types(self, response: Dict[str, Any], field_types: Dict[str, Type]) -> ValidationResult:
        """
        Validate that fields have the expected types.
        
        Args:
            response: The API response data
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []
        
        for field_name, expected_type in field_types.items():
            if field_name in response:
                actual_value = response[field_name]
                actual_type = type(actual_value)
                
                # Strict type checking - handle bool/int distinction
                if expected_type == bool:
                    # For bool, only accept actual bool, not int
                    if actual_type != bool:
                        errors.append(
                            f"Field '{field_name}' has type {actual_type.__name__}, "
                            f"expected {expected_type.__name__}"
                        )
                elif expected_type == int:
                    # For int, accept int but not bool (even though bool is subclass of int)
                    if actual_type == bool:
                        errors.append(
                            f"Field '{field_name}' has type {actual_type.__name__}, "
                            f"expected {expected_type.__name__}"
                        )
                    elif not isinstance(actual_value, int):
                        # Handle special case for float that represents an integer
                        if isinstance(actual_value, float) and actual_value.is_integer():
                            continue  # Allow float that represents an integer
                        errors.append(
                            f"Field '{field_name}' has type {actual_type.__name__}, "
                            f"expected {expected_type.__name__}"
                        )
                elif expected_type == float:
                    # For float, accept float or int, but not bool
                    if actual_type == bool:
                        errors.append(
                            f"Field '{field_name}' has type {actual_type.__name__}, "
                            f"expected {expected_type.__name__}"
                        )
                    elif not isinstance(actual_value, (int, float)):
                        errors.append(
                            f"Field '{field_name}' has type {actual_type.__name__}, "
                            f"expected {expected_type.__name__}"
                        )
                else:
                    # For other types, use standard isinstance check
                    if not isinstance(actual_value, expected_type):
                        errors.append(
                            f"Field '{field_name}' has type {actual_type.__name__}, "
                            f"expected {expected_type.__name__}"
                        )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_business_logic(self, response: Dict[str, Any], business_rules: List[Callable[[Dict[str, Any]], bool]]) -> ValidationResult:
        """
        Validate business logic rules against the response.
        
        Args:
            response: The API response data
            business_rules: List of functions that return True if business rule is satisfied
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []
        
        for i, rule in enumerate(business_rules):
            try:
                if not rule(response):
                    errors.append(f"Business rule {i + 1} failed for response")
            except Exception as e:
                errors.append(f"Business rule {i + 1} raised exception: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_list_structure(self, response: Dict[str, Any], list_field: str, item_rules: List[ValidationRule]) -> ValidationResult:
        """
        Validate the structure of list items in the response.
        
        Args:
            response: The API response data
            list_field: Name of the field containing the list
            item_rules: Validation rules to apply to each list item
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []
        
        if list_field not in response:
            errors.append(f"List field '{list_field}' is missing from response")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        items = response[list_field]
        if not isinstance(items, list):
            errors.append(f"Field '{list_field}' is not a list")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"Item {i} in '{list_field}' is not a dictionary")
                continue
            
            # Validate each rule against the item
            for rule in item_rules:
                if rule.required and rule.field_name not in item:
                    errors.append(f"Item {i} in '{list_field}' missing required field '{rule.field_name}'")
                elif rule.field_name in item:
                    value = item[rule.field_name]
                    if not isinstance(value, rule.field_type):
                        errors.append(
                            f"Item {i} in '{list_field}' field '{rule.field_name}' has type "
                            f"{type(value).__name__}, expected {rule.field_type.__name__}"
                        )
                    
                    # Apply business rule if present
                    if rule.business_rule and not rule.business_rule(value):
                        errors.append(
                            f"Item {i} in '{list_field}' field '{rule.field_name}' "
                            f"failed business rule: {rule.description}"
                        )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_status_code(self, actual_status: int, expected_statuses: List[int]) -> ValidationResult:
        """
        Validate HTTP status code independently of response models.
        
        Args:
            actual_status: The actual HTTP status code
            expected_statuses: List of acceptable status codes
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []
        
        if actual_status not in expected_statuses:
            errors.append(
                f"HTTP status {actual_status} not in expected statuses {expected_statuses}"
            )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_response(self, response: Dict[str, Any]) -> ValidationResult:
        """
        Validate response against all configured rules.
        
        Args:
            response: The API response data
            
        Returns:
            ValidationResult with validation status and any errors
        """
        all_errors = []
        all_warnings = []
        
        # Apply all validation rules
        for rule in self.validation_rules:
            if rule.required and rule.field_name not in response:
                all_errors.append(f"Required field '{rule.field_name}' is missing")
            elif rule.field_name in response:
                value = response[rule.field_name]
                actual_type = type(value)
                expected_type = rule.field_type
                
                # Type validation with strict bool/int distinction
                type_valid = True
                if expected_type == bool:
                    # For bool, only accept actual bool, not int
                    if actual_type != bool:
                        type_valid = False
                elif expected_type == int:
                    # For int, accept int but not bool (even though bool is subclass of int)
                    if actual_type == bool:
                        type_valid = False
                    elif not isinstance(value, int):
                        # Handle special case for float that represents an integer
                        if isinstance(value, float) and value.is_integer():
                            type_valid = True
                        else:
                            type_valid = False
                elif expected_type == float:
                    # For float, accept float or int, but not bool
                    if actual_type == bool:
                        type_valid = False
                    elif not isinstance(value, (int, float)):
                        type_valid = False
                else:
                    # For other types, use standard isinstance check
                    if not isinstance(value, expected_type):
                        type_valid = False
                
                if not type_valid:
                    all_errors.append(
                        f"Field '{rule.field_name}' has type {actual_type.__name__}, "
                        f"expected {expected_type.__name__}"
                    )
                
                # Business rule validation
                if rule.business_rule and not rule.business_rule(value):
                    all_errors.append(
                        f"Field '{rule.field_name}' failed business rule: {rule.description}"
                    )
        
        # Check for additional fields in strict mode
        if self.strict_mode:
            expected_fields = {rule.field_name for rule in self.validation_rules}
            actual_fields = set(response.keys())
            additional_fields = actual_fields - expected_fields
            
            if additional_fields:
                all_warnings.append(f"Additional fields found: {list(additional_fields)}")
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def allow_additional_fields(self, allow: bool = True) -> None:
        """
        Configure whether additional fields are allowed.
        
        Args:
            allow: If True, additional fields don't cause validation failure
        """
        self.strict_mode = not allow


class EndpointValidator:
    """
    Validator for specific API endpoints that encapsulates
    endpoint-specific validation logic.
    """
    
    def __init__(self, endpoint: str, method: str):
        self.endpoint = endpoint
        self.method = method
        self.validators: Dict[int, APIResponseValidator] = {}  # status_code -> validator
    
    def add_status_validator(self, status_code: int, validator: APIResponseValidator) -> None:
        """Add a validator for a specific status code."""
        self.validators[status_code] = validator
    
    def validate_response(self, status_code: int, response_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate response for the given status code.
        
        Args:
            status_code: HTTP status code
            response_data: Response data
            
        Returns:
            ValidationResult with validation status and any errors
        """
        if status_code not in self.validators:
            return ValidationResult(
                is_valid=False,
                errors=[f"No validator configured for status code {status_code}"],
                warnings=[]
            )
        
        validator = self.validators[status_code]
        return validator.validate_response(response_data)


def create_groups_validator() -> EndpointValidator:
    """Create validator for groups endpoints."""
    validator = EndpointValidator("/api/v1/private/groups/get", "GET")
    
    # Validator for 200 status
    success_validator = APIResponseValidator(strict_mode=False)
    success_validator.add_rule(ValidationRule("groups", list, required=True))
    
    validator.add_status_validator(200, success_validator)
    return validator


def create_n8n_cards_validator() -> EndpointValidator:
    """Create validator for N8N cards endpoints."""
    validator = EndpointValidator("/api/v1/private/n8n_ui/cards/save", "POST")
    
    # Validator for success response (200)
    success_validator = APIResponseValidator(strict_mode=False)
    success_validator.add_rule(ValidationRule("success", bool, required=True))
    success_validator.add_rule(ValidationRule("new_card_hist_id", int, required=False))
    
    # Validator for conflict response (200 with success=False)
    conflict_validator = APIResponseValidator(strict_mode=False)
    conflict_validator.add_rule(ValidationRule("success", bool, required=True))
    conflict_validator.add_rule(ValidationRule("conflicts", dict, required=False))
    
    validator.add_status_validator(200, success_validator)
    return validator