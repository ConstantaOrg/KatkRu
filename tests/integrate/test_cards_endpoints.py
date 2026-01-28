import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from docx import Document

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
    resp = await client.get(
        "/api/v1/private/n8n_ui/cards/history",
        params={"sched_ver_id": seed_info["ttable_id"], "group_id": seed_info["group_id"]},
    )
    assert resp.status_code == 200
    history = resp.json()["history"]
    assert len(history) == 1
    row = history[0]
    assert row["status_id"] == seed_info["cards_statuses"]["edited"]
    assert row["is_current"] is True
    assert row["user_name"] == "Test User"


@pytest.mark.asyncio
async def test_cards_content(client, seed_info):
    resp = await client.get(
        "/api/v1/private/n8n_ui/cards/content",
        params={"card_hist_id": seed_info["hist_id"]},
    )
    assert resp.status_code == 200
    content = resp.json()["card_content"]
    assert len(content) == 1
    row = content[0]
    assert row["position"] == 1
    assert row["aud"] == "101"
    assert row["discipline_title"] == "Math"
    assert row["teacher_name"] == "Иванов И.И."


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
    assert resp.status_code == 200
    lessons = resp.json()["lessons"]
    assert len(lessons) == 1
    item = lessons[0]
    assert item["status_card"] == seed_info["cards_statuses"]["draft"]
    assert item["position"] == 1
    assert item["title"] == "Math"

    async with pg_pool.acquire() as conn:
        current = await conn.fetch("SELECT id, is_current FROM cards_states_history WHERE sched_ver_id=$1", new_sched_id)
    assert len(current) == 1
    assert current[0]["is_current"] is True


@pytest.mark.asyncio
async def test_current_ttable_get_all_returns_active_cards(client, seed_info):
    resp = await client.post(
        "/api/v1/private/n8n_ui/current_ttable/get_all",
        json={"ttable_id": seed_info["ttable_id"]},
    )
    assert resp.status_code == 200
    lessons = resp.json()["lessons"]
    assert len(lessons) == 1
    row = lessons[0]
    assert row["card_hist_id"] == seed_info["hist_id"]
    assert row["status_card"] == seed_info["cards_statuses"]["edited"]
    assert row["title"] == "Math"


@pytest.mark.asyncio
async def test_cards_save_creates_new_version(client, seed_info, pg_pool):
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    new_hist_id = data["new_card_hist_id"]
    assert isinstance(new_hist_id, int)
    assert new_hist_id != seed_info["hist_id"]

    async with pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT csd.card_hist_id, csh.is_current, csd.aud "
            "FROM cards_states_details csd "
            "JOIN cards_states_history csh ON csh.id = csd.card_hist_id "
            "WHERE csh.sched_ver_id=$1",
            seed_info["ttable_id"],
        )
    assert any(r["card_hist_id"] == new_hist_id for r in rows)
    assert any(r["aud"] == "202" and r["is_current"] for r in rows)


@pytest.mark.asyncio
async def test_cards_save_conflict_due_to_unique_index(client, seed_info):
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "conflicts" in data


@pytest.mark.asyncio
async def test_cards_save_conflict_even_with_force(client, seed_info):
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data.get("new_card_hist_id"), int)

