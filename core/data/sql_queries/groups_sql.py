from asyncpg import Connection


class GroupsQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_all(self, building_id: int, is_active_flag: bool | None, limit: int, offset: int):
        is_active_filter = ''
        filter_args = []

        "Фильтры"
        if is_active_flag is not None:
            is_active_filter = 'AND is_active = $4'
            filter_args.append(is_active_flag)

        query = f'SELECT id, name, is_active FROM groups WHERE building_id = $1 {is_active_filter} LIMIT $2 OFFSET $3'
        res = await self.conn.fetch(query, building_id, limit, offset, *filter_args)
        return res

    async def add(self, group_name: str, building_id: int):
        query = '''
        INSERT INTO groups (name, building_id) VALUES ($1, $2)
        ON CONFLICT (name) DO NOTHING
        RETURNING id
        '''
        res = await self.conn.fetchval(query, group_name, building_id)
        return res

    async def switch_status(self, ids2active, ids2deprecated):
        active_rows, inactive_rows = [], []
        if ids2active:
            active_rows = await self.conn.fetch(
                'UPDATE groups SET is_active = true WHERE id = ANY($1) RETURNING id', ids2active)
        if ids2deprecated:
            inactive_rows = await self.conn.fetch(
                'UPDATE groups SET is_active = false WHERE id = ANY($1) RETURNING id', ids2deprecated)

        return len(active_rows), len(inactive_rows)

    async def groups2elastic(self):
        query = 'SELECT id, name, is_active FROM groups'
        res = await self.conn.fetch(query)
        return res