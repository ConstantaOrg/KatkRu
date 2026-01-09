from asyncpg import Connection, UniqueViolationError

from core.utils.anything import TimetableVerStatuses, TimetableTypes, CardsStatesStatuses, extract_conflict_values
from core.utils.logger import log_event


class N8NIUQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_cards(self, sched_ver_id: int):
        query = '''
        SELECT csd.card_hist_id, csh.status_id AS status_card, csh.group_id, g.name, csd.position, csd.discipline_id, d.title, csd.is_force
        FROM cards_states_details csd
        JOIN cards_states_history csh ON csh.id = csd.card_hist_id
        JOIN disciplines d ON d.id = csd.discipline_id
        JOIN groups g ON g.id = csh.group_id
        WHERE csd.sched_ver_id = $1
          AND csh.is_current = true
        '''
        res = await self.conn.fetch(query, sched_ver_id)
        return res

    async def load_std_lessons_as_current(self, building_id: int, week_day: int, sched_ver_id: int, user_id: int):
        query = '''
        WITH std_recs AS (
            SELECT s_t.group_id, s_t.discipline_id, s_t.position, s_t.aud, s_t.teacher_id
            FROM std_ttable s_t
            JOIN ttable_versions t_v ON t_v.id = s_t.sched_ver_id
            JOIN groups g ON g.id = s_t.group_id AND g.is_active = true             -- Фильтр нужен для выгрузки "Неудалённых" записей
            JOIN teachers t ON t.id = s_t.teacher_id AND t.is_active = true         -- Фильтр нужен для выгрузки "Неудалённых" записей
            JOIN disciplines d ON d.id = s_t.discipline_id AND d.is_active = true   -- Фильтр нужен для выгрузки "Неудалённых" записей
            WHERE t_v.status_id = $1
              AND t_v.is_commited = true 
              AND t_v.building_id = $2
              AND t_v.type = $3              
              AND s_t.week_day = $4
        ),
        switch_cur AS (
            UPDATE cards_states_history SET is_current = false WHERE sched_ver_id = $5 AND is_current = true
        ),
        ins_hist AS (
            INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current)
            SELECT $5, $6, $7, s_r.group_id, true
            FROM std_recs s_r
            GROUP BY s_r.group_id
            RETURNING id, group_id
        ),
        ins_details AS (
            INSERT INTO cards_states_details (card_hist_id, discipline_id, "position", aud, teacher_id, sched_ver_id)
            SELECT h.id, s_r.discipline_id, s_r.position, s_r.aud, s_r.teacher_id, $5
            FROM std_recs s_r
            JOIN ins_hist h ON h.group_id = s_r.group_id
            RETURNING card_hist_id, position, discipline_id
        )
        SELECT i_d.card_hist_id, $7 AS status_card, g.id, g.name, i_d.position, d.id, d.title, false AS is_force
        FROM ins_details i_d
        JOIN ins_hist i_h ON i_h.id = i_d.card_hist_id
        JOIN groups g ON g.id = i_h.group_id
        JOIN disciplines d ON d.id = i_d.discipline_id
        '''
        res = await self.conn.fetch(query, TimetableVerStatuses.accepted, building_id, TimetableTypes.standard, week_day, sched_ver_id, user_id, CardsStatesStatuses.draft)
        return res

    async def check_loaded_std_pairs(self, building_id: int, sched_ver_id: int):
        q_std_groups = f'''
        SELECT DISTINCT g.name FROM cards_states_details csd
        JOIN ttable_versions t_v ON t_v.id = csd.sched_ver_id
        JOIN cards_states_history csh ON csh.id = csd.card_hist_id AND csh.is_current = true
        JOIN groups g ON g.id = csh.group_id AND g.building_id = $1
        WHERE g.is_active = false 
        AND csd.sched_ver_id = $2
        AND t_v.is_commited = true 
        '''
        q_std_disciplines = f'''
        SELECT DISTINCT d.title FROM cards_states_details csd
        JOIN ttable_versions t_v ON t_v.id = csd.sched_ver_id
        JOIN cards_states_history csh ON csh.id = csd.card_hist_id AND csh.is_current = true
        JOIN disciplines d ON d.id = csd.discipline_id
        WHERE d.is_active = false
        AND csd.sched_ver_id = $1
        AND t_v.is_commited = true 
        '''
        q_std_teachers = f'''
        SELECT DISTINCT t.fio FROM cards_states_details csd
        JOIN ttable_versions t_v ON t_v.id = csd.sched_ver_id
        JOIN cards_states_history csh ON csh.id = csd.card_hist_id AND csh.is_current = true
        JOIN teachers t ON t.id = csd.teacher_id
        WHERE t.is_active = false
        AND csd.sched_ver_id = $1
        AND t_v.is_commited = true 
        '''

        diff_groups = await self.conn.fetch(q_std_groups, building_id, sched_ver_id)
        diff_disciplines = await self.conn.fetch(q_std_disciplines, sched_ver_id)
        diff_teachers = await self.conn.fetch(q_std_teachers, sched_ver_id)
        return {
            'diff_groups': diff_groups,
            'diff_disciplines': diff_disciplines,
            'diff_teachers': diff_teachers
        }


    async def get_ext_card(self, card_hist_id: int):
        query = '''
        SELECT csd.position, t.fio AS teacher_name, csd.teacher_id, csd.aud FROM cards_states_details csd
        JOIN teachers t ON t.id = csd.teacher_id
        WHERE csd.card_hist_id = $1
        '''
        res = await self.conn.fetch(query, card_hist_id)
        return res

    async def save_card(self, card_hist_id: int, sched_ver_id: int, user_id: int, lessons_json: str):
        query = '''
        WITH switch_cur AS (
            UPDATE cards_states_history SET is_current = false WHERE id = $1
            RETURNING group_id
        ),
        ins_hist AS (
            INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current)
            SELECT $2, $3, $4, sc.group_id, true
            FROM switch_cur sc
            RETURNING id AS new_hist_id
        ),
        ins_details AS (
            INSERT INTO cards_states_details (card_hist_id, discipline_id, "position", aud, teacher_id, is_force, sched_ver_id)
            SELECT i_h.new_hist_id, l.discipline_id, l.position, l.aud, l.teacher_id, l.is_force, $2
            FROM jsonb_to_recordset($5::jsonb) AS l(position int, discipline_id int, teacher_id int, aud text, is_force bool)
            CROSS JOIN ins_hist i_h
        )
        SELECT new_hist_id AS id FROM ins_hist
        '''
        try:
            res = (await self.conn.fetchrow(query, card_hist_id, sched_ver_id, user_id, CardsStatesStatuses.edited, lessons_json))['id']
        except UniqueViolationError as e:
            exc = e.as_dict()['detail']
            details = extract_conflict_values(exc)
            res = {'columns': details[0], 'values': tuple(map(int, details[1]))}
            log_event(f"Конфликты при сохранении карточки | msg: \033[33m{exc}\033[0m", level='CRITICAL')
        return res

    async def get_cards_history(self, sched_ver_id: int, group_id: int):
        query = '''
        SELECT csh.id AS card_hist_id, csh.created_at, csh.user_id, u.name AS user_name, csh.status_id, csh.is_current
        FROM cards_states_history csh
        JOIN users u ON u.id = csh.user_id
        WHERE csh.sched_ver_id = $1 AND csh.group_id = $2
        ORDER BY csh.is_current DESC, csh.id DESC -- Возможно в фронта кинуть эту задачу
        LIMIT 50                                  -- Мейби сделать пагинацию для фронта 
        '''
        return await self.conn.fetch(query, sched_ver_id, group_id)

    async def get_card_content(self, card_hist_id: int):
        query = '''
        SELECT csd.position, csd.aud, csd.discipline_id, d.title AS discipline_title, csd.teacher_id, t.fio AS teacher_name
        FROM cards_states_details csd
        JOIN disciplines d ON d.id = csd.discipline_id
        JOIN teachers t ON t.id = csd.teacher_id
        WHERE csd.card_hist_id = $1
        '''
        return await self.conn.fetch(query, card_hist_id)

    async def accept_card(self, card_hist_id: int):
        query = 'UPDATE cards_states_history SET status_id = $2 WHERE id = $1'
        await self.conn.execute(query, card_hist_id, CardsStatesStatuses.accepted)
