from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

import getters
import setters
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("design/untitled.ui", self)

        self.setWindowTitle("Calculating estimate")

        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")

        self.setup_page_switching()

    def setup_page_switching(self):
        # Словарь для связи кнопок с индексами страниц
        self.page_buttons = {
            "pushButton_current_estimate": 0,
            "pushButton_drafts": 1,
            "pushButton_estimates": 2,
            "pushButton_data": 3
        }

        for button_name, page_index in self.page_buttons.items():
            button = self.findChild(QPushButton, button_name)
            button.clicked.connect(lambda _, idx=page_index: self.switch_page(idx))

    def switch_page(self, page_index):
        self.stacked_widget.setCurrentIndex(page_index)



load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

app = QApplication(sys.argv)

window = MainWindow()
window.show()
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

# setters.add_work(supabase, 2, "каракуля", 88.88, "шт")

# setters.add_work(supabase, 2, "каракуля", 88.88, "шт")

# setters.delete_work(supabase, 219)