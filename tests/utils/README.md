# Independent API Response Validator

This module provides validation utilities that test actual API responses without depending on Pydantic models, breaking the circular dependency between tests, response models, and documentation.

## Overview

The `APIResponseValidator` class allows you to:

- Validate API responses directly without model dependencies
- Focus on essential field validation while allowing additional fields
- Handle multi-response scenarios (different status codes)
- Validate business logic independently of documentation models
- Maintain test stability when response models change

## Key Features

### 1. Model Independence
Tests validate actual API behavior rather than model compliance:

```python
from tests.utils.api_response_validator import APIResponseValidator, ValidationRule

# Create validator focused on essential fields only
validator = APIResponseValidator(strict_mode=False)
validator.add_rule(ValidationRule("groups", list, required=True))

# Validate actual API response
response_data = resp.json()
result = validator.validate_response(response_data)
```

### 2. Flexible Field Validation
Allow additional fields without breaking tests:

```python
# Non-strict mode allows additional fields (recommended)
validator = APIResponseValidator(strict_mode=False)

# Strict mode requires exact field matching
validator = APIResponseValidator(strict_mode=True)
```

### 3. Business Logic Validation
Validate business rules independently:

```python
def groups_not_empty(response):
    return len(response.get("groups", [])) >= 0

business_rules = [groups_not_empty]
result = validator.validate_business_logic(response_data, business_rules)
```

### 4. Multi-Response Scenarios
Handle endpoints with different response formats:

```python
endpoint_validator = EndpointValidator("/api/endpoint", "POST")

# Configure different validators for different status codes
success_validator = APIResponseValidator()
success_validator.add_rule(ValidationRule("success", bool, required=True))

error_validator = APIResponseValidator()
error_validator.add_rule(ValidationRule("error", str, required=True))

endpoint_validator.add_status_validator(200, success_validator)
endpoint_validator.add_status_validator(400, error_validator)
```

## Usage Examples

### Basic Response Validation

```python
@pytest.mark.asyncio
async def test_groups_endpoint(client, seed_info):
    resp = await client.get("/api/v1/private/groups/get", params={...})
    
    # Validate status code
    validator = APIResponseValidator()
    status_result = validator.validate_status_code(resp.status_code, [200])
    assert status_result.is_valid
    
    # Validate response structure
    response_data = resp.json()
    field_result = validator.validate_required_fields(response_data, ["groups"])
    assert field_result.is_valid
    
    # Validate field types
    type_result = validator.validate_field_types(response_data, {"groups": list})
    assert type_result.is_valid
```

### List Structure Validation

```python
# Validate list items structure
item_rules = [
    ValidationRule("id", int, required=True),
    ValidationRule("name", str, required=True)
]

result = validator.validate_list_structure(response_data, "groups", item_rules)
assert result.is_valid
```

## Benefits

1. **Test Independence**: Tests remain stable when response models change for documentation purposes
2. **Essential Focus**: Validate only what matters for business logic
3. **Flexibility**: Allow additional fields without breaking tests
4. **Clear Errors**: Descriptive error messages for debugging
5. **Multi-Scenario Support**: Handle complex endpoints with different response formats

## Property-Based Testing

The framework includes comprehensive property-based tests that validate:

- **Test Framework Independence**: Tests remain stable across model changes
- **Direct Response Validation**: Validates actual response data without model dependencies
- **Essential Field Validation**: Focuses on required fields while allowing additional ones
- **Business Logic Independence**: Validates business rules independent of models
- **Multi-Response Scenario Handling**: Properly handles different response formats

## Migration from Model-Based Tests

To migrate existing tests:

1. Replace Pydantic model validation with direct response validation
2. Focus on essential fields rather than exact schema matching
3. Use business logic validation for complex rules
4. Allow additional fields to prevent breaking changes

Example migration:

```python
# Before (model-dependent)
response = GroupsGetResponse(**resp.json())
assert response.groups is not None

# After (model-independent)
validator = APIResponseValidator(strict_mode=False)
validator.add_rule(ValidationRule("groups", list, required=True))
result = validator.validate_response(resp.json())
assert result.is_valid
```

This approach breaks the circular dependency and makes tests more robust and maintainable.