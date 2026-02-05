from asyncpg import Connection


class DisciplinesQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_all(self, limit: int, offset: int):
        """
        Необходимы привязки предметов на группы: отдельная таблица.
        Необходимо для вкладки, из которой как блоки можно будет перетягивать пары в расписание группы
        """
        query = 'SELECT id, title, is_active FROM disciplines LIMIT $1 OFFSET $2'
        res = await self.conn.fetch(query, limit, offset)
        return res

    async def add(self, disp_title: str):
        query = '''
        INSERT INTO disciplines (title) VALUES ($1)
        ON CONFLICT (title) DO NOTHING
        RETURNING id
        '''
        res = await self.conn.fetchval(query, disp_title)
        return res

    async def switch_status(self, ids2active, ids2deprecated):
        active_rows, inactive_rows = [], []
        if ids2active:
            active_rows = await self.conn.fetch(
                'UPDATE disciplines SET is_active = true WHERE id = ANY($1) RETURNING id', ids2active)
        if ids2deprecated:
            inactive_rows = await self.conn.fetch(
                'UPDATE disciplines SET is_active = false WHERE id = ANY($1) RETURNING id', ids2deprecated)

        return len(active_rows), len(inactive_rows)