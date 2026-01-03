from asyncpg import Pool
from elasticsearch import NotFoundError, AsyncElasticsearch
from fastapi import APIRouter
from starlette.requests import Request

from core.config_dir.config import ElasticDep, env
from core.config_dir.index_settings import search_ptn, settings, mappings, aliases
from core.data.postgre import PgSql
from core.schemas.schemas2depends import PagenDep
from core.schemas.specs_schema import AutocompleteSearchSchema, DeepSearchSchema
from core.utils.logger import log_event

router = APIRouter(tags=["Search🔍"])



async def init_elasticsearch_index(index_name: str, db: Pool, aioes: AsyncElasticsearch):
    async with db.acquire() as conn:
        "Вытягиваем из БД записи для индекса"
        conn = PgSql(conn)
        records = await conn.specialties.specialties2elastic()

    "Обеспечение Идемпотентности"
    try:
        aliases_ = await aioes.indices.get_alias(name=env.search_index)
        if aliases_:
            return {'success': False, 'message': "Индекс уже был создан и Проиндексирован"}
    except NotFoundError:
        pass

    "Создаём и Наполняем индекс"
    log_event("Создание индекса: %s", index_name, level='WARNING')
    await aioes.indices.create(index=index_name,
                                   aliases=aliases,
                                   settings=settings,
                                   mappings=mappings)
    batch = []
    for record in records:
        doc = {
            "id": record['id'],
            "code_prefix": record['spec_code'],
            "spec_title_prefix": record['title'],
            "spec_title_search": record['title']
        }
        batch.append({'index': {'_index': index_name, '_id': doc['id']}})       # action
        batch.append({
            "code_prefix": record['spec_code'],
            "spec_title_prefix": record['title'],
            "spec_title_search": record['title']
        })

        "Батч-вставка"
        if len(batch) >= 2000:
            await aioes.bulk(body=batch)
            batch.clear()
            log_event(f'В индекс "{index_name}" залетела партия!', level='WARNING')

    "Добираем оставшееся/Обновляем индекс"
    if batch:
        await aioes.bulk(body=batch, refresh=True)
    else:    await aioes.indices.refresh(index=index_name)

    log_event(f'Индексация и создание "{index_name}" успешны!', level='WARNING')
    return {'success': True, 'message': f'Индекс {index_name} поднят, документы вставлены'}



@router.post("/public/elastic/autocomplete_spec")
async def fast_search(body: AutocompleteSearchSchema, request: Request, aioes: ElasticDep):
    """
    код специальности и название склеить на фронте(возможно)
    """
    search_schema = search_ptn(body.search_term, search_mode=body.search_mode)
    raw_res = await aioes.search(index=env.search_index, query=search_schema, size=5, filter_path='hits.hits')
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', request=request, level='WARNING')
    return {"search_res": tuple(
        {'id': rec['_id'], 'spec_code': rec['_source']['code_prefix'], 'title': rec['_source']['spec_title_prefix']}
        for rec in search_res
    )}


@router.post("/public/elastic/ext_spec")
async def deep_search(body: DeepSearchSchema, pagen: PagenDep, aioes: ElasticDep):
    """
    код специальности и название склеить на фронте(возможно)
    """
    search_schema = search_ptn(body.search_term, search_mode=body.search_mode)
    raw_res = await aioes.search(
        index=env.search_index,
        query=search_schema,
        filter_path='hits.hits',
        from_=pagen.offset,
        size=pagen.limit
    )
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', level='WARNING')
    return {"search_res": tuple(
        {'id': rec['_id'], 'spec_code': rec['_source']['code_prefix'], 'title': rec['_source']['spec_title_prefix']}
        for rec in search_res
    )}
