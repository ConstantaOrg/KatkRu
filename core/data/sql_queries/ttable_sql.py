import datetime
from types import NoneType

from asyncpg import Connection

from core.api.timetable.ttable_parser import raw_values2db_ids_handler
from core.utils.anything import TimetableTypes, TimetableVerStatuses, CardsStatesStatuses
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

    async def base_groups(self, building_id: int):
        query = 'SELECT id FROM groups WHERE is_active = true AND building_id = $1'
        res = await self.conn.fetch(query, building_id)
        return res

    async def ttable_ver_groups(self, sched_ver_id: int):
        query = '''
        SELECT DISTINCT group_id FROM cards_states_history
        WHERE sched_ver_id = $1
          AND status_id IN ($2, $3)
        '''
        res = await self.conn.fetch(query, sched_ver_id, CardsStatesStatuses.accepted, CardsStatesStatuses.draft)
        return res

    async def pre_commit_version(self, cur_ttable_id: int):
        query = '''
        WITH old_active_ver AS (
            SELECT id FROM ttable_versions
            WHERE status_id = $2
              AND type = (SELECT type FROM ttable_versions WHERE id = $1) 
              AND is_commited = true 
        ),
        upd_try AS (
            UPDATE ttable_versions 
            SET last_modified_at = now(), status_id = $2, is_commited = CASE 
                WHEN EXISTS (SELECT 1 FROM old_active_ver) THEN false
                ELSE true
                END
            WHERE id = $1
        )
        SELECT id FROM old_active_ver
        '''
        res = await self.conn.fetchval(query, cur_ttable_id, TimetableVerStatuses.accepted)
        return res

    async def check_accept_constraints(self, sched_ver_id: int):
        await self.conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        building_id = await self.conn.fetchval('SELECT building_id FROM ttable_versions WHERE id = $1', sched_ver_id)

        base_groups = {rec['id'] for rec in (await self.base_groups(building_id))}
        ttable_ver_groups = {rec['group_id'] for rec in (await self.ttable_ver_groups(sched_ver_id))}

        'Не все группы в версии расписания "готовы"'
        if remains_groups:=(base_groups - ttable_ver_groups):
            await self.conn.execute('ROLLBACK')
            return 409, {"message": f"Недостаточно групп в Расписании", "needed_groups": list(remains_groups), "ttable_id": sched_ver_id}

        res_switch = await self.pre_commit_version(sched_ver_id)
        await self.conn.execute('COMMIT')

        "Есть другое расписание"
        if res_switch:
            return 202, {'message': "Расписание прошло проверки, но есть другое расписание с тем же предназначением", 'cur_active_ver': res_switch, "pending_ver_id": sched_ver_id}

        "Другого расписания нет, успешный коммит"
        return None

    async def commit_version(self, pending_ver_id: int, target_ver_id: int):
        query = '''
        WITH deactivate_ver AS (
            UPDATE ttable_versions SET last_modified_at = now(), status_id = $3, is_commited = false
            WHERE id = $1
        )
        UPDATE ttable_versions SET last_modified_at = now(), is_commited = true WHERE id = $2
        '''
        await self.conn.execute(query, pending_ver_id, target_ver_id, TimetableVerStatuses.pending)
