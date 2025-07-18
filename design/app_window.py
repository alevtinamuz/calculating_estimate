from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt
from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, CLOSE_BUTTON_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Hello World App")
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
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
        self.showFullScreen()