import sqlite3
import pandas



# функция для создания структуры базы данных
def create_database_structure (db_path):
  # создаем файл и подключаемся
  connection = sqlite3.connect(db_path)
  cursor = connection.cursor()
  
  # удаляем таблицу, если существует (нужно для переобновления данных)
  # пока так, потом оптимизируем
  cursor.execute("DROP TABLE IF EXISTS works")
  cursor.execute("DROP TABLE IF EXISTS works_categories")
  
  # создаем таблицу для категорий работ, у каждой категории свой уникальный айдишник
  # и они будут использоваться для связи со второй таблицей (непосредственно с всеми работами)
  # название текстом и обязательно непустое и уникальное
  cursor.execute("""
                CREATE TABLE works_categories(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE
                  )
                  """)
  
  # создаем таблицу для всех работ
  # у каждой работы свой уникальный айдишник
  # айдишник категории - для связи с категориями
  # имя работы - текст (непустой обязательно)
  # цена - стоимость работы (дробное число) (обязательная)
  # единица измерения (unit) - текс (обязательное поле) ("м2", "м.п.", "шт" и т.д.)
  cursor.execute("""
                CREATE TABLE works(
                  id INTEGER PRIMARY KEY,
                  category_id INTEGER,
                  name TEXT NOT NULL,
                  price REAL NOT NULL, 
                  unit TEXT NOT NULL,
                  FOREIGN KEY (category_id) REFERENCES works_categories(id)
                )
                """)
  
  connection.commit()
  connection.close()


# функция для импорта из экселевского файла
def import_from_excel (excel_path, db_path):
  # создаем соединение с базой данныых и импортируем данные из excel файла 
  connection = sqlite3.connect(db_path)
  excel = pandas.ExcelFile(excel_path)
  
  # проходимся по всем листам из файла excel
  # кроме листа "Главная" и остальных пустых листов (начинаются с "Лист")
  # далее выполняем множественную вставку данных в таблицу works_categories базы данных
  # works_categories = [("Фасадные работы",), ("Кровельные работы",), ...] - список кортежей (для работы c sqlite)
  works_categories = []
  for sheet in excel.sheet_names:
    if sheet not in ["Главная"] and not sheet.startswith("Лист"):
      works_categories.append((sheet,))
      
  connection.executemany("INSERT INTO works_categories (name) VALUES (?)", works_categories)
  connection.commit()
  
  # также проходимся по листам, кроме пустых или ненужных
  # считываем данные из файла (по каждой категории, пропуская первые две строки)
  # далее удаляем пустые строки (проверяем только столбец "Наименование работ")
  # проверяем на то, есть ли нужные столбцы в листе, если нет, то пропуск
  # далее получаем id категории, которую просматриваем на данный момент
  for sheet in excel.sheet_names: 
    if sheet not in ["Главная"] and not sheet.startswith("Лист"):
      data = pandas.read_excel(excel_path, sheet_name=sheet, skiprows=2)
      
      data = data.dropna(subset=["Наименование работ"])
      
      if not all (column in data.columns for column in ["Наименование работ", "Стоимость", "Ед. изм."]):
        continue
      
      category_id = connection.execute(
                                      "SELECT id FROM works_categories WHERE name = ?", (sheet,)
                                      ).fetchone()[0]
      
      works = []
      # заполняем массив works (подготавливаем перед вставкой в бд)
      # итерируемся по номеру строки(id строки) и по данным в строке
      # айди категории вычислили на предыдущем шаге
      # название работы записываем строкой (в базе хранится текстом), убираем лишние пробелы
      # стоимость переводим в float
      # единицы измерения также записываем строкой, убираем пробелы
      for _, row in data.iterrows():
        works.append((
          category_id,
          str(row["Наименование работ"]).strip(),
          float(row["Стоимость"]),
          str(row["Ед. изм."]).strip()
        ))
      
      if works:
        connection.executemany(
                              "INSERT INTO works (category_id, name, price, unit) VALUES (?, ?, ?, ?)", works
                              )
      
  connection.commit()
  connection.close()
  