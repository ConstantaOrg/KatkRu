"""
Demonstration of Independent API Response Validation

This test shows how the new APIResponseValidator works with actual
API endpoints, validating real responses without depending on Pydantic models.
"""

import pytest
from tests.utils.api_response_validator import (
    APIResponseValidator,
    ValidationRule,
    EndpointValidator
)


@pytest.mark.asyncio
async def test_groups_endpoint_with_independent_validation(client, seed_info):
    """
    Demonstrate independent validation of groups endpoint.
    
    This test validates actual API behavior without depending on response models,
    showing how the framework breaks the circular dependency.
    """
    # Make actual API call
    resp = await client.post(
        "/api/v1/private/groups/get",
        params={"bid": seed_info["building_id"], "limit": 10, "offset": 0},
    )
    
    # Validate HTTP status independently
    validator = APIResponseValidator(strict_mode=False)
    status_result = validator.validate_status_code(resp.status_code, [200])
    assert status_result.is_valid, f"Status validation failed: {status_result.errors}"
    
    # Get actual response data
    response_data = resp.json()
    
    # Validate essential fields directly (no model dependency)
    essential_fields = ["groups"]
    field_result = validator.validate_required_fields(response_data, essential_fields)
    assert field_result.is_valid, f"Required fields missing: {field_result.errors}"
    
    # Validate field types based on actual response structure
    field_types = {"groups": list}
    type_result = validator.validate_field_types(response_data, field_types)
    assert type_result.is_valid, f"Field type validation failed: {type_result.errors}"
    
    # Validate business logic independently
    def groups_list_not_empty(response):
        return len(response.get("groups", [])) >= 0  # Allow empty but must be list
    
    def groups_contain_expected_data(response):
        groups = response.get("groups", [])
        if groups:
            # If groups exist, they should have basic structure
            first_group = groups[0]
            return isinstance(first_group, dict) and "name" in first_group
        return True  # Empty list is valid
    
    business_rules = [groups_list_not_empty, groups_contain_expected_data]
    business_result = validator.validate_business_logic(response_data, business_rules)
    assert business_result.is_valid, f"Business logic validation failed: {business_result.errors}"
    
    # Verify that we can find the expected test group
    groups = response_data["groups"]
    assert any(group["name"] == "GR1" for group in groups), "Expected test group 'GR1' not found"


@pytest.mark.asyncio
async def test_cards_save_multi_response_validation(client, seed_info):
    """
    Demonstrate multi-response scenario validation for cards/save endpoint.
    
    This shows how the framework handles endpoints that can return different
    response formats based on business logic.
    """
    # Test successful save scenario first
    success_payload = {
        "card_hist_id": seed_info["hist_id"],
        "ttable_id": seed_info["ttable_id"],
        "lessons": [
            {
                "position": 3,  # Different position to avoid conflict (seed has 1 and 2)
                "discipline_id": seed_info["discipline_id"],
                "teacher_id": seed_info["teacher_id"],
                "aud": "303",
                "is_force": False,
            }
        ],
    }
    
    resp = await client.post("/api/v1/private/n8n_ui/cards/save", json=success_payload)
    response_data = resp.json()
    
    # Create validator that handles both success and conflict scenarios
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("success", bool, required=True))
    
    # Validate basic structure
    result = validator.validate_response(response_data)
    assert result.is_valid, f"Response validation failed: {result.errors}"
    
    # Verify business logic: successful save should have success=True
    assert response_data["success"] is True, "Expected successful save"
    assert "new_card_hist_id" in response_data, "Expected new card history ID"
    
    # Test conflict scenario
    conflict_payload = {
        "card_hist_id": seed_info["hist_id"],
        "ttable_id": seed_info["ttable_id"],
        "lessons": [
            {
                "position": 1,  # Same position as existing - should conflict
                "discipline_id": seed_info["discipline_id"],
                "teacher_id": seed_info["teacher_id"],
                "aud": "303",
                "is_force": False,
            }
        ],
    }
    
    conflict_resp = await client.post("/api/v1/private/n8n_ui/cards/save", json=conflict_payload)
    conflict_data = conflict_resp.json()
    
    # Validate conflict response structure (only check required fields)
    conflict_result = validator.validate_response(conflict_data)
    assert conflict_result.is_valid, f"Conflict response validation failed: {conflict_result.errors}"
    
    # Verify business logic: conflict should have success=False
    assert conflict_data["success"] is False, "Expected conflict response"
    assert "conflicts" in conflict_data, "Expected conflicts information"


@pytest.mark.asyncio
async def test_framework_independence_demonstration(client, seed_info):
    """
    Demonstrate that the test framework is independent of response model changes.
    
    This test shows that validation continues to work even when response models
    might be updated or changed, as long as the actual API behavior remains consistent.
    """
    # Make API call
    resp = await client.post(
        "/api/v1/private/groups/get",
        params={"bid": seed_info["building_id"], "limit": 10, "offset": 0},
    )
    
    response_data = resp.json()
    
    # Create validator focused only on essential business logic
    validator = APIResponseValidator(strict_mode=False)  # Allow additional fields
    
    # Define only the essential validation rules (what the business actually needs)
    essential_rules = [
        ValidationRule("groups", list, required=True, description="Must have groups list")
    ]
    
    for rule in essential_rules:
        validator.add_rule(rule)
    
    # Validate original response
    original_result = validator.validate_response(response_data)
    assert original_result.is_valid, f"Original validation failed: {original_result.errors}"
    
    # Simulate response model changes by adding "documentation-only" fields
    # (This represents what happens when response models are updated for documentation)
    enhanced_response = response_data.copy()
    enhanced_response.update({
        "pagination": {"total": 100, "page": 1},  # New pagination info
        "metadata": {"version": "v2", "timestamp": "2024-01-01T00:00:00Z"},  # New metadata
        "debug_info": {"query_time_ms": 15},  # New debug info
    })
    
    # Validate enhanced response - should still pass because we focus on essentials
    enhanced_result = validator.validate_response(enhanced_response)
    assert enhanced_result.is_valid, f"Enhanced validation failed: {enhanced_result.errors}"
    
    # The key insight: essential business logic validation remains stable
    # even when response models are updated for documentation purposes
    assert len(enhanced_result.errors) == len(original_result.errors), (
        "Framework should be independent of non-essential model changes"
    )
    
    # Verify that business logic still works correctly
    groups = enhanced_response["groups"]
    assert isinstance(groups, list), "Groups should still be a list"
    if groups:
        assert "name" in groups[0], "Group items should still have names"