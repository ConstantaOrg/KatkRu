import pytest
from datetime import date

from core.utils.anything import TimetableVerStatuses
from tests.utils.api_response_validator import APIResponseValidator, ValidationRule


@pytest.mark.asyncio
async def test_public_timetable_get(client, pg_pool, seed_info):
    """Test public timetable get endpoint validates actual data processing and handles different scenarios."""
    # Create validator for timetable response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("schedule", list, required=True))
    
    async with pg_pool.acquire() as conn:
        # Update ttable_versions to be committed so it appears in public API
        await conn.execute(
            """
            UPDATE ttable_versions
            SET is_commited = true
            WHERE id = $1
            """,
            seed_info["ttable_id"],
        )
        
        # Update cards_states_history status to 'accepted' so it appears in public API
        await conn.execute(
            """
            UPDATE cards_states_history
            SET status_id = $2
            WHERE id = $1
            """,
            seed_info["hist_id"],
            seed_info["cards_statuses"]["accepted"],
        )
        
        # Update cards_states_details with test data
        await conn.execute(
            """
            UPDATE cards_states_details
            SET aud = '201'
            WHERE card_hist_id = $1
            """,
            seed_info["hist_id"],
        )

    body = {"group": "GR1", "date": date.today().isoformat()}
    resp = await client.post("/api/v1/public/ttable/get", json=body)

    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: schedule should contain expected data
    schedule = data["schedule"]
    assert isinstance(schedule, list), "Schedule should be a list"
    assert len(schedule) >= 1, "Expected at least one schedule record"
    
    # Find the record with aud='201' (the one we updated)
    updated_row = next((row for row in schedule if row.get("aud") == "201"), None)
    assert updated_row is not None, "Should find the updated record with aud='201'"
    
    # Validate essential fields exist
    assert "position" in updated_row, "Schedule record should have position field"
    assert "aud" in updated_row, "Schedule record should have aud field"
    
    # Validate business logic values
    assert updated_row["position"] == 1, "Position should be 1"
    assert updated_row["aud"] == "201", "Aud should be '201' (updated value)"


@pytest.mark.asyncio
async def test_public_timetable_get_empty_result(client, seed_info):
    """Test timetable endpoint handles empty result scenarios correctly."""
    # Create validator for empty timetable response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("schedule", list, required=True))
    
    # Request timetable for non-existent group
    body = {"group": "NONEXISTENT"}
    resp = await client.post("/api/v1/public/ttable/get", json=body)

    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: empty schedule should still be a valid list
    schedule = data["schedule"]
    assert isinstance(schedule, list), "Schedule should be a list even when empty"
    assert len(schedule) == 0, "Schedule should be empty for non-existent group"


@pytest.mark.asyncio
async def test_public_timetable_get_different_query_parameters(client, seed_info):
    """Test timetable endpoint handles different query parameters correctly."""
    # Create validator for timetable response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("schedule", list, required=True))
    
    # Test with different parameter combinations
    test_cases = [
        {"group": "GR1"},
        {"group": "GR1", "week_day": 1},
    ]
    
    for body in test_cases:
        resp = await client.post("/api/v1/public/ttable/get", json=body)
        
        # Validate response structure for each parameter combination
        assert resp.status_code == 200, f"Failed for parameters: {body}"
        data = resp.json()
        
        validation_result = validator.validate_response(data)
        assert validation_result.is_valid, f"Validation errors for {body}: {validation_result.errors}"
        
        # Validate business logic: schedule should always be a list
        schedule = data["schedule"]
        assert isinstance(schedule, list), f"Schedule should be a list for parameters: {body}"
