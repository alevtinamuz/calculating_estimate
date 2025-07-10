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
                        JOIN categories ON works.category_id = categories.id
                        WHERE categories.name = ?
                        ORDER BY works.id
                          """, connection, params=[category_name]
                          )
  
  return data