from asyncpg import Pool
from elasticsearch import NotFoundError, AsyncElasticsearch
from fastapi import APIRouter
from starlette.requests import Request

from core.api.elastic_search.sub_handlers import fill_group_index, fill_spec_index
from core.config_dir.config import ElasticDep, env
from core.config_dir.index_settings import SpecIndex, GroupIndex, LogIndex
from core.data.postgre import PgSql
from core.response_schemas.elastic_search import (
    AutocompleteSearchResponse, DeepSearchResponse
)
from core.schemas.schemas2depends import PagenDep
from core.schemas.specs_schema import AutocompleteSearchSchema, DeepSearchSchema, BaseSpecSearchSchema
from core.utils.logger import log_event

router = APIRouter(tags=["Search🔍"])



async def init_elasticsearch_index(index_names: list[str], db: Pool, aioes: AsyncElasticsearch):
    async with db.acquire() as conn:
        "Вытягиваем из БД записи для индекса"
        conn = PgSql(conn)
        records_specs = await conn.specialties.specialties2elastic()
        records_groups = await conn.groups.groups2elastic()
    log_event(f'Будущие документы. Из БД взяты records_specs: \033[34m{len(records_specs)}\033[0m; records_groups: \033[32m{len(records_groups)}\033[0m')

    "Индексы для инициализации"
    app_indices = [
        [env.log_index, None, LogIndex],             # Индекс, флаг для индексации, Класс настроек индекса
        [env.search_index_spec, True, SpecIndex],    # Индекс, флаг для индексации, Класс настроек индекса
        [env.search_index_group, True, GroupIndex],  # Индекс, флаг для индексации, Класс настроек индекса
    ]

    for idx, index in enumerate(app_indices):
        "Обеспечение Идемпотентности"
        index_name, index_alias, idx_conf = index_names[idx], index[0], index[2]
        try:
            aliases_ = await aioes.indices.get_alias(name=index_alias) # смотрим имя индекса из параметров инита в лайфспане!
            if aliases_:
                index[1] = False
                log_event(f"Индекс {index_name} уже был создан и Проиндексирован | alias: {index_alias}", level='WARNING')
                continue
        except NotFoundError:
            pass

        "Создаем ILM политику"
        if hasattr(idx_conf, 'ilm_policy'):  # для LogIndex
            try:
                await aioes.ilm.put_lifecycle(name=idx_conf.policy_name, body=idx_conf.ilm_policy)
                log_event(f"ILM policy '{idx_conf.policy_name}' создана/обновлена", level='INFO')
            except Exception as e:
                log_event(f"Ошибка создания ILM policy: {e}", level='CRITICAL')

        "Создаём индекс"
        log_event("Создание индекса: %s", index_alias, level='WARNING')
        await aioes.indices.create(
            index=index_name,
            aliases=idx_conf.aliases,
            settings=idx_conf.settings,
            mappings=idx_conf.mappings
        )

    "Вносим записи(документы)"
    spec_status = await fill_spec_index(records_specs, index_names[1], aioes) if app_indices[1][1] else False # Не вносим записи, если нет индексации
    group_status = await fill_group_index(records_groups, index_names[2], aioes) if app_indices[2][1] else False # Не вносим записи, если нет индексации
    log_level = 'WARNING' if spec_status and group_status else 'CRITICAL'

    log_event(f'Индексация и создание "{index_names}" | \033[34mspec_status: {spec_status}; group_status: {group_status}; app-logs-index: создан с ILM\033[0m', level=log_level)
    return {'success': spec_status and group_status, 'message': f'Индексы {index_names} подняты, документы вставлены'}



@router.post("/public/elastic/autocomplete_spec", response_model=AutocompleteSearchResponse)
async def fast_search(body: AutocompleteSearchSchema, request: Request, aioes: ElasticDep):
    """
    код специальности и название склеить на фронте(возможно)
    """
    search_schema = SpecIndex.search_ptn(body.search_term, search_mode=body.search_mode)
    raw_res = await aioes.search(index=env.search_index_spec, query=search_schema, size=5, filter_path='hits.hits')
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', request=request, level='WARNING')
    return {"search_res": tuple(
        {'id': rec['_id'], 'spec_code': rec['_source']['code_autocomplete'], 'title': rec['_source']['title']}
        for rec in search_res
    )}


@router.post("/public/elastic/ext_spec", response_model=DeepSearchResponse)
async def deep_search(body: DeepSearchSchema, pagen: PagenDep, aioes: ElasticDep):
    """
    код специальности и название склеить на фронте(возможно)
    """
    search_schema = SpecIndex.search_ptn(body.search_term, search_mode=body.search_mode)
    raw_res = await aioes.search(
        index=env.search_index_spec,
        query=search_schema,
        filter_path='hits.hits',
        from_=pagen.offset,
        size=pagen.limit
    )
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', level='WARNING')
    return {"search_res": tuple(
        {'id': rec['_id'], 'spec_code': rec['_source']['code_autocomplete'], 'title': rec['_source']['title']}
        for rec in search_res
    )}

@router.post("/public/elastic/search_group", response_model=AutocompleteSearchResponse)
async def fast_search(body: BaseSpecSearchSchema, request: Request, aioes: ElasticDep):
    search_schema = GroupIndex.search_ptn(body.search_term)
    raw_res = await aioes.search(index=env.search_index_spec, query=search_schema, size=10, filter_path='hits.hits')
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', request=request, level='WARNING')
    return {"search_res": tuple(
        {'id': rec['_id'], 'group_name': rec['_source']['group_name']}
        for rec in search_res
    )}