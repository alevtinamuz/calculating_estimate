import sqlite3


def get_price_by_name(db_path, name: str):
  # создаем файл и подключаемся
  connection = sqlite3.connect(db_path)
  cursor = connection.cursor()

  price = connection.execute(
      "SELECT price FROM works WHERE name = ?", (name,)
  ).fetchone()[0]

  return price