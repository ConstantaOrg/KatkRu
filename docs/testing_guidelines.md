# API Testing Guidelines

## Overview

This document provides best practices for API testing that is independent of response models, maintaining test-model separation, and effectively using @overload response models.

**Requirements validated: 4.4, 7.2**

## Core Principles

### 1. Test Independence from Response Models

**Principle**: Tests should validate actual API behavior, not documentation models.

```python
# ❌ BAD: Testing against response model
def test_endpoint_bad():
    response = client.post("/api/endpoint", json=data)
    parsed = EndpointResponse.model_validate(response.json())
    assert parsed.success == True

# ✅ GOOD: Testing actual response behavior
def test_endpoint_good():
    response = client.post("/api/endpoint", json=data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "required_field" in data
```

**Benefits**:
- Tests continue to pass when models are corrected
- Tests validate real API behavior
- Reduced coupling between tests and documentation

### 2. Essential Field Validation

**Principle**: Focus on essential data presence rather than exact schema matching.

```python
# ✅ GOOD: Essential field validation
def validate_essential_fields(response_data: dict, required_fields: list):
    """Validate that essential fields are present with correct types."""
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"
        assert response_data[field] is not None, f"Field {field} is null"

def test_user_data():
    response = client.get("/api/users/123")
    data = response.json()
    
    # Validate essential fields
    validate_essential_fields(data, ["id", "name", "email"])
    
    # Allow additional fields without failing
    # This makes tests resilient to non-breaking changes
```

### 3. Business Logic Focus

**Principle**: Tests should validate business logic correctness, not model compliance.

```python
# ✅ GOOD: Business logic validation
def test_card_save_conflict_detection():
    """Test that the system correctly detects teacher conflicts."""
    # Setup: Create a card with teacher at specific time
    setup_data = create_test_card(teacher_id=1, position=1, ttable_id=1)
    
    # Action: Try to save another card with same teacher/time
    conflict_data = create_conflicting_card(teacher_id=1, position=1, ttable_id=1)
    response = client.post("/api/cards/save", json=conflict_data)
    
    # Validation: Business logic should detect conflict
    assert response.status_code == 200  # Still returns 200 but with conflict info
    data = response.json()
    assert data["success"] == False
    assert "conflicts" in data
    assert "teacher already has a group" in data["description"].lower()
```

## Testing Multi-Response Endpoints

### Pattern for @overload Response Models

When testing endpoints that use @overload response models:

```python
def test_multi_response_endpoint():
    """Test endpoint with multiple response scenarios."""
    
    # Test success scenario
    success_response = client.post("/api/endpoint", json=valid_data)
    assert success_response.status_code == 200
    success_data = success_response.json()
    assert success_data["success"] == True
    assert "result_field" in success_data
    
    # Test conflict scenario
    conflict_response = client.post("/api/endpoint", json=conflicting_data)
    assert conflict_response.status_code == 200  # May still be 200 with conflict info
    conflict_data = conflict_response.json()
    assert conflict_data["success"] == False
    assert "conflicts" in conflict_data or "error" in conflict_data
```

### Status Code Testing

```python
def test_status_code_scenarios():
    """Test different status codes for the same endpoint."""
    
    # 200: Success
    response_200 = client.put("/api/ttable/versions/pre-commit", json=ready_data)
    assert response_200.status_code == 200
    
    # 202: Existing active version (business logic conflict)
    response_202 = client.put("/api/ttable/versions/pre-commit", json=existing_data)
    assert response_202.status_code == 202
    
    # 409: Missing groups (validation conflict)
    response_409 = client.put("/api/ttable/versions/pre-commit", json=incomplete_data)
    assert response_409.status_code == 409
```

## Using @overload Response Models Effectively

### 1. Creating Clean Response Models

```python
from typing import overload, Literal, Union
from pydantic import BaseModel, Field

# Define separate models for each scenario
class OperationSuccessResponse(BaseModel):
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field(..., description="Success message")
    result_id: int = Field(..., description="ID of created resource")

class OperationConflictResponse(BaseModel):
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field(..., description="Error message")
    conflicts: Dict[str, Any] = Field(..., description="Conflict details")

# Union type for FastAPI
OperationResponse = Union[OperationSuccessResponse, OperationConflictResponse]
```

### 2. Type-Safe Response Creation

```python
# Use @overload for type safety
@overload
def create_operation_response(
    success: Literal[True],
    result_id: int,
    message: str = "Operation completed successfully"
) -> OperationSuccessResponse: ...

@overload
def create_operation_response(
    success: Literal[False],
    conflicts: Dict[str, Any],
    message: str = "Operation failed"
) -> OperationConflictResponse: ...

def create_operation_response(
    success: bool,
    result_id: int = None,
    conflicts: Dict[str, Any] = None,
    message: str = None
) -> OperationResponse:
    """Create type-safe response based on success status."""
    if success:
        return OperationSuccessResponse(
            result_id=result_id,
            message=message or "Operation completed successfully"
        )
    else:
        return OperationConflictResponse(
            conflicts=conflicts,
            message=message or "Operation failed"
        )
```

### 3. FastAPI Endpoint Implementation

```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse

@router.post("/operation", responses={
    200: {"model": OperationSuccessResponse, "description": "Operation successful"},
    409: {"model": OperationConflictResponse, "description": "Operation conflicts detected"}
})
async def perform_operation(data: OperationData):
    try:
        result_id = await business_logic(data)
        response = create_operation_response(success=True, result_id=result_id)
        return JSONResponse(
            status_code=200,
            content=response.model_dump(exclude_none=True)
        )
    except ConflictError as e:
        response = create_operation_response(
            success=False,
            conflicts=e.conflicts,
            message=str(e)
        )
        return JSONResponse(
            status_code=409,
            content=response.model_dump(exclude_none=True)
        )
```

## Test Utilities and Helpers

### 1. Response Validation Utilities

```python
class APIResponseValidator:
    """Utility class for validating API responses independent of models."""
    
    def validate_required_fields(self, response: dict, required_fields: list):
        """Validate that required fields are present."""
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"
            assert response[field] is not None, f"Field {field} is null"
    
    def validate_field_types(self, response: dict, field_types: dict):
        """Validate field types without strict schema matching."""
        for field, expected_type in field_types.items():
            if field in response:
                assert isinstance(response[field], expected_type), \
                    f"Field {field} has type {type(response[field])}, expected {expected_type}"
    
    def validate_business_logic(self, response: dict, business_rules: list):
        """Validate business logic rules."""
        for rule in business_rules:
            assert rule(response), f"Business rule failed: {rule.__name__}"
    
    def allow_additional_fields(self, response: dict, known_fields: set):
        """Allow additional fields without failing (non-breaking changes)."""
        additional_fields = set(response.keys()) - known_fields
        if additional_fields:
            print(f"Note: Response contains additional fields: {additional_fields}")
        # This is informational only, not a failure
```

### 2. Test Data Generators

```python
def create_test_data_matching_constraints():
    """Create test data that matches actual database constraints."""
    return {
        "teacher_id": random.randint(1, 100),
        "group_id": random.randint(1, 50),
        "position": random.randint(1, 8),  # Valid lesson positions
        "ttable_id": random.randint(1, 10)
    }

def create_conflicting_scenario(base_data: dict):
    """Create data that should trigger business logic conflicts."""
    return {
        **base_data,
        "teacher_id": base_data["teacher_id"],  # Same teacher
        "position": base_data["position"],      # Same time slot
        "group_id": base_data["group_id"] + 1   # Different group (conflict)
    }
```

## Best Practices Summary

### DO ✅

1. **Test actual API behavior** - Validate HTTP responses directly
2. **Focus on essential fields** - Test required data presence and types
3. **Validate business logic** - Test that business rules are enforced
4. **Use flexible assertions** - Allow additional fields for non-breaking changes
5. **Test all response scenarios** - Cover success, conflict, and error cases
6. **Use @overload for type safety** - Create clean response models without null pollution
7. **Separate concerns** - Keep tests independent of documentation models

### DON'T ❌

1. **Don't validate against response models in tests** - This creates circular dependencies
2. **Don't use strict schema matching** - This breaks tests on non-breaking changes
3. **Don't ignore business logic** - Tests should validate actual functionality
4. **Don't create inheritance-based response models** - This leads to null field pollution
5. **Don't mix documentation and testing concerns** - Keep them separate
6. **Don't use placeholder examples** - Use realistic data in documentation
7. **Don't assume model accuracy** - Always validate models against real responses

## Migration Guide

### From Model-Dependent to Independent Testing

1. **Identify model-dependent tests**:
   ```python
   # Find tests that use .model_validate() or similar
   grep -r "model_validate\|parse_obj" tests/
   ```

2. **Replace with direct validation**:
   ```python
   # Before
   parsed = ResponseModel.model_validate(response.json())
   assert parsed.field == expected_value
   
   # After
   data = response.json()
   assert data["field"] == expected_value
   ```

3. **Add business logic validation**:
   ```python
   # Add tests for actual business rules
   def test_business_rule():
       # Test that the system enforces business constraints
       pass
   ```

4. **Update response models to use @overload**:
   ```python
   # Create clean, scenario-specific models
   # Use @overload functions for type safety
   # Remove inheritance-based pollution
   ```

## Conclusion

Following these guidelines ensures that:
- Tests validate real API behavior, not documentation artifacts
- Response models accurately reflect actual API responses
- Documentation remains high-quality and useful
- The system is maintainable and resilient to changes

The key is maintaining clear separation between testing (validates behavior), models (document contracts), and business logic (implements functionality).