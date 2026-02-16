from asyncpg import Connection, UniqueViolationError, NotNullViolationError


class DisciplinesQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_all(self, is_active: bool | None, group_name: str | None, limit: int, offset: int):
        """
        Необходимы привязки предметов на группы: отдельная таблица.
        Необходимо для вкладки, из которой как блоки можно будет перетягивать пары в расписание группы
        """
        is_active_filter, group_filter = '', ''
        filter_args = []
        param_num = 3

        if is_active is not None:
            is_active_filter = f'WHERE d.is_active = ${param_num}'
            filter_args.append(is_active)
            param_num += 1
        if group_name is not None:
            group_filter = f'JOIN groups_disciplines gd on d.id = gd.discipline_id AND gd.group_id = (SELECT id FROM groups WHERE name = ${param_num})'
            filter_args.append(group_name)

        query = f'''
        SELECT d.id, d.title, d.is_active FROM disciplines d
        {group_filter}
        {is_active_filter}
        LIMIT $1 OFFSET $2'''
        res = await self.conn.fetch(query, limit, offset, *filter_args)
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

    async def disciplines2elastic(self):
        query = 'SELECT id, title, is_active FROM disciplines'
        res = await self.conn.fetch(query)
        return res


    async def get_relations(self, discipline_id: int):
        query = '''
        SELECT g.name, gd.group_id, g.is_active FROM groups_disciplines gd
        JOIN groups g on g.id = gd.group_id
        WHERE gd.discipline_id = $1
        '''
        res = await self.conn.fetch(query, discipline_id)
        return res


    async def add_relations_g2d(self, discipline_id: int, group_name: str):
        query = '''
        INSERT INTO groups_disciplines (group_id, discipline_id)
        SELECT
            (SELECT id FROM groups WHERE name = $2) AS group_id,
            $1 AS discipline_id
        '''

        try:
            await self.conn.execute(query, discipline_id, group_name)
            res = 200, 'Связка создана'
        except UniqueViolationError:
            res = 409, 'Такая пара уже существует'
        except NotNullViolationError:
            res = 400, 'Такой группы не существует'

        "Вставка успешна"
        return res
