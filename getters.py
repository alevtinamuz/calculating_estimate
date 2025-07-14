import sqlite3


def get_price_by_name(db_path, name: str):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    price = connection.execute(
        "SELECT price FROM works WHERE name = ?", (name,)
    ).fetchone()[0]

    return price


def get_materials_by_category(supabase, name_of_category: str):
    cat_id = supabase.table('material_categories').select('id').eq('name', name_of_category).execute().data[0]['id']
    print(cat_id)
    response = supabase.table('works').select('*').eq('name', 'Покраска карнизных и торцевых свесов в 2 слоя').execute()
    print(response.data)
