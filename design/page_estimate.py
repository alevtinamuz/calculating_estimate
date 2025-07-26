from PyQt6.QtCore import Qt, QMarginsF, QPoint, QRectF
from PyQt6.QtGui import QPageSize, QPainter, QPageLayout, QFont
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, \
    QPushButton, QMainWindow, QFileDialog

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.class_TableManager import EstimateTableManager
from design.classes import MaterialItem, WorkItem
from design.styles import LABEL_STYLE, DATA_TABLE_STYLE, PRIMARY_BUTTON_STYLE, MESSAGE_BOX_STYLE


class PageEstimate(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        self.supabase = supabase
        self.table_estimate = None
        self.table_manager = None
        self.main_widget = None
        self.main_layout = None

    def create_page_estimate(self):
        """Создает страницу со сметой"""
        page_estimate = QWidget()
        layout = QVBoxLayout()

        self.main_widget = page_estimate
        self.main_layout = layout

        label_estimate = QLabel("Страница сметы")
        label_estimate.setStyleSheet(LABEL_STYLE)
        layout.addWidget(label_estimate)

        table_estimate = self.create_table_estimate()
        layout.addWidget(table_estimate)

        page_estimate.setLayout(layout)

        page_estimate.setStyleSheet(MESSAGE_BOX_STYLE)

        return page_estimate

    def create_table_estimate(self):
        """Создает таблицу для подсчета сметы"""
        try:
            estimate_container = QWidget()
            layout = QVBoxLayout(estimate_container)

            # Создаем таблицу как атрибут класса
            self.table_estimate = QTableWidget()

            self.table_manager = EstimateTableManager(self.table_estimate, self.supabase, self)

            layout.addWidget(self.table_estimate)

            button_panel = self.create_button_panel()
            layout.addWidget(button_panel)

            estimate_container.setLayout(layout)

            print("Таблица успешно создана")

            return estimate_container

        except Exception as e:
            self.show_error("Ошибка создания таблицы", str(e))
            print(f"Ошибка создания таблицы: {e}")
            raise

    def add_row_work(self):
        """Добавляет строку с работой в таблицу"""
        try:
            self.table_manager.add_row_work()

        except Exception as e:
            self.show_error("Не удалось добавить строку работы", str(e))

    def add_row_material(self):
        """Добавляет строку с материалами в таблицу для выбранной работы"""
        try:
            self.table_manager.add_row_material()

        except Exception as e:
            self.show_error("Не удалось добавить строку материалов", str(e))

    def delete_selected_work(self):
        """Удаляет выбранную работу"""
        try:
            self.table_manager.delete_selected_work()
        except Exception as e:
            self.show_error("Не удалось удалить работу", str(e))

    def delete_selected_material(self):
        """Удаляет выбранный материал"""
        try:
            self.table_manager.delete_selected_material()
        except Exception as e:
            self.show_error("Не удалось удалить материал", str(e))

    def clear_table(self):
        """Обработчик очистки таблицы"""
        try:
            self.table_manager.clear_all_data()
        except Exception as e:
            self.show_error("Ошибка очистки таблицы", str(e))

    def export_to_pdf(self):
        """Обработчик экспорта в PDF"""
        try:
            self.table_manager.export_to_pdf()
        except Exception as e:
            self.show_error("Ошибка экспорта в PDF", str(e))

    def create_button_panel(self):
        """Создает кнопки для добавления работ и материалов"""
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)

        add_work_btn = self.create_button("Добавить работу", lambda: self.add_row_work())
        add_material_btn = self.create_button("Добавить материал", lambda: self.add_row_material())
        delete_work_btn = self.create_button("Удалить работу", lambda: self.delete_selected_work())
        delete_material_btn = self.create_button("Удалить материал", lambda: self.delete_selected_material())
        clear_table_btn = self.create_button("Очистить таблицу", lambda: self.clear_table())
        export_pdf_btn = self.create_button("Экспорт в PDF", lambda: self.table_manager.actions.export_to_pdf())

        button_layout.addWidget(add_work_btn)
        button_layout.addWidget(add_material_btn)
        button_layout.addWidget(delete_work_btn)
        button_layout.addWidget(delete_material_btn)
        button_layout.addWidget(clear_table_btn)
        button_layout.addWidget(export_pdf_btn)

        return button_panel

    def create_button(self, text, handler):
        """Создает кнопку"""
        btn = QPushButton(text)
        btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        btn.clicked.connect(handler)

        return btn

    def show_error(self, title, message):
        """Выводит QMessageBox с ошибкой"""
        QMessageBox.critical(self, title, message)
