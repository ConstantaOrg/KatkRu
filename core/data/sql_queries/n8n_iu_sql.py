from asyncpg import Connection, UniqueViolationError

from core.utils.anything import TimetableVerStatuses, TimetableTypes, CardsStatesStatuses, extract_conflict_values, \
    accept_card_constraint
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

    async def save_card(self, card_hist_id: int, sched_ver_id: int, user_id: int, lessons):
        query = '''
        WITH ver_check AS (
            SELECT id, is_commited, status_id
            FROM ttable_versions
            WHERE id = $2
        ),
        switch_cur AS (
            UPDATE cards_states_history SET is_current = false 
            WHERE id = $1
              AND EXISTS (
                SELECT 1 FROM ver_check 
                WHERE is_commited = false OR status_id != $4
              )
            RETURNING group_id
        ),
        ins_hist AS (
            INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current)
            SELECT $2, $3, $10, sc.group_id, true
            FROM switch_cur sc
            RETURNING id AS new_hist_id
        ),
        ins_details AS (
            INSERT INTO cards_states_details (card_hist_id, discipline_id, "position", aud, teacher_id, is_force, sched_ver_id)
            SELECT 
                i_h.new_hist_id, UNNEST($5::int[]), UNNEST($6::int[]), UNNEST($7::text[]), UNNEST($8::int[]), UNNEST($9::bool[]), $2
            FROM ins_hist i_h
        )
        SELECT new_hist_id AS id FROM ins_hist
        '''
        discipline_ids = tuple(lesson.discipline_id for lesson in lessons)
        positions = tuple(lesson.position for lesson in lessons)
        auds = tuple(lesson.aud for lesson in lessons)
        teacher_ids = tuple(lesson.teacher_id for lesson in lessons)
        is_forces = tuple(lesson.is_force for lesson in lessons)

        try:
            res = await self.conn.fetchval(
                query,
                card_hist_id, sched_ver_id, user_id, TimetableVerStatuses.accepted, discipline_ids, positions, auds, teacher_ids, is_forces, CardsStatesStatuses.edited
            )
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
        check_query = '''
        SELECT EXISTS (
            SELECT 1 
            FROM cards_states_history csh1
            JOIN cards_states_history csh2 ON csh2.id = $1
            WHERE csh1.sched_ver_id = csh2.sched_ver_id
              AND csh1.group_id = csh2.group_id
              AND csh1.status_id = $2
              AND csh1.id != $1
        ) as has_accepted
        '''
        has_accepted = await self.conn.fetchval(check_query, card_hist_id, CardsStatesStatuses.accepted)
        if has_accepted:
            return 409, 'Для этой группы уже существует утвержденная карточка в данной версии расписания'
        
        query = '''
        WITH ver_check AS (
            SELECT tv.id, tv.is_commited, tv.status_id
            FROM cards_states_history csh
            JOIN ttable_versions tv ON tv.id = csh.sched_ver_id
            WHERE csh.id = $1
        ),
        pairs_count AS (
            SELECT COUNT(*) as cnt
            FROM cards_states_details
            WHERE card_hist_id = $1
        ),
        update_result AS (
            UPDATE cards_states_history 
            SET status_id = $2
            WHERE id = $1
              AND EXISTS (
                SELECT 1 FROM ver_check 
                WHERE is_commited = false OR status_id != $4
              )
              AND EXISTS (
                SELECT 1 FROM pairs_count WHERE cnt >= $3
              )
            RETURNING id
        )
        SELECT ur.id as updated_id, vc.is_commited, vc.status_id, pc.cnt as pairs_count
        FROM ver_check vc
        CROSS JOIN pairs_count pc
        LEFT JOIN update_result ur ON true
        '''
        
        try:
            res = await self.conn.fetchrow(query, card_hist_id, CardsStatesStatuses.accepted, accept_card_constraint, TimetableVerStatuses.accepted)
        except UniqueViolationError:
            return 409, 'Для этой группы уже существует утвержденная карточка в данной версии расписания'
        
        if res['updated_id'] is not None:
            return 200, 'Карточка сменила статус на "Утверждено"!'
        
        if res['is_commited'] and res['status_id'] == TimetableVerStatuses.accepted:
            return 403, 'Версия расписания уже утверждена, изменения запрещены'
        
        return 409, f'В расписании для группы должно быть хотя бы {accept_card_constraint} занятий на день'


    async def bulk_add_cards(self, ttable_id: int, user_id: int, group_names: list[str], lessons: list):
        """
        Bulk-вставка карточек для групп.
        Если lessons пустой - создаются пустые карточки (только для одной группы).
        Если lessons не пустой(вставка из буфера обмена) - создаются карточки с дисциплинами для всех скопированных карточек-групп.
        """

        # Подготовка данных для lessons
        if lessons:
            discipline_ids = [lesson.discipline_id for lesson in lessons]
            positions = [lesson.position for lesson in lessons]
            auds = [lesson.aud for lesson in lessons]
            teacher_ids = [lesson.teacher_id for lesson in lessons]
            is_forces = [lesson.is_force for lesson in lessons]
        else:
            discipline_ids = []
            positions = []
            auds = []
            teacher_ids = []
            is_forces = []
        
        query = '''
        WITH ver_check AS (
            SELECT id, is_commited, status_id
            FROM ttable_versions
            WHERE id = $1
        ),
        group_ids AS (
            SELECT id, name
            FROM groups
            WHERE name = ANY($2::text[])
              AND is_active = true
        ),
        ins_hist AS (
            INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current)
            SELECT $1, $3, $4, g.id, true
            FROM group_ids g
            WHERE EXISTS (
                SELECT 1 FROM ver_check 
                WHERE is_commited = false OR status_id != $5
            )
            RETURNING id, group_id
        ),
        ins_details AS (
            INSERT INTO cards_states_details (card_hist_id, discipline_id, "position", aud, teacher_id, sched_ver_id, is_force)
            SELECT 
                h.id,
                lesson_data.discipline_id,
                lesson_data.position,
                lesson_data.aud,
                lesson_data.teacher_id,
                $1,
                lesson_data.is_force
            FROM ins_hist h
            CROSS JOIN (
                SELECT 
                    UNNEST($6::int[]) as discipline_id,
                    UNNEST($7::int[]) as position,
                    UNNEST($8::text[]) as aud,
                    UNNEST($9::int[]) as teacher_id,
                    UNNEST($10::bool[]) as is_force
            ) lesson_data
            WHERE $11 > 0
            ON CONFLICT (position, teacher_id, sched_ver_id) WHERE is_force = false DO NOTHING
            RETURNING card_hist_id
        )
        SELECT 
            COALESCE(array_agg(DISTINCT h.id), ARRAY[]::bigint[]) as card_ids,
            (SELECT is_commited FROM ver_check) as is_commited,
            (SELECT status_id FROM ver_check) as status_id,
            COALESCE(array_agg(DISTINCT g.name), ARRAY[]::text[]) as found_groups
        FROM ins_hist h
        FULL OUTER JOIN group_ids g ON true
        '''
        
        res = await self.conn.fetchrow(
            query,
            ttable_id, group_names, user_id, CardsStatesStatuses.draft, TimetableVerStatuses.accepted,
            discipline_ids, positions, auds, teacher_ids, is_forces, len(discipline_ids)
        )
        
        "Разбираемся, что получилось в запросе"
        if res['is_commited'] and res['status_id'] == TimetableVerStatuses.accepted:
            return None, 'Версия расписания уже утверждена, изменения запрещены'
        
        card_ids = res.get('card_ids', [])
        found_groups = set(res.get('found_groups', []))
        
        "Все ли группы найдены"
        not_found = set(group_names) - found_groups
        if not_found:
            return card_ids, f'Группы не найдены или неактивны: {", ".join(sorted(not_found))}'

        return card_ids, None

    async def switch_as_edit(self, card_hist_id: int):
        query = 'UPDATE cards_states_history SET status_id = $2 WHERE id = $1'
        await self.conn.execute(query, card_hist_id, CardsStatesStatuses.edited)