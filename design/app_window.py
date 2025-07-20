import os

from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QCursor, QMovie
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QSizePolicy,
                             QTableWidgetItem, QTableWidget, QHeaderView,
                             QMessageBox, QToolButton, QTabWidget, QComboBox, QLineEdit, QApplication, QDialog,
                             QDialogButtonBox, QDoubleSpinBox, QFormLayout)
from dotenv import load_dotenv
from supabase import create_client, Client

import getters
import setters
from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.classes import WorkItem, MaterialItem
from design.page_db import PageDB
from design.page_estimate import PageEstimate
from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, TABLE_STYLE, TOOL_BUTTON_STYLE, TAB_STYLE, \
    TABLE_SELECTION_LAYOUT_STYLE, COMBO_BOX_STYLE


class MainWindow(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        self.setWindowTitle("Calculating estimate")
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # Инициализация Supabase
        self.supabase = supabase

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
        self.page_db = PageDB(supabase).create_page_db()
        self.page_estimate = PageEstimate(supabase).create_page_estimate()

        # Добавляем страницы во вкладки
        self.tabs.addTab(self.page_db, "База данных")
        self.tabs.addTab(self.page_estimate, "Смета")

        self.setStyleSheet(TAB_STYLE)

        # Показываем окно в полноэкранном режиме
        self.showMaximized()
