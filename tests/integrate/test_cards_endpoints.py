import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import date
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
    assert resp.json().get("status") == "ok"


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
    assert row["status_id"] == 2
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
    assert status_row["status_id"] == 1  # accepted


@pytest.mark.asyncio
async def test_timetable_standard_import(client, pg_pool):
    with NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    _build_simple_doc(tmp_path, "GR1", "Math", "Иванов И.И.", "201", day_label="пн")

    with tmp_path.open("rb") as f:
        files = {"file_obj": (tmp_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        resp = await client.post(
            "/api/v1/private/timetable/standard/import",
            params={"smtr": "1", "bid": 1},
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
async def test_timetable_get(client):
    body = {"building_id": 1, "group": "GR1"}
    resp = await client.post("/api/v1/public/timetable/get", json=body)
    assert resp.status_code == 200
    assert "schedule" in resp.json()
