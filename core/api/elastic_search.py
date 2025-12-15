from elasticsearch import NotFoundError
from fastapi import APIRouter

from core.config_dir.config import ElasticDep, env
from core.config_dir.index_settings import search_ptn, settings, mappings, aliases
from core.data.postgre import PgSqlDep
from core.schemas.schemas2depends import PagenDep
from core.schemas.specs_schema import AutocompleteSearchSchema, DeepSearchSchema
from core.utils.logger import log_event

router = APIRouter(prefix="/v1", tags=["Search🔍"])



@router.put('/server/elastic/index_up/{index_name}', summary='Название индекса может быть произвольным, но не должно совпадать с Элиасом')
async def put_index(index_name: str, db: PgSqlDep, aioes: ElasticDep):
    """
    В маркетплейсе предусмотреть загрузку из БД. Будет очень не очень, если за раз из БД выберется миллион+ записей
    """
    records = await db.specialties.specialties2elastic()
    async with aioes as aioes:
        "Обеспечение Идемпотентности ручки"
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
            category = ''.join(record['category_full'].replace('/', ' '))
            doc = {
                "id": record['id'],
                "prd_name": record['prd_name'],
                "category": category
            }
            batch.append({'index': {'_index': index_name, '_id': doc['id']}})       # action
            batch.append({'prd_name': doc['prd_name'], 'category': doc['category']})  # body
            if len(batch) >= 2000:
                await aioes.bulk(body=batch)
                batch.clear()
                log_event(f'В индекс "{index_name}" залетела партия!', level='WARNING')
        if batch:
            await aioes.bulk(body=batch, refresh=True)
        else:    await aioes.indices.refresh(index=index_name)

        log_event(f'Индексация и создание "{index_name}" успешны!', level='WARNING')
        return {'success': True, 'message': f'Индекс {index_name} поднят, документы вставлены'}


@router.post("/public/elastic/autocomplete_spec")
async def fast_search(body: AutocompleteSearchSchema, aioes: ElasticDep):
    """
    код специальности и название склеить на фронте(возможно)
    """
    search_schema = search_ptn(body.search_term, search_mode=body.search_mode)
    raw_res = await aioes.search(index=env.search_index, query=search_schema, size=5, source=False, filter_path='hits.hits')
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', level='WARNING')
    return {"search_res": search_res}


@router.post("/public/elastic/ext_spec")
async def deep_search(body: DeepSearchSchema, pagen: PagenDep, aioes: ElasticDep):
    """
    код специальности и название склеить на фронте(возможно)
    """
    search_schema = search_ptn(body.search_term, search_mode=body.search_mode)
    raw_res = await aioes.search(
        index=env.search_index,
        query=search_schema,
        source=False,
        filter_path='hits.hits',
        from_=pagen.offset,
        size=pagen.limit
    )
    search_res = raw_res['hits']['hits']

    log_event(f'Поисковая выдача: search_term: "{body.search_term}"; length hits: {len(search_res)}; \033[33m{body.search_mode}\033[0m', level='WARNING')
    return {"search_res": search_res}
