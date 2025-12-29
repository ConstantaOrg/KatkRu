from asyncpg import Connection

from core.utils.anything import TimetableVerStatuses, TimetableTypes, CardsStatesStatuses


class N8NIUQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def load_std_lessons_as_current(self, building_id: int, week_day: int, sched_ver_id: int, user_id: int):
        query = '''
        WITH std_recs AS (
            SELECT s_t.group_id, s_t.discipline_id, s_t.position, s_t.aud, s_t.teacher_id
            FROM std_ttable s_t
            JOIN ttable_versions t_v ON t_v.id = s_t.sched_ver_id
            JOIN groups g ON g.id = s_t.group_id AND g.is_active = true
            WHERE t_v.status_id = $1          
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
        SELECT i_d.card_hist_id, g.name, i_d.position, d.title
        FROM ins_details i_d
        JOIN ins_hist i_h ON i_h.id = i_d.card_hist_id
        JOIN groups g ON g.id = i_h.group_id
        JOIN disciplines d ON d.id = i_d.discipline_id
        '''
        res = await self.conn.fetch(query, TimetableVerStatuses.accepted, building_id, TimetableTypes.standard, week_day, sched_ver_id, user_id, CardsStatesStatuses.draft)
        return res

    async def get_ext_card(self, card_hist_id: int):
        query = '''
        
        '''
        res = await self.conn.fetch(query, )
        return res
