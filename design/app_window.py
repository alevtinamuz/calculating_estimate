from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget)
from design.page_db import PageDB
from design.page_estimate import PageEstimate
from design.styles import MAIN_WINDOW_STYLE, TAB_STYLE
import os
from PyQt6.QtGui import QIcon


class MainWindow(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        icon_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Estimate Calculator")
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # Инициализация Supabase
        self.supabase = supabase

        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet(MAIN_WINDOW_STYLE)
        self.setCentralWidget(central_widget)

        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        # main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создаем страницы
        self.page_db = PageDB(supabase).create_page_db()
        self.page_estimate = PageEstimate(supabase).create_page_estimate()

        # Добавляем страницы во вкладки
        self.tabs.addTab(self.page_db, "База данных")
        self.tabs.addTab(self.page_estimate, "Смета")

        self.setStyleSheet(TAB_STYLE)

        # Показываем окно в полноэкранном режиме
        self.showMaximized()