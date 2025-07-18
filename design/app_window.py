import os

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QSpacerItem, QSizePolicy,
                             QTableWidgetItem, QTableWidget, QStackedWidget,
                             QTabWidget)
from PyQt6.QtCore import Qt
from supabase import create_client, Client
from dotenv import load_dotenv

from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, CLOSE_BUTTON_STYLE, TABLE_STYLE, TAB_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hello World App")
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        load_dotenv()
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet(MAIN_WINDOW_STYLE)
        self.setCentralWidget(central_widget)

        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создаем страницы
        self.create_page_db()
        self.create_page_estimate()

        # Добавляем страницы во вкладки
        self.tabs.addTab(self.page_db, "База данных")
        self.tabs.addTab(self.page_estimate, "Смета")

        self.setStyleSheet(TAB_STYLE)

        # Показываем окно в полноэкранном режиме
        self.showMaximized()

    def create_page_db(self):
        """Создает первую страницу (база данных)"""
        self.page_db = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel("База данных")
        self.label.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.label)

        # Таблица для данных
        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Кнопка загрузки данных
        self.load_button = QPushButton("Загрузить данные")
        self.load_button.setStyleSheet(BUTTON_STYLE)
        self.load_button.clicked.connect(self.load_data_from_supabase)
        layout.addWidget(self.load_button)

        self.page_db.setLayout(layout)

    def create_page_estimate(self):
        """Создает вторую страницу (смета)"""
        self.page_estimate = QWidget()
        layout = QVBoxLayout()

        self.label_estimate = QLabel("Страница сметы")
        self.label_estimate.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.label_estimate)

        # Здесь можно добавить виджеты для работы со сметой

        self.page_estimate.setLayout(layout)

    def load_data_from_supabase(self):
        """Загружает данные из таблицы 'works' Supabase и отображает их в таблице"""
        try:
            # Получаем данные из Supabase
            response = self.supabase.table('works').select('*').execute()
            data = response.data

            if not data:
                self.label.setText("Нет данных для отображения")
                return

            # Настраиваем таблицу
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(data[0].keys()))
            self.table.setHorizontalHeaderLabels(data[0].keys())

            # Заполняем таблицу данными
            for row_idx, row_data in enumerate(data):
                for col_idx, (key, value) in enumerate(row_data.items()):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)

            # Ресайз колонок по содержимому
            self.table.resizeColumnsToContents()
            self.label.setText("Данные успешно загружены")

        except Exception as e:
            self.label.setText(f"Ошибка: {str(e)}")