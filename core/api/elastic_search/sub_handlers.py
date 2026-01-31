from elasticsearch import AsyncElasticsearch

from core.utils.logger import log_event


async def fill_spec_index(records, spec_index, es_obj: AsyncElasticsearch):
    batch = []
    for record in records:
        doc = {
            "id": record['id'],
            "code_prefix": record['spec_code'],
            "spec_title_prefix": record['title'],
            "spec_title_search": record['title']
        }
        batch.append({'index': {'_index': spec_index, '_id': doc['id']}})  # action
        batch.append({
            "code_prefix": record['spec_code'],
            "spec_title_prefix": record['title'],
            "spec_title_search": record['title']
        })

        "Батч-вставка"
        if len(batch) >= 2000:
            await es_obj.bulk(body=batch)
            batch.clear()
            log_event(f'В индекс "{spec_index}" залетела партия!', level='WARNING')

    "Добираем оставшееся/Обновляем индекс"
    if batch:
        await es_obj.bulk(body=batch, refresh=True)
    else:
        await es_obj.indices.refresh(index=spec_index)

    "Индекс успешно поднят"
    return True


async def fill_group_index(records, group_index, es_obj: AsyncElasticsearch):
    batch = []
    for record in records:
        doc = {
            "id": record['id'],
            "group_name": record['name'],
        }
        batch.append({'index': {'_index': group_index, '_id': doc['id']}})  # action
        batch.append({"group_name": record['name']})                        # body

        "Батч-вставка"
        if len(batch) >= 2000:
            await es_obj.bulk(body=batch)
            batch.clear()
            log_event(f'В индекс "{group_index}" залетела партия!', level='WARNING')

    "Добираем оставшееся/Обновляем индекс"
    if batch:
        await es_obj.bulk(body=batch, refresh=True)
    else:
        await es_obj.indices.refresh(index=group_index)

    "Индекс успешно поднят"
    return True

