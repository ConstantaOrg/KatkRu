tables_to_truncate = [
    "cards_states_details",
    "cards_states_history",
    "std_ttable",
    "ttable_versions",
    "teachers_weekend",
    "teachers_buildings",
    "teachers",
    "groups",
    "specialties",
    "disciplines",
    "sessions_users",
    "users",
    "cards_statuses",
    "ttable_statuses",
    "buildings",
]
# print(', '.join(tables_to_truncate))




string = '''"Утверждено"
"В ожидании"
"Отклонено"'''

def add_symbols(text):
    text = text.replace('"', "'")
    texts = text.split("\n")
    for idx, rec in enumerate(texts):
        texts[idx] = f'({rec})'
    return ','.join(texts)



print(add_symbols(string))






