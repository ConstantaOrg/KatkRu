from elasticsearch import AsyncElasticsearch

from core.utils.logger import log_event


async def fill_spec_index(records, spec_index, es_obj: AsyncElasticsearch):
    batch = []
    for record in records:
        batch.append({'index': {'_index': spec_index, '_id': record['id']}})  # action
        batch.append({
            "code_autocomplete": record['spec_code'],
            "title": record['title'],
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
    log_event(f'В индекс "{spec_index}" залетела партия!', level='WARNING')

    "Индекс успешно поднят"
    return True


async def fill_group_index(records, group_index, es_obj: AsyncElasticsearch):
    batch = []
    for record in records:
        batch.append({'index': {'_index': group_index, '_id': record['id']}})  # action
        batch.append({
            "group_name": record['name'],
            "is_active": record['is_active']
        })

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
    log_event(f'В индекс "{group_index}" залетела партия!', level='WARNING')

    "Индекс успешно поднят"
    return True


async def fill_disciplines_index(records, disciplines_index, es_obj: AsyncElasticsearch):
    batch = []
    for record in records:
        batch.append({'index': {'_index': disciplines_index, '_id': record['id']}})  # action
        batch.append({
            "title": record['title'],
            "is_active": record['is_active']
        })

        "Батч-вставка"
        if len(batch) >= 2000:
            await es_obj.bulk(body=batch)
            batch.clear()
            log_event(f'В индекс "{disciplines_index}" залетела партия!', level='WARNING')

    "Добираем оставшееся/Обновляем индекс"
    if batch:
        await es_obj.bulk(body=batch, refresh=True)
    else:
        await es_obj.indices.refresh(index=disciplines_index)
    log_event(f'В индекс "{disciplines_index}" залетела партия!', level='WARNING')

    "Индекс успешно поднят"
    return True


async def fill_teachers_index(records, teachers_index, es_obj: AsyncElasticsearch):
    batch = []
    for record in records:
        batch.append({'index': {'_index': teachers_index, '_id': record['id']}})  # action
        batch.append({
            "fio": record['fio'],
            "is_active": record['is_active']
        })

        "Батч-вставка"
        if len(batch) >= 2000:
            await es_obj.bulk(body=batch)
            batch.clear()
            log_event(f'В индекс "{teachers_index}" залетела партия!', level='WARNING')

    "Добираем оставшееся/Обновляем индекс"
    if batch:
        await es_obj.bulk(body=batch, refresh=True)
    else:
        await es_obj.indices.refresh(index=teachers_index)
    log_event(f'В индекс "{teachers_index}" залетела партия!', level='WARNING')

    "Индекс успешно поднят"
    return True

