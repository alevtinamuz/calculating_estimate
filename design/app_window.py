import os

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QSpacerItem, QSizePolicy, QTableWidgetItem, QTableWidget)
from PyQt6.QtCore import Qt
from supabase import create_client, Client
from dotenv import load_dotenv

from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, CLOSE_BUTTON_STYLE, TABLE_STYLE


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
        self.setCentralWidget(central_widget)
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Таблица для отображения данных из Supabase
        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) 

        main_layout.addWidget(self.table)

        # Кнопка для загрузки данных
        self.load_button = QPushButton("Загрузить данные")
        self.load_button.setStyleSheet(BUTTON_STYLE)
        self.load_button.clicked.connect(self.load_data_from_supabase)
        main_layout.addWidget(self.load_button)
        
        # Метка с текстом
        self.label = QLabel("Hello, world?")
        self.label.setStyleSheet(LABEL_STYLE)
        main_layout.addWidget(self.label)
        
        # Пустая кнопка
        self.button = QPushButton("")
        self.button.setStyleSheet(BUTTON_STYLE)
        main_layout.addStretch()  # Растягиваемое пространство
        main_layout.addWidget(self.button)
        
        # Горизонтальный layout для кнопки закрытия (внизу справа)
        bottom_layout = QHBoxLayout()
        
        # Добавляем растягиваемое пространство слева
        bottom_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Кнопка закрытия
        self.close_button = QPushButton("Закрыть")
        self.close_button.setStyleSheet(CLOSE_BUTTON_STYLE)
        self.close_button.clicked.connect(self.close)  # Подключаем закрытие окна
        bottom_layout.addWidget(self.close_button)
        
        main_layout.addLayout(bottom_layout)
        
        # Показываем окно в полноэкранном режиме
        self.showMaximized()


    def load_data_from_supabase(self):
        """Загружает данные из таблицы 'works' Supabase и отображает их в таблице"""
        try:
            # Получаем данные из Supabase
            response = self.supabase.table('works').select('*').execute()
            data = response.data

            # if not data:
            #     self.label.setText("Нет данных для отображения")
            #     return

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
            # self.label.setText("Данные успешно загружены")

        except Exception as e:
            print('111')
            # self.label.setText(f"Ошибка: {str(e)}")