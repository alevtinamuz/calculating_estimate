# Стили для главного окна
MAIN_WINDOW_STYLE = """
    QWidget {
        background-color: white;
    }
"""

# Стили для метки
LABEL_STYLE = """
    QLabel {
        color: black;
        font-size: 24px;
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
    QTableWidget::item:selected {
        background-color: #e6f3ff;
        color: black;
    }
    QTableWidget {
        gridline-color: transparent;
        show-decoration-selected: 1; /* Показывать выделение на всей строке */
    }
    
    QTableWidget::item:edit-focus {
        color: black;
    }
    
    QLineEdit {
        color: black;
        background-color: white;
        selection-color: white;
        selection-background-color: #0078d7;
    }
    QSpinBox {
        color: black;
        background-color: white;
    }
"""


TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background: white;
    }

    QTabBar::tab {
        background: white;
        color: black;
        padding: 8px 16px;
        border: 1px solid #ddd;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }

    QTabBar::tab:selected {
        background: white;
        color: black;
        border-color: #aaa;
        font-weight: bold;
    }

    QTabBar::tab:!selected {
        background: #f0f0f0;
    }

    QTabBar::tab:hover {
        background: #e9e9e9;
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

COMBO_BOX_STYLE = """
    QComboBox {
        background-color: white;
        color: black;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px;
        min-width: 150px;
    }

    QComboBox:hover {
        border: 1px solid #aaa;
    }

    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 1px;
        border-left-color: #ccc;
        border-left-style: solid;
    }

    QComboBox::down-arrow {
        image: url(icons/down_arrow.png);
        width: 12px;
        height: 12px;
    }

    QComboBox QAbstractItemView {
        background-color: white;
        color: black;
        selection-background-color: #e0e0e0;
        selection-color: black;
        border: 1px solid #ccc;
    }
"""

TABLE_SELECTION_LAYOUT_STYLE = """
    QHBoxLayout {
        background-color: white;
        padding: 10px;
        border-radius: 4px;
        border: 1px solid #eee;
    }
"""

MENU_STYLE = """
    QMenu {
        background-color: white;
        border: 1px solid #ccc;
    }
    QMenu::item {
        padding: 5px 25px 5px 20px;
        color: black;
    }
    QMenu::item:selected {
        background-color: #e6f3ff;
    }
"""