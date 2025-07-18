from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

import getters
import setters
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic
from design.app_window import MainWindow


# load_dotenv()
# supabase: Client = create_client(
#     os.getenv("SUPABASE_URL"),
#     os.getenv("SUPABASE_KEY")
# )

app = QApplication(sys.argv)

window = MainWindow()
window.show()  # Хотя showFullScreen() уже вызван в классе

sys.exit(app.exec())

# cat_name = 'Утеплители'
# getters.get_materials_by_category(supabase, cat_name)

# cat_name = 'Барабашка'
# getters.get_materials_by_category(supabase, cat_name)

# cat_name = 'Напольные покрытия'
# getters.get_works_by_category(supabase, cat_name)
# cat_name = 'Утеплители'
# getters.get_materials_by_category(supabase, cat_name)

# response = supabase.table('works').select('price').eq('name', 'Покраска фасада в два слоя').execute()
# print(response.data[0])

# substr = 'утЕплИтеЛь'
# getters.get_materials_by_substr(supabase, substr)
#
# substr = 'Покраска'
# getters.get_works_by_substr(supabase, substr)

# response = supabase.table('works').select('*').ilike('name', f'%{str}%').execute()
# print(response.data)

# #
# str = 'Покраска'
# response = supabase.table('works').select('*').ilike('name', f'%{str}%').execute()

# response = supabase.table('works').select('*').execute()
# print(response.data)

setters.add_work(supabase, 2, "каракуля", 88.88, "шт")

setters.add_work(supabase, 2, "каракуля", 88.88, "шт")

# setters.delete_work(supabase, 219)
# setters.add_material_category(supabase, "gg")
# setters.add_material(supabase, 16, "hh", 11, "mm")
# setters.add_material(supabase, 16, "gg", 11, "mm")
# setters.add_material(supabase, 16, "qwqw", 11, "mm")
# setters.delete_material_category(supabase, 16)