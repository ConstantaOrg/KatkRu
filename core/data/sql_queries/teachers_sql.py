from asyncpg import Connection


class TeachersQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_all(self, is_active_flag: bool | None, limit: int, offset: int):
        """
        Привязка по зданию - в будущих версиях. Также поможет контролю версий
        (будет проверять, чтобы была +1 пара между парами препода, если они в разных зданиях)
        """
        is_active_filter = ''
        filter_args = []

        "Фильтры"
        if is_active_flag is not None:
            is_active_filter = 'WHERE is_active = $3'
            filter_args.append(is_active_flag)

        query = f'SELECT id, fio, is_active FROM teachers {is_active_filter} LIMIT $1 OFFSET $2'
        res = await self.conn.fetch(query, limit, offset, *filter_args)
        return res

    async def add(self, fio: str):
        query = '''
        INSERT INTO teachers (fio) VALUES ($1)
        ON CONFLICT (fio) DO NOTHING
        RETURNING id
        '''
        res = await self.conn.fetchval(query, fio)
        return res

    async def switch_status(self, ids2active, ids2deprecated):
        active_rows, inactive_rows = [], []
        if ids2active:
            active_rows = await self.conn.fetch(
                'UPDATE teachers SET is_active = true WHERE id = ANY($1) RETURNING id', ids2active)
        if ids2deprecated:
            inactive_rows = await self.conn.fetch(
                'UPDATE teachers SET is_active = false WHERE id = ANY($1) RETURNING id', ids2deprecated)

        return len(active_rows), len(inactive_rows)

    async def teachers2elastic(self):
        query = 'SELECT id, fio, is_active FROM teachers'
        res = await self.conn.fetch(query)
        return res