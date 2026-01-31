import pytest

from tests.utils.api_response_validator import APIResponseValidator, ValidationRule


@pytest.mark.asyncio
async def test_specialties_all(client):
    """Test specialties all endpoint validates actual data structure and business logic."""
    # Create validator for specialties response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("specialties", list, required=True))
    
    resp = await client.post("/api/v1/public/specialties/all", json={"limit": 10, "offset": 0})
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: specialties should be a list
    specialties = data["specialties"]
    assert isinstance(specialties, list), "Specialties should be a list"


@pytest.mark.asyncio
async def test_specialties_get(client, pg_pool):
    """Test specialties get endpoint validates actual data structure and business logic."""
    # Create validator for specialty response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("speciality", dict, required=True))
    
    # ensure at least one specialty exists
    async with pg_pool.acquire() as conn:
        spec_id = await conn.fetchval(
            "INSERT INTO specialties (spec_code, title, learn_years, description, full_time, free_form, evening_form, cost_per_year) "
            "VALUES ('99.99', 'SpecTest', 4, 'desc', true, false, false, 10000) RETURNING id"
        )
    
    resp = await client.get(f"/api/v1/public/specialties/{spec_id}")
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: specialty should contain expected data
    specialty = data["speciality"]
    assert isinstance(specialty, dict), "Speciality should be a dictionary"
    
    # Validate essential fields exist
    assert "spec_code" in specialty, "Specialty should have spec_code field"
    assert "description" in specialty, "Specialty should have description field"
    
    # Validate business logic values
    assert specialty["spec_code"] == "99.99", "Spec code should match expected value"
    assert specialty["description"] == "desc", "Description should match expected value"
