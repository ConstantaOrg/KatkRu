from datetime import date as date_type

from asyncpg import Connection

from core.api.ttable_versions.ttable_parser import raw_values2db_ids_handler
from core.utils.anything import TimetableTypes, TimetableVerStatuses, CardsStatesStatuses
from core.utils.logger import log_event


class TimetableQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_ttable(self, group: str | list[str] | None, date):
        query = '''
        SELECT csd.position, dp.title, t.fio, csd.aud 
        FROM cards_states_details csd 
        JOIN cards_states_history csh ON csh.id = csd.card_hist_id
            AND csh.is_current = true
            AND csh.status_id IN ($4, $5)
        JOIN ttable_versions t_v ON t_v.id = csh.sched_ver_id 
            AND t_v.status_id = $2 
            AND t_v.is_commited = true
            AND t_v.schedule_date = $3
        JOIN groups g ON g.id = csh.group_id 
            AND g.is_active = true 
            AND g.name = $1
        JOIN disciplines dp ON dp.id = csd.discipline_id
        JOIN teachers t ON t.id = csd.teacher_id
        '''
        res = await self.conn.fetch(query, group, TimetableVerStatuses.accepted, date, CardsStatesStatuses.draft, CardsStatesStatuses.accepted)
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

    async def create(self, building_id: int, date: date_type | None, type_: str, status: int, user_id: int):
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
            return 409, {"message": "Недостаточно групп в Расписании", "needed_groups": list(remains_groups), "ttable_id": sched_ver_id}

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


    async def filtered_layout(
            self, building_id: int, status_id: int | None, ttable_type: str | None, is_commited: bool | None, schedule_date: date_type | None, sort_type: str, limit: int, offset: int
    ):
        status_filter, ttable_type_filter, is_commited_filter, schedule_date_filter = '', '', '', ''
        filter_args = []
        param_num = 5

        "Используем динамические плейсхолдеры для фильтров"
        if status_id is not None:
            status_filter = f'AND tv.status_id = ${param_num}'
            filter_args.append(status_id)
            param_num += 1
        if ttable_type is not None:
            ttable_type_filter = f'AND tv.type = ${param_num}'
            filter_args.append(ttable_type)
            param_num += 1
        if is_commited is not None:
            is_commited_filter = f'AND tv.is_commited = ${param_num}'
            filter_args.append(is_commited)
            param_num += 1
        if schedule_date is not None or ttable_type == TimetableTypes.standard:
            schedule_date_filter = 'AND tv.schedule_date IS NULL'
            if ttable_type != TimetableTypes.standard:
                schedule_date_filter = f'AND tv.schedule_date = ${param_num}'
                filter_args.append(schedule_date)

        base_query = f'''
        WITH filtered_records AS (
            SELECT tv.id, tv.type, tv.schedule_date, tv.building_id, tv.status_id, tv.is_commited, tv.user_id
            FROM ttable_versions tv
            JOIN public.users u ON tv.user_id = u.id
            WHERE u.building_id = $1
            {status_filter}
            {ttable_type_filter}
            {is_commited_filter}
            {schedule_date_filter}
            ORDER BY tv.id {sort_type}
            LIMIT $2 OFFSET $3
        ),
        add_replace_icons AS (
            SELECT 
                fr.id as ttable_id,
                EXISTS (
                    SELECT 1 
                    FROM ttable_versions tv_approved
                    WHERE tv_approved.status_id = $4
                    AND tv_approved.is_commited = true
                    AND tv_approved.building_id = fr.building_id
                    AND tv_approved.type = fr.type
                    AND (
                        (tv_approved.schedule_date IS NULL AND fr.schedule_date IS NULL)
                        OR tv_approved.schedule_date = fr.schedule_date
                    )
                    AND tv_approved.id != fr.id
                ) as show_icon
            FROM filtered_records fr
        )
        SELECT fr.id, fr.type, ts.title as status, fr.schedule_date, fr.is_commited, u.name, ari.show_icon 
        FROM filtered_records fr
        JOIN ttable_statuses ts ON ts.id = fr.status_id
        JOIN public.users u ON fr.user_id = u.id
        JOIN add_replace_icons ari ON fr.id = ari.ttable_id
        ORDER BY fr.id {sort_type}
        '''
        records = await self.conn.fetch(base_query, building_id, limit, offset, TimetableVerStatuses.accepted, *filter_args)
        return records


    async def get_by_id(self, ttable_id: int, building_id: int):
        query = '''
        WITH target_record AS (
            SELECT tv.id, tv.type, tv.schedule_date, tv.building_id, tv.status_id, tv.is_commited, tv.user_id
            FROM ttable_versions tv
            JOIN public.users u ON tv.user_id = u.id
            WHERE tv.id = $1 AND u.building_id = $2
        ),
        add_replace_icon AS (
            SELECT 
                tr.id as ttable_id,
                EXISTS (
                    SELECT 1 
                    FROM ttable_versions tv_approved
                    WHERE tv_approved.status_id = $3
                    AND tv_approved.is_commited = true
                    AND tv_approved.building_id = tr.building_id
                    AND tv_approved.type = tr.type
                    AND (
                        (tv_approved.schedule_date IS NULL AND tr.schedule_date IS NULL)
                        OR tv_approved.schedule_date = tr.schedule_date
                    )
                    AND tv_approved.id != tr.id
                ) as show_icon
            FROM target_record tr
        )
        SELECT tr.id, tr.type, ts.title as status, tr.schedule_date, tr.is_commited, u.name, ari.show_icon 
        FROM target_record tr
        JOIN ttable_statuses ts ON ts.id = tr.status_id
        JOIN public.users u ON tr.user_id = u.id
        LEFT JOIN add_replace_icon ari ON tr.id = ari.ttable_id
        '''
        record = await self.conn.fetchrow(query, ttable_id, building_id, TimetableVerStatuses.accepted)
        return record

    async def get_candidates_by_ver(self, ttable_id: int, building_id: int):
        query = '''
        WITH source_version AS (
            SELECT tv.type, tv.schedule_date, tv.building_id
            FROM ttable_versions tv
            JOIN public.users u ON tv.user_id = u.id
            WHERE tv.id = $1 AND u.building_id = $2
        )
        SELECT tv.id, tv.type, ts.title as status, tv.schedule_date, tv.is_commited, u.name, tv.created_at, tv.last_modified_at
        FROM ttable_versions tv
        JOIN ttable_statuses ts ON ts.id = tv.status_id
        JOIN public.users u ON tv.user_id = u.id
        CROSS JOIN source_version sv
        WHERE tv.building_id = sv.building_id
        AND tv.type = sv.type
        AND (
            (tv.schedule_date IS NULL AND sv.schedule_date IS NULL)
            OR tv.schedule_date = sv.schedule_date
        )
        AND tv.id != $1
        AND tv.status_id = $3
        ORDER BY tv.last_modified_at DESC
        '''
        records = await self.conn.fetch(query, ttable_id, building_id, TimetableVerStatuses.accepted)
        return records

    async def switch_ver_status(self, ttable_id: int, building_id: int):
        """2 защиты: building_id - если НСД доступ; is_commited != true - Нельзя изменить статус утверждённого расписния"""
        query = 'UPDATE ttable_versions SET status_id = $3 WHERE id = $1 AND building_id = $2 AND is_commited != true RETURNING id'
        record = await self.conn.fetchval(query, ttable_id, building_id, TimetableVerStatuses.pending)
        return record
