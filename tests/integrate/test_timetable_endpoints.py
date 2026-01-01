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


