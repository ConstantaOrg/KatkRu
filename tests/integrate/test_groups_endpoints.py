import pytest

from tests.utils.api_response_validator import APIResponseValidator, ValidationRule


@pytest.mark.asyncio
async def test_groups_get(client, seed_info):
    """Test groups get endpoint validates actual data structure and business logic."""
    # Create validator for groups response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("groups", list, required=True))
    
    resp = await client.post(
        "/api/v1/private/groups/get",
        params={"bid": seed_info["building_id"], "limit": 10, "offset": 0},
    )
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: groups should contain expected data
    groups = data["groups"]
    assert isinstance(groups, list), "Groups should be a list"
    
    # Validate business logic: should contain the expected group
    group_names = [group.get("name") for group in groups if isinstance(group, dict)]
    assert "GR1" in group_names, "Expected group 'GR1' should be present in response"
    
    # Validate essential fields exist in group records
    for group in groups:
        if isinstance(group, dict):
            assert "name" in group, "Group record should have 'name' field"


@pytest.mark.asyncio
async def test_groups_add(client, pg_pool, seed_info):
    """Test groups add endpoint validates actual data processing logic."""
    # Create validator for add response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("group_id", int, required=True))
    
    resp = await client.post(
        "/api/v1/private/groups/add",
        json={"group_name": "GR2", "building_id": seed_info["building_id"]},
    )
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: group_id should be present and valid
    new_id = data["group_id"]
    assert isinstance(new_id, int), "group_id should be an integer"
    assert new_id > 0, "group_id should be positive"
    
    # Validate actual database changes (business logic verification)
    async with pg_pool.acquire() as conn:
        exists = await conn.fetchval("SELECT count(*) FROM groups WHERE id=$1 AND name='GR2'", new_id)
    assert exists == 1, "New group should exist in database with correct name"


@pytest.mark.asyncio
async def test_groups_update(client, pg_pool, seed_info):
    """Test groups update endpoint validates actual data processing logic."""
    # Note: This endpoint may not return structured data, so we validate status code and business logic
    
    # ожидаем деактивации группы
    resp = await client.put(
        "/api/v1/private/groups/update",
        json={"set_as_active": [], "set_as_deprecated": [seed_info["group_id"]]},
    )
    
    # Validate response status
    assert resp.status_code == 200, "Groups update should return 200 status"
    
    # Validate actual database changes (business logic verification)
    async with pg_pool.acquire() as conn:
        is_active = await conn.fetchval("SELECT is_active FROM groups WHERE id=$1", seed_info["group_id"])
    assert is_active is False, "Group should be deactivated after update"
