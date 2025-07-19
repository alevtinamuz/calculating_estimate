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
  
def add_material(supabase, category_id, name, price, unit):
  response = (
    supabase.table("materials")
    .insert({
            "category_id": category_id,
            "name": name,
            "price": price,
            "unit": unit
            })
    .execute()
  )
  
def add_work(supabase, category_id, name, price, unit):
  response = (
    supabase.table("works")
    .insert({
            "category_id": category_id,
            "name": name,
            "price": price,
            "unit": unit
            })
    .execute()
  )
  
def delete_material_category(supabase, id):
  response = (
    supabase.table("materials")
    .delete()
    .eq("category_id", id)
    .execute(),
    
    supabase.table("materials_categories")
    .delete()
    .eq("id", id)
    .execute()
  )
  
def delete_work_category(supabase, id):
  response = (
    supabase.table("works")
    .delete()
    .eq("category_id", id)
    .execute(),
    
    supabase.table("works_categories")
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