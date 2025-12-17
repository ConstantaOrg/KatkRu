from asyncpg import Connection

from core.utils.logger import log_event


class TimetableQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_ttable(self, building_id: int, group: str, date_start, date_end):
        date_filter = 's_d.date BETWEEN $3 AND $4'
        date_args = (date_start, date_end)
        if not date_end:
            date_filter = 's_d.date = $3'
            date_args = (date_start,)
        query = f'''
        SELECT l.sched_id, l.position, dp.title, l.aud, t.fio FROM lessons l
        JOIN disciplines dp ON dp.id = l.discipline_id
        JOIN teachers t ON t.id = l.teacher_id
        WHERE l.sched_id IN (
            SELECT s_d.id FROM schedule_days s_d
            WHERE s_d.building_id = $1
            AND s_d.group_id = (SELECT g.id FROM groups g WHERE g.name = $2)
            AND {date_filter}
        )
        '''
        res = await self.conn.fetch(query, building_id, group, *date_args)
        return res