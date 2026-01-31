import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from docx import Document

from tests.utils.api_response_validator import APIResponseValidator, ValidationRule, EndpointValidator

BASE_DIR = Path(__file__).resolve().parents[2]
DOCX_PATH = BASE_DIR / "ttable_25-26.docx"


def _build_simple_doc(path: Path, group_name: str, discipline: str, teacher: str, aud: str, day_label: str = "пн"):
    doc = Document()
    table = doc.add_table(rows=2, cols=4)
    # Header
    hdr = table.rows[0].cells
    hdr[0].text = "День"
    hdr[1].text = "№"
    hdr[2].text = group_name
    hdr[3].text = "Ауд"
    # Row 1
    row = table.rows[1].cells
    row[0].text = day_label
    row[1].text = "1"
    row[2].text = f"{discipline}\n{teacher}"
    row[3].text = aud
    doc.save(path)


@pytest.mark.asyncio
async def test_healthcheck(client):
    resp = await client.post("/api/v1/healthcheck")
    assert resp.status_code == 200
    assert resp.json().get("status") == True


@pytest.mark.asyncio
async def test_cards_history(client, seed_info):
    """Test cards history endpoint validates actual data structure."""
    # Create validator for history response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("history", list, required=True))
    
    resp = await client.get(
        "/api/v1/private/n8n_ui/cards/history",
        params={"sched_ver_id": seed_info["ttable_id"], "group_id": seed_info["group_id"]},
    )
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: history should contain expected data
    history = data["history"]
    assert len(history) == 1, "Expected exactly one history record"
    
    row = history[0]
    # Validate essential fields exist with correct business logic
    assert "status_id" in row, "History record should have status_id"
    assert "is_current" in row, "History record should have is_current"
    assert "user_name" in row, "History record should have user_name"
    
    # Validate business logic values
    assert row["status_id"] == seed_info["cards_statuses"]["edited"], "Status should be 'edited'"
    assert row["is_current"] is True, "Record should be current"
    assert row["user_name"] == "Test User", "User name should match expected value"


@pytest.mark.asyncio
async def test_cards_content(client, seed_info):
    """Test cards content endpoint validates actual data structure."""
    # Create validator for content response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("card_content", list, required=True))
    
    resp = await client.get(
        "/api/v1/private/n8n_ui/cards/content",
        params={"card_hist_id": seed_info["hist_id"]},
    )
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: content should contain expected data
    content = data["card_content"]
    assert len(content) == 1, "Expected exactly one content record"
    
    row = content[0]
    # Validate essential fields exist
    assert "position" in row, "Content record should have position"
    assert "aud" in row, "Content record should have aud"
    assert "discipline_title" in row, "Content record should have discipline_title"
    assert "teacher_name" in row, "Content record should have teacher_name"
    
    # Validate business logic values
    assert row["position"] == 1, "Position should be 1"
    assert row["aud"] == "101", "Aud should be '101'"
    assert row["discipline_title"] == "Math", "Discipline should be 'Math'"
    assert row["teacher_name"] == "Иванов И.И.", "Teacher name should match expected value"


@pytest.mark.asyncio
async def test_cards_get_by_id(client, seed_info):
    resp = await client.post(
        "/api/v1/private/n8n_ui/cards/get_by_id",
        json={"card_hist_id": seed_info["hist_id"]},
    )
    assert resp.status_code == 200
    payload = resp.json()["ext_card"]
    assert payload[0]["teacher_id"] == seed_info["teacher_id"]
    assert payload[0]["aud"] == "101"


@pytest.mark.asyncio
async def test_cards_accept(client, seed_info, pg_pool):
    resp = await client.put(
        "/api/v1/private/n8n_ui/cards/accept",
        json={"card_hist_id": seed_info["hist_id"]},
    )
    assert resp.status_code == 200
    async with pg_pool.acquire() as conn:
        status_row = await conn.fetchrow(
            "SELECT status_id FROM cards_states_history WHERE id=$1",
            seed_info["hist_id"],
        )
    assert status_row["status_id"] == seed_info["cards_statuses"]["accepted"]  # accepted


@pytest.mark.asyncio
async def test_timetable_standard_import(client, pg_pool, seed_info):
    with NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    _build_simple_doc(tmp_path, "GR1", "Math", "Иванов И.И.", "201", day_label="пн")

    with tmp_path.open("rb") as f:
        files = {"file_obj": (tmp_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        resp = await client.post(
            "/api/v1/private/timetable/standard/import",
            params={"smtr": "1", "bid": seed_info["building_id"]},
            files=files,
        )
    tmp_path.unlink(missing_ok=True)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("success") is True
    new_id = payload["ttable_ver_id"]["id"] if isinstance(payload["ttable_ver_id"], dict) else payload["ttable_ver_id"]
    async with pg_pool.acquire() as conn:
        cnt = await conn.fetchval("SELECT count(*) FROM ttable_versions WHERE id=$1", new_id)
    assert cnt == 1


@pytest.mark.asyncio
async def test_std_ttable_get_all_creates_snapshot(client, seed_info, pg_pool):
    """Test std_ttable get_all endpoint validates actual data processing logic."""
    # Create validator for lessons response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("lessons", list, required=True))
    
    async with pg_pool.acquire() as conn:
        new_sched_id = await conn.fetchval(
            """
            INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited)
            VALUES (CURRENT_DATE, $1, $2, $3, 'standard', false)
            RETURNING id
            """,
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"],
        )

    body = {
        "building_id": seed_info["building_id"],
        "week_day": 1,
        "ttable_id": new_sched_id,
    }
    resp = await client.post("/api/v1/private/n8n_ui/std_ttable/get_all", json=body)
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: lessons should contain expected data
    lessons = data["lessons"]
    assert len(lessons) == 1, "Expected exactly one lesson record"
    
    item = lessons[0]
    # Validate essential fields exist
    assert "status_card" in item, "Lesson should have status_card"
    assert "position" in item, "Lesson should have position"
    assert "title" in item, "Lesson should have title"
    
    # Validate business logic values
    assert item["status_card"] == seed_info["cards_statuses"]["draft"], "Status should be 'draft'"
    assert item["position"] == 1, "Position should be 1"
    assert item["title"] == "Math", "Title should be 'Math'"

    # Validate actual database changes (business logic verification)
    async with pg_pool.acquire() as conn:
        current = await conn.fetch("SELECT id, is_current FROM cards_states_history WHERE sched_ver_id=$1", new_sched_id)
    
    assert len(current) == 1, "Expected exactly one card state history record"
    assert current[0]["is_current"] is True, "Card state should be current"


@pytest.mark.asyncio
async def test_current_ttable_get_all_returns_active_cards(client, seed_info):
    """Test current_ttable get_all endpoint validates actual data processing logic."""
    # Create validator for lessons response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("lessons", list, required=True))
    
    resp = await client.post(
        "/api/v1/private/n8n_ui/current_ttable/get_all",
        json={"ttable_id": seed_info["ttable_id"]},
    )
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: lessons should contain expected data
    lessons = data["lessons"]
    assert len(lessons) == 1, "Expected exactly one lesson record"
    
    row = lessons[0]
    # Validate essential fields exist
    assert "card_hist_id" in row, "Lesson should have card_hist_id"
    assert "status_card" in row, "Lesson should have status_card"
    assert "title" in row, "Lesson should have title"
    
    # Validate business logic values
    assert row["card_hist_id"] == seed_info["hist_id"], "Card hist ID should match expected"
    assert row["status_card"] == seed_info["cards_statuses"]["edited"], "Status should be 'edited'"
    assert row["title"] == "Math", "Title should be 'Math'"


@pytest.mark.asyncio
async def test_cards_save_creates_new_version(client, seed_info, pg_pool):
    """Test cards save endpoint validates actual data processing logic."""
    # Create validator for cards save endpoint
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("success", bool, required=True))
    validator.add_rule(ValidationRule("new_card_hist_id", int, required=False))
    
    payload = {
        "card_hist_id": seed_info["hist_id"],
        "ttable_id": seed_info["ttable_id"],
        "lessons": [
            {
                "position": 2,
                "discipline_id": seed_info["discipline_id"],
                "teacher_id": seed_info["teacher_id"],
                "aud": "202",
                "is_force": False,
            }
        ],
    }
    resp = await client.post("/api/v1/private/n8n_ui/cards/save", json=payload)
    
    # Validate response using independent validator
    assert resp.status_code == 200
    data = resp.json()
    
    # Use validator to check response structure
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: success should be True for valid save
    assert data["success"] is True, "Expected successful save operation"
    
    # Validate business logic: new_card_hist_id should be present and different
    assert "new_card_hist_id" in data, "Expected new_card_hist_id in successful response"
    new_hist_id = data["new_card_hist_id"]
    assert isinstance(new_hist_id, int), "new_card_hist_id should be an integer"
    assert new_hist_id != seed_info["hist_id"], "new_card_hist_id should be different from original"

    # Validate actual database changes (business logic verification)
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT csd.card_hist_id, csh.is_current, csd.aud "
            "FROM cards_states_details csd "
            "JOIN cards_states_history csh ON csh.id = csd.card_hist_id "
            "WHERE csh.sched_ver_id=$1",
            seed_info["ttable_id"],
        )
    
    # Verify business logic: new record exists and is current
    new_record_exists = any(r["card_hist_id"] == new_hist_id for r in rows)
    assert new_record_exists, "New card history record should exist in database"
    
    correct_aud_and_current = any(r["aud"] == "202" and r["is_current"] for r in rows)
    assert correct_aud_and_current, "New record should have correct aud and be current"


@pytest.mark.asyncio
async def test_cards_save_conflict_due_to_unique_index(client, seed_info):
    """Test cards save endpoint handles conflicts correctly."""
    # Create validator for conflict response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("success", bool, required=True))
    validator.add_rule(ValidationRule("conflicts", dict, required=False))
    
    payload = {
        "card_hist_id": seed_info["hist_id"],
        "ttable_id": seed_info["ttable_id"],
        "lessons": [
            {
                "position": 1,  # конфликтует с существующей записью
                "discipline_id": seed_info["discipline_id"],
                "teacher_id": seed_info["teacher_id"],
                "aud": "303",
                "is_force": False,
            }
        ],
    }
    resp = await client.post("/api/v1/private/n8n_ui/cards/save", json=payload)
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: conflict should result in success=False
    assert data["success"] is False, "Expected conflict to result in success=False"
    
    # Validate business logic: conflicts should be present when success=False
    assert "conflicts" in data, "Expected conflicts field when save fails due to conflict"


@pytest.mark.asyncio
async def test_cards_save_conflict_even_with_force(client, seed_info):
    """Test cards save endpoint handles force flag correctly."""
    # Create validator for force save response
    validator = APIResponseValidator(strict_mode=False)
    validator.add_rule(ValidationRule("success", bool, required=True))
    validator.add_rule(ValidationRule("new_card_hist_id", int, required=False))
    
    payload = {
        "card_hist_id": seed_info["hist_id"],
        "ttable_id": seed_info["ttable_id"],
        "lessons": [
            {
                "position": 1,  # тот же слот, но is_force=True
                "discipline_id": seed_info["discipline_id"],
                "teacher_id": seed_info["teacher_id"],
                "aud": "304",
                "is_force": True,
            }
        ],
    }
    resp = await client.post("/api/v1/private/n8n_ui/cards/save", json=payload)
    
    # Validate response structure
    assert resp.status_code == 200
    data = resp.json()
    
    validation_result = validator.validate_response(data)
    assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    # Validate business logic: force flag should allow save despite conflict
    assert data["success"] is True, "Expected force flag to allow save despite conflict"
    
    # Validate business logic: new_card_hist_id should be present for successful save
    assert "new_card_hist_id" in data, "Expected new_card_hist_id for successful force save"
    assert isinstance(data.get("new_card_hist_id"), int), "new_card_hist_id should be integer"

