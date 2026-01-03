from datetime import datetime, timedelta
import json

from fastapi import APIRouter

from core.config_dir.config import WORKDIR
from core.data.postgre import PgSqlDep

router = APIRouter(prefix='/sched_layout', tags=['No Need API'])

@router.get('/fill_groups')
async def fill_groups(db: PgSqlDep):
    """
    Достаём ключи из словаря просто
    """
    with open(WORKDIR / 'ttable_25-26_sem1.json', 'rb') as f:
        ttable = json.load(f)

    await db.conn.execute('INSERT INTO groups (building_id, name) SELECT $1, group_name FROM UNNEST($2::text[]) AS t(group_name)', 1, tuple(ttable.keys()))

    return {'success': True}


@router.get('/fill_disciplines')
async def fill_disciplines(db: PgSqlDep):
    with open(WORKDIR / 'ttable_25-26_sem2.json', 'rb') as f:
        ttable = json.load(f)

    discps = set()
    for group in ttable.keys():
        for w_day in ttable[group].keys():
            for pair, content in ttable[group][w_day].items():
                discps.add(content['discipline'])

    res = await db.conn.execute('INSERT INTO disciplines (title) SELECT * FROM UNNEST($1::text[]) ON CONFLICT DO NOTHING', tuple(discps))
    return {'success': True, 'res': res}


@router.get('/fill_teachers')
async def fill_disciplines(db: PgSqlDep):
    with open(WORKDIR / 'ttable_25-26_sem1.json', 'rb') as f:
        ttable = json.load(f)

    teachers = set()
    for group in ttable.keys():
        for w_day in ttable[group].keys():
            for pair, content in ttable[group][w_day].items():
                for t in content['teachers']:
                    teachers.add(t)

    res = await db.conn.execute('INSERT INTO teachers (fio) SELECT * FROM UNNEST($1::text[]) ON CONFLICT DO NOTHING', tuple(teachers))
    return {'success': True, 'res': res}


@router.post('/bind_ids-teachers_disciplines')
async def bind_ids(db: PgSqlDep):
    teachers = await db.conn.fetch('SELECT * FROM teachers')
    disciplines = await db.conn.fetch('SELECT * FROM disciplines')

    t2id = {rec['fio']: rec['id'] for rec in teachers}
    disp2id = {rec['title']: rec['id'] for rec in disciplines}

    with open(WORKDIR / 'ttable_25-26_sem1.json', 'rb') as f:
        ttable = json.load(f)

    for group in ttable.keys():
        for w_day in ttable[group].keys():
            for pair, content in ttable[group][w_day].items():
                new_ts = []
                for t in content['teachers']:
                    new_ts.append(t2id[t])
                content['teachers'] = new_ts
                content['discipline'] = disp2id[content['discipline']]

    return ttable

@router.post('/deprecated/create_sched_days')
async def create_sched_days(db: PgSqlDep):
    with open(WORKDIR / 'ttable_25-26_ids_bind-teachers_disciplines.json', 'rb') as f:
        ttable = json.load(f)

    start_week = datetime.now().date() - timedelta(days=2)
    sched_days = []
    for group in ttable.keys():
        for day in range(6):
            sched_days.append((group, start_week + timedelta(days=day)))

    groups, dates = zip(*sched_days)
    db_groups = await db.conn.fetch('SELECT id, name FROM groups')
    gr2id = {rec['name']: rec['id'] for rec in db_groups}
    groups = tuple(gr2id[group] for group in groups)

    res = await db.conn.execute('INSERT INTO schedule_days (group_id, building_id, date) SELECT g_id, $1, dt FROM UNNEST($2::int[], $3::date[]) AS t(g_id, dt)', 1, groups, dates)
    return {'success': True, 'res': res}


@router.post('/bind_groups-ids')
async def bind_groups_ids(db: PgSqlDep):
    with open(WORKDIR / 'ttable_25-26_ids_bind-teachers_disciplines.json', 'rb') as f:
        ttable = json.load(f)
    db_groups = await db.conn.fetch('SELECT id, name FROM groups')
    gr2id = {rec['name']: rec['id'] for rec in db_groups}
    new_ttable = {}
    for group in ttable.keys():
        new_ttable[gr2id[group]] = ttable[group]

    return new_ttable


@router.post('/deprecated-19-12-25/accept_pairs_std_ttable_on_week')
async def create_std_ttable_on_week(db: PgSqlDep):
    with open(WORKDIR / 'ttable_25-26_normalize_t_gr_d_ids.json', 'rb') as f:
        ttable = json.load(f)

    rows = await db.conn.fetch("SELECT id, group_id FROM schedule_days ORDER BY id ASC")
    sched_map: dict[int, list[int]] = {}

    for r in rows:
        sched_map.setdefault(r["group_id"], []).append(r["id"])

    lessons_to_insert = []

    for group_id_str, days in ttable.items():
        group_id = int(group_id_str)

        sched_ids = sched_map.get(group_id)
        if not sched_ids:
            continue

        for day_index, (_day_name, pairs) in enumerate(days.items()):
            if day_index >= len(sched_ids):
                break

            sched_id = sched_ids[day_index]

            for position_str, payload in pairs.items():
                position = int(position_str)
                discipline_id = payload["discipline"]
                aud = payload.get("auditory").split(',')
                teachers = payload.get("teachers", [])

                for idx, teacher_id in enumerate(teachers):
                    lessons_to_insert.append(
                        (
                            sched_id,
                            discipline_id,
                            position,
                            aud[idx].strip(),
                            teacher_id
                        )
                    )

    if lessons_to_insert:
        await db.conn.executemany(
            """
            INSERT INTO lessons
                (sched_id, discipline_id, position, aud, teacher_id)
            VALUES ($1, $2, $3, $4, $5)
            """,
            lessons_to_insert)

    return {"success": True, "inserted": len(lessons_to_insert)}


@router.post('/accept_pairs_std_ttable_on_week')
async def create_std_ttable_on_week(db: PgSqlDep):
    with open(WORKDIR / 'ttable_25-26_normalize_t_gr_d_ids.json', 'rb') as f:
        ttable = json.load(f)

    lessons_to_insert = []

    for group_id_str, days in ttable.items():
        group_id = int(group_id_str)

        for day_index, (_day_name, pairs) in enumerate(days.items()):
            for position_str, payload in pairs.items():
                position = int(position_str)
                discipline_id = payload["discipline"]
                aud = payload.get("auditory").split(',')
                teachers = payload.get("teachers", [])

                for idx, teacher_id in enumerate(teachers):
                    lessons_to_insert.append(
                        (
                            2,
                            group_id,
                            discipline_id,
                            position,
                            aud[idx].strip(),
                            teacher_id,
                            day_index
                        )
                    )

    if lessons_to_insert:
        await db.conn.copy_records_to_table(
            'std_ttable',
            records=lessons_to_insert,
            columns=[
                'sched_ver_id',
                'group_id',
                'discipline_id',
                'position',
                'aud',
                'teacher_id',
                'week_day'
            ]
        )