def update_name_material_category(supabase, id, new_name):
  response = (
    supabase.table("materials_categories")
    .update({"name": new_name})
    .eq("id", id)
    .execute()
  )
  
def update_name_work_category(supabase, id, new_name):
  response = (
    supabase.table("works_categories")
    .update({"name": new_name})
    .eq("id", id)
    .execute()
  )
  
def update_name_section(supabase, id, new_name):
  response = (
    supabase.table("sections")
    .update({"name": new_name})
    .eq("id", id)
    .execute()
  )
  
def add_material_category(supabase, name):
  response = (
    supabase.table("materials_categories")
    .insert({"name": name})
    .execute()
  )

def add_work_category(supabase, name):
  response = (
    supabase.table("works_categories")
    .insert({"name": name})
    .execute()
  )
  
def add_section(supabase, name):
  response = (
    supabase.table("sections")
    .insert({"name": name})
    .execute()
  )
  
def update_name_of_materials(supabase, id, new_name):
  response = (
    supabase.table("materials")
    .update({"name": new_name})
    .eq("id", id)
    .execute()
  )
  
def update_name_of_work(supabase, id, new_name):
  response = (
    supabase.table("works")
    .update({"name": new_name})
    .eq("id", id)
    .execute()
  )
  
def update_category_id_of_material(supabase, id, new_category_id):
  response = (
    supabase.table("materials")
    .update({"category_id": new_category_id})
    .eq("id", id)
    .execute()
  )
  
def update_category_id_of_work(supabase, id, new_category_id):
  response = (
    supabase.table("works")
    .update({"category_id": new_category_id})
    .eq("id", id)
    .execute()
  )
  
def update_price_of_material(supabase, id, new_price):
  response = (
    supabase.table("materials")
    .update({"price": new_price})
    .eq("id", id)
    .execute()
  )
  
def update_price_of_work(supabase, id, new_price):
  response = (
    supabase.table("works")
    .update({"price": new_price})
    .eq("id", id)
    .execute()
  )
  
def update_unit_of_materials(supabase, id, new_unit):
  response = (
    supabase.table("materials")
    .update({"unit": new_unit})
    .eq("id", id)
    .execute()
  )
  
def update_unit_of_works(supabase, id, new_unit):
  response = (
    supabase.table("works")
    .update({"unit": new_unit})
    .eq("id", id)
    .execute()
  )

def update_keywords_of_work(supabase, id, new_keywords):
  response = (
    supabase.table("works")
    .update({"keywords": new_keywords})
    .eq("id", id)
    .execute()
  )

def update_keywords_of_materials(supabase, id, new_keywords):
  response = (
    supabase.table("materials")
    .update({"keywords": new_keywords})
    .eq("id", id)
    .execute()
  )
  
def add_material(supabase, category_id, name, price, unit, keywords):
  response = (
    supabase.table("materials")
    .insert({
            "category_id": category_id,
            "name": name,
            "price": price,
            "unit": unit,
            'keywords': keywords
            })
    .execute()
  )
  
def add_work(supabase, category_id, name, price, unit, keywords):
  response = (
    supabase.table("works")
    .insert({
            "category_id": category_id,
            "name": name,
            "price": price,
            "unit": unit,
            'keywords': keywords
            })
    .execute()
  )
  
def delete_material_category(supabase, id):
  response = (
    supabase.table("materials_categories")
    .delete()
    .eq("id", id)
    .execute()
  )
  
def delete_work_category(supabase, id):
  response = (
    supabase.table("works_categories")
    .delete()
    .eq("id", id)
    .execute()
  )
  
def delete_section(supabase, id):
  response = (
    supabase.table("sections")
    .delete()
    .eq("id", id)
    .execute()
  )
  
def delete_material(supabase, id):
  repsonse = (
    supabase.table("materials")
    .delete()
    .eq("id", id)
    .execute()
  )
  
def delete_work(supabase, id):
  repsonse = (
    supabase.table("works")
    .delete()
    .eq("id", id)
    .execute()
  )
  
def clear_table(supabase, name_of_table: str):
  repsonse = (
    supabase.table(name_of_table)
    .delete()
    .neq('id', '00000000-0000-0000-0000-000000000000')
    .execute()
  )
  
def upsert_work(supabase, category_id, name, price, unit, keywords):
    """Обновляет или создает работу (без указания ID)"""
    supabase.table('works').upsert({
        'category_id': category_id,
        'name': name,
        'price': price,
        'unit': unit,
        'keywords': keywords
    }).execute()

def upsert_material(supabase, category_id, name, price, unit, keywords):
    """Обновляет или создает материал (без указания ID)"""
    supabase.table('materials').upsert({
        'category_id': category_id,
        'name': name,
        'price': price,
        'unit': unit,
        'keywords': keywords
    }).execute()

def upsert_work_category(supabase, name):
    """Обновляет или создает категорию работ"""
    supabase.table('works_categories').upsert({
        'name': name
    }).execute()

def upsert_material_category(supabase, name):
    """Обновляет или создает категорию материалов"""
    supabase.table('materials_categories').upsert({
        'name': name
    }).execute()
    
def batch_insert_works_fast(supabase, items):
    """Быстрая пакетная вставка работ"""
    data = [{
        'category_id': item['category_id'],
        'name': item['name'],
        'price': item['price'],
        'unit': item['unit'],
        'keywords': item['keywords']
    } for item in items]
    supabase.table('works').insert(data, returning='minimal').execute()

def batch_insert_materials_fast(supabase, items):
    """Быстрая пакетная вставка материалов"""
    data = [{
        'category_id': item['category_id'],
        'name': item['name'],
        'price': item['price'],
        'unit': item['unit'],
        'keywords': item['keywords']
    } for item in items]
    supabase.table('materials').insert(data, returning='minimal').execute()

def batch_insert_work_categories_fast(supabase, items):
    """Быстрая пакетная вставка категорий работ"""
    data = [{'name': item['name']} for item in items]
    supabase.table('works_categories').insert(data, returning='minimal').execute()

def batch_insert_material_categories_fast(supabase, items):
    """Быстрая пакетная вставка категорий материалов"""
    data = [{'name': item['name']} for item in items]
    supabase.table('materials_categories').insert(data, returning='minimal').execute()
    
def batch_insert_work_categories_with_ids(supabase, items):
    """Пакетная вставка категорий работ с сохранением ID"""
    response = supabase.rpc('batch_insert_work_categories_with_ids', {
        'items': items
    }).execute()
    return response

def batch_insert_material_categories_with_ids(supabase, items):
    """Пакетная вставка категорий материалов с сохранением ID"""
    response = supabase.rpc('batch_insert_material_categories_with_ids', {
        'items': items
    }).execute()
    return response