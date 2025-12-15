from asyncpg import Connection


class SpecsQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_specialties(self, limit: int, offset: int):
        query = 'SELECT learn_years, title, profession FROM specialties LIMIT $1 OFFSET $2'
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
        query2 = '''
        ДОКУМЕНТАЦИОННОЕ ОБЕСПЕЧЕНИЕ УПРАВЛЕНИЯ И АРХИВОВЕДЕНИЕ (ВНЕБЮДЖЕТ)

        (46.02.01)

        Виды деятельности: работа в секретариатах, службах документационного обеспечения, кадровых службах и архивах государственных органов и учреждений, в органах местного самоуправления, негосударственных организациях всех форм собственности, общественных организациях (учреждениях). осуществление организационного и документационного обеспечения деятельности организации; организация архивной работы по документам организаций различных форм собственности

        2 года 10 месяцев
        '''

        '''
        SELECT title, spec_code, description, learn_years FROM specialties
        '''
        res = await self.conn.fetch(query)
        return res