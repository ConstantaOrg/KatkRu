import re
from typing import Literal

from docx import Document
from collections import defaultdict

day_weeks = {
    "понедельник": 0,
    "пн": 0,
    "вторник": 1,
    "вт": 1,
    "среда": 2,
    "ср": 2,
    "четверг": 3,
    "чт": 3,
    "пятница": 4,
    "пт": 4,
    "суббота": 5,
    "суббта": 5,
    "сб": 5,
}


def normalize_day_name(day: str) -> str:
    return day.replace('.', '').strip().lower()


def day_to_index(day: str) -> int:
    norm = normalize_day_name(day)
    if norm not in day_weeks:
        raise ValueError(f"Unknown day name: {day}")
    return day_weeks[norm]


def extract_teachers(text: str) -> list[str]:
    teach_regexp = re.compile(
        r'([А-ЯЁ][а-яё]+)\s+([А-ЯЁ]\.[А-ЯЁ]\.)'
    )
    if not text:
        return []

    matches = teach_regexp.findall(text)
    return [f"{surname} {initials}" for surname, initials in matches]



def std_ttable_doc_processer( doc_file, semester: Literal[1, 2]):
    schedule = defaultdict(lambda: defaultdict(dict))
    doc = Document(doc_file)

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
                raw_day = "".join(cells[0].split("\n"))
                current_day = normalize_day_name(raw_day)


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


async def raw_values2db_ids_handler(std_ttable: dict, sched_ver_id: int, conn_obj): #conn_obj: TimetableQueries
    disciplines = await conn_obj.discipline_ids()
    teachers = await conn_obj.teacher_ids()
    groups = await conn_obj.group_ids()

    disp2id = {rec['title']: rec['id'] for rec in disciplines}
    t2id = {rec['fio']: rec['id'] for rec in teachers}
    gr2id = {rec['name']: rec['id'] for rec in groups}


    "Фио учителей, названия предметов -> teacher_id, discipline_id"
    for group in std_ttable.keys():
        for w_day in std_ttable[group].keys():
            for pair, content in std_ttable[group][w_day].items():
                new_ts = []
                for t in content['teachers']:
                    new_ts.append(t2id[t])
                content['teachers'] = new_ts
                content['discipline'] = disp2id[content['discipline']]

    normalized_ttable = {}
    "Названия групп -> group_id"
    for group in std_ttable.keys():
        normalized_ttable[gr2id[group]] = std_ttable[group]

    "Распаковка и формирование кортежей"
    lessons_to_insert = []
    for group_id_str, days in normalized_ttable.items():
        group_id = int(group_id_str)

        for day_name, pairs in days.items():
            day_index = day_to_index(day_name)
            for position_str, payload in pairs.items():
                position = int(position_str)
                discipline_id = payload["discipline"]
                aud = payload.get("auditory").split(',')
                teachers = payload.get("teachers", [])

                for idx, teacher_id in enumerate(teachers):
                    lessons_to_insert.append(
                        (
                            sched_ver_id,
                            group_id,
                            discipline_id,
                            position,
                            aud[idx].strip(),
                            teacher_id,
                            day_index
                        )
                    )
    return lessons_to_insert
