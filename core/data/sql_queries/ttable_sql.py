import datetime
from types import NoneType

from asyncpg import Connection

from core.api.timetable.ttable_parser import raw_values2db_ids_handler
from core.utils.anything import TimetableTypes, TimetableVerStatuses
from core.utils.logger import log_event


class TimetableQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_ttable(self, building_id: int, group: str | list[str] | None, date_start, date_end):
        date_filter = 't_v.schedule_date BETWEEN $4 AND $5'
        date_args = (date_start, date_end)
        if not date_end:
            date_filter = 't_v.schedule_date = $4'
            date_args = (date_start,)

        group_filter = 'AND s_d.group_id = (SELECT g.id FROM groups g WHERE g.is_active = true AND g.name = $2)'
        if not isinstance(group, str):
            "Если указано несколько групп"
            group_filter = 'AND s_d.group_id IN (SELECT id FROM groups WHERE is_active = true AND name IN ANY($2))'
            if isinstance(group, NoneType):
                group_filter = ''

        query = f'''
        SELECT l.position, dp.title, t.fio, l.aud FROM lessons l
        JOIN disciplines dp ON dp.id = l.discipline_id
        JOIN teachers t ON t.id = l.teacher_id
        WHERE l.sched_id IN (
            SELECT s_d.id FROM schedule_days s_d
            JOIN ttable_versions t_v ON t_v.id = s_d.sched_ver_id AND t_v.status_id = $3
            WHERE t_v.building_id = $1
            {group_filter}
            AND {date_filter}
        )
        '''
        res = await self.conn.fetch(query, building_id, group, TimetableVerStatuses.accepted, *date_args)
        return res

    async def teacher_ids(self):
        teachers = await self.conn.fetch('SELECT id, fio FROM teachers')
        return teachers

    async def discipline_ids(self):
        disciplines = await self.conn.fetch('SELECT id, title FROM disciplines')
        return disciplines

    async def group_ids(self):
        groups = await self.conn.fetch('SELECT id, name FROM groups')
        return groups

    async def import_raw_std_ttable(self, std_ttable: dict, building_id: int, user_id: int):
        """"""
        "Проводим транзакцию"
        await self.conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED')


        "Фиксируем импорт расписания"
        ttable_ver_id = (await self.conn.fetchrow(
            'INSERT INTO ttable_versions (status_id, building_id, user_id, type) VALUES ($1, $2, $3, $4) RETURNING id',
            TimetableVerStatuses.pending, building_id, user_id, TimetableTypes.standard
        ))['id']
        lessons_to_insert = await raw_values2db_ids_handler(std_ttable, ttable_ver_id, self)
        log_event(f"Зафиксировали импорт №{ttable_ver_id}. Вливаем данные")

        await self.conn.copy_records_to_table(
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
        await self.conn.execute('COMMIT')
        log_event(f"Влили данные в расписание №{ttable_ver_id}. Транзакция успешна")
        return ttable_ver_id

    async def create(self, building_id: int, date: datetime.date | None, type_: str, status: int, user_id: int):
        query = 'INSERT INTO ttable_versions (building_id, schedule_date, type, status_id, user_id) VALUES ($1, $2, $3, $4, $5) RETURNING id'
        res = await self.conn.fetchrow(query, building_id, date, type_, status, user_id)
        return res['id']