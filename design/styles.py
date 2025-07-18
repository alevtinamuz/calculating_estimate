from PyQt6.QtGui import QColor

# Стили для главного окна
MAIN_WINDOW_STYLE = """
    background-color: white;
"""

# Стили для метки
LABEL_STYLE = """
    QLabel {
        color: red;
        font-size: 48px;
        qproperty-alignment: AlignCenter;
    }
"""

# Стили для пустой кнопки
BUTTON_STYLE = """
    QPushButton {
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        min-height: 40px;
    }
    
    QPushButton:hover {
        background-color: #e0e0e0;
    }
"""

# Стили для кнопки закрытия
CLOSE_BUTTON_STYLE = """
    QPushButton {
        background-color: #ff6b6b;
        color: white;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
        border-radius: 4px;
    }
    
    QPushButton:hover {
        background-color: #ff5252;
    }
"""