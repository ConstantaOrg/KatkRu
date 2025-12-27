from asyncpg import Connection

from core.utils.anything import TimetableVerStatuses, TimetableTypes


class N8NIUQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_std_lessons(self, building_id: int, week_day: int):
        query = '''
        SELECT s_t.group_id, g.name, s_t.discipline_id, s_t.position, d.title, s_t.aud, s_t.teacher_id FROM std_ttable s_t 
        JOIN ttable_versions t_v ON t_v.id = s_t.sched_ver_id
        JOIN groups g ON g.id = s_t.group_id AND g.is_active = true
        JOIN disciplines d ON d.id = s_t.discipline_id
        WHERE t_v.status_id = $1 AND t_v.building_id = $2 AND t_v.type = $3 AND s_t.week_day = $4
        '''
        to_show = await self.conn.fetch(query, TimetableVerStatuses.accepted, building_id, TimetableTypes.standard, week_day)

        return to_show

    async def get_aud_teach_id_by_card(self, ttable_id: int, building_id: int, week_day: int):
        query_main = '''
        SELECT * FROM ttable_versions tv 
        '''
        query_fallback = '''
        SELECT * FROM std_ttable s_t
        JOIN ttable_versions t_v ON t_v.id = s_t.sched_ver_id
        WHERE t_v.status_id = $1 AND t_v.building_id = $2 AND t_v.type = $3 AND s_t.week_day = $4
        '''

        res = await self.conn.fetch(query_main, )
        if not res:
            res = await self.conn.fetch(query_fallback, TimetableVerStatuses.accepted, building_id, TimetableTypes.standard, week_day)
        return res