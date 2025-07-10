import sqlite3
import pandas



def create_database_structue (db_path):
  connection = sqlite3.connect(db_path)
  cursor = connection.cursor()
  
  cursor.execute("DROP TABLE IF EXISTS materials")
  cursor.execute("DROP TABLE IF EXISTS material_categories")
  
  
  cursor.execute("""
                CREATE TABLE material_categories(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE
                  )
                  """)
  
  cursor.execute("""
                CREATE TABLE materials(
                  id INTEGER PRIMARY KEY,
                  category_id INTEGER,
                  name TEXT NOT NULL,
                  price REAL NOT NULL,
                  unit TEXT NOT NULL,
                  FOREIGN KEY (category_id) REFERENCES material_categories(id)
                )
                """)
  
  connection.commit()
  connection.close()
  


def import_from_excel (excel_path, db_path):
  connection = sqlite3.connect(db_path)
  excel = pandas.ExcelFile(excel_path)
  
  material_categories = []
  for sheet in excel.sheet_names:
    if sheet not in ["Главная"] and not sheet.startswith("Лист"):
      material_categories.append((sheet,))
      
  connection.executemany("INSERT INTO material_categories (name) VALUES (?)", material_categories)
  connection.commit()
  
  for sheet in excel.sheet_names:
    if sheet not in ["Главная"] and not sheet.startswith("Лист"):
      data = pandas.read_excel(excel_path, sheet_name=sheet, skiprows=2)
      
      data = data.dropna(subset=["Наименование"])
      
      if not all(column in data.columns for column in ["Наименование", "Стоимость", "Ед. изм."]):
        continue
      
      category_id = connection.execute(
        "SELECT id FROM material_categories WHERE name = ?", (sheet,)
      ).fetchone()[0]
      
      materials = []
      for _, row in data.iterrows():
        materials.append((
          category_id,
          str(row["Наименование"]).strip(),
          float(str(row["Стоимость"]).replace(" руб.", "").replace(",", "").strip()),
          str(row["Ед. изм."]).strip(),
        ))
      
      if materials:
        connection.executemany(
                              "INSERT INTO materials (category_id, name, price, unit) VALUES (?, ?, ?, ?)", materials
                              )
  connection.commit()
  connection.close()