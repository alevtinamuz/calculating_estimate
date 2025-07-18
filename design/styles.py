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


TABLE_STYLE = """
    QTableWidget {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        color: black;
    }
    QHeaderView::section {
        background-color: #e9ecef;
        padding: 5px;
        border: 1px solid #dee2e6;
        color: black;
    }
"""


TOOL_BUTTON_STYLE = """
    QToolButton {
        background-color: rgba(255, 255, 255, 150);
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 2px;
        margin: 1px;
    }
    QToolButton:hover {
        background-color: rgba(255, 255, 255, 200);
    }
    #editToolButton {
        background-color: rgba(76, 175, 80, 150);
    }
    #deleteToolButton {
        background-color: rgba(244, 67, 54, 150);
    }
"""