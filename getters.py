import sqlite3


def get_price_by_name(db_path, name: str):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    price = connection.execute(
        "SELECT price FROM works WHERE name = ?", (name,)
    ).fetchone()[0]

    return price


def get_materials_by_category(supabase, name_of_category: str):
    cat_id = supabase.table('materials_categories').select('id').eq('name', name_of_category).execute().data[0]['id']
    response = supabase.table('materials').select('*').eq('category_id', cat_id).execute()

    return response.data


def get_works_by_category(supabase, name_of_category: str):
    cat_id = supabase.table('works_categories').select('id').eq('name', name_of_category).execute().data[0]['id']
    response = supabase.table('works').select('*').eq('category_id', cat_id).execute()

    return response.data


def get_materials_by_substr(supabase, substr):
    response = supabase.table('materials').select('*').ilike('name', f'%{substr}%').execute()

    return response.data


def get_entity_by_substr(supabase, name_of_table: str, substr, cat_id: int = 0):
    if cat_id:
        response = supabase.table(name_of_table).select('*').eq('category_id', cat_id).ilike('name', f'%{substr}%').execute()
    else:
        response = supabase.table(name_of_table).select('*').ilike('name', f'%{substr}%').execute()

    return response.data


def get_works_by_substr(supabase, substr):
    response = supabase.table('works').select('*').ilike('name', f'%{substr}%').execute()

    return response.data


def get_all_table(supabase, name_of_table: str):
    response = supabase.table(name_of_table).select('*').execute()
    
    return response.data

def get_entity_by_id(supabase, name_of_table: str, entity_id: int):
    if entity_id:
        response = supabase.table(name_of_table).select('*').eq('id', entity_id).execute()
    
        return response.data
    else:
        data = [{'id': 0, 'category_id': 0, 'name': '-', 'price': 0, 'unit': '-'}]

        return data


def sort_by_id(supabase, name_of_table: str, sort_column):
    response = supabase.table(name_of_table).select('*').order(sort_column, desc=False).execute()
    
    return response.data
