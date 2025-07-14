import sqlite3
import csv
import os

def db_to_csv(db_path, output_folder):
    # Подключаемся к SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем папку для CSV, если её нет
    os.makedirs(output_folder, exist_ok=True)
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        # Запрос данных из таблицы
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        # Получаем названия столбцов
        col_names = [description[0] for description in cursor.description]
        
        # Сохраняем в CSV
        csv_path = os.path.join(output_folder, f"{table_name}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(col_names)  # Заголовки
            writer.writerows(data)     # Данные
        
        print(f"Таблица '{table_name}' сохранена в {csv_path}")
    
    conn.close()

# Использование
db_to_csv("materials_cost.db", "csv")