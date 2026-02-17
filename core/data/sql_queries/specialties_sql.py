from asyncpg import Connection


class SpecsQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_specialties(self, limit: int, offset: int):
        """
        Нужно добавить картинку. С3 бакет соответственно
        """
        query = 'SELECT spec_code, title, img_path FROM specialties LIMIT $1 OFFSET $2'
        res = await self.conn.fetch(query, limit, offset)
        return res

    async def get_spec_by_id(self, spec_id: int):
        query = '''
        SELECT spec_code, description, full_time, free_form, evening_form, cost_per_year
        FROM specialties WHERE id = $1
        '''
        res = await self.conn.fetchrow(query, spec_id)
        return res

    async def specialties2elastic(self):
        query = 'SELECT id, spec_code, title FROM specialties'
        res = await self.conn.fetch(query)
        return res