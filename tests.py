import sqlite3
import pandas


def get_works_by_category (db_path, category_name):
  pandas.set_option('display.max_colwidth', None)
  pandas.set_option('display.width', None) 
  pandas.set_option('display.max_rows', None)
  
  connection = sqlite3.connect(db_path)
  
  data = pandas.read_sql("""
                        SELECT 
                          works.name,
                          works.price,
                          works.unit
                        FROM works
                        JOIN works_categories ON works.category_id = works_categories.id
                        WHERE works_categories.name = ?
                        ORDER BY works.id
                          """, connection, params=[category_name]
                          )
  
  connection.close()
  return data



def get_materials_by_category(db_path, category_name):
  pandas.set_option('display.max_colwidth', None)
  pandas.set_option('display.width', None) 
  pandas.set_option('display.max_rows', None)
  
  connection = sqlite3.connect(db_path)
  
  data = pandas.read_sql("""
                        SELECT 
                          materials.name,
                          materials.price,
                          materials.unit
                        FROM materials
                        JOIN material_categories ON materials.category_id = material_categories.id
                        WHERE material_categories.name = ?
                        ORDER BY materials.id
                          """, connection, params=[category_name]
                        )
  
  connection.close()
  return data
