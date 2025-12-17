import re
from pathlib import Path
from typing import Any, Literal

from docx import Document
from collections import defaultdict


def extract_teachers(text: str) -> list[str]:
    teach_regexp = re.compile(
        r'([А-ЯЁ][а-яё]+)\s+([А-ЯЁ]\.[А-ЯЁ]\.)'
    )
    if not text:
        return []

    matches = teach_regexp.findall(text)
    return [f"{surname} {initials}" for surname, initials in matches]



def ttable_doc_processer(semester: Literal[1, 2], doc_path: Path | str = "ttable_25-26.docx") -> dict[Any, dict[Any, dict]]:
    schedule = defaultdict(lambda: defaultdict(dict))
    doc = Document(doc_path)

    for table in doc.tables:
        header = [cell.text.strip() for cell in table.rows[0].cells]

        groups = []
        for i in range(2, len(header), 3):
            if header[i]:
                groups.append((header[i], i))

        current_day = None

        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]

            if cells[0]:
                current_day = "".join(cells[0].split("\n"))


            for group, idx in groups:
                if idx >= len(cells):
                    continue

                subject = cells[idx]
                auditory = cells[idx + 1] if idx + 1 < len(cells) else ""
                pair_num = cells[idx - 1]

                if not subject or not pair_num:
                    continue

                pair_num = int(pair_num)

                "Случай с знаменателем"
                pair_keys = schedule[group][current_day].keys()
                if pair_num in pair_keys and semester == 1:
                    continue

                "Прочие нужные данные"
                parts = subject.split("\n")
                discipline = parts[0].replace('  ', ' ') # иногда бывают пробелы X2

                teachers = []
                "1. Пробуем явную строку преподавателя"
                if len(parts) > 1:
                    teachers = extract_teachers(parts[1])
                "2. Fallback — ищем во всём тексте"
                if not teachers:
                    "Убираем ФИО учителей из названия дисциплины"
                    teachers = extract_teachers(subject) # достаём список учителей
                    discipline_wo_teachers = discipline.split(' ')[:-(len(teachers)*2)] # Убираем инициалы и фамилии
                    discipline = ' '.join(discipline_wo_teachers)

                schedule[group.upper()][current_day][pair_num] = {
                    "discipline": discipline,
                    "auditory": auditory.replace("\n", ", "),
                    "teachers": teachers,
                }

    return schedule