import os

arrow_path = os.path.join(os.path.dirname(__file__), "arrow.png").replace("\\", "/")

# Черно-белая палитра с приглушенным голубым акцентом
BLACK = "#000000"  # Основной черный
WHITE = "#FFFFFF"  # Чистый белый
LIGHT_GRAY = "#F5F5F5"  # Очень светлый серый для фона
DARK_GRAY = "#E5E5E5"  # Светло-серый для границ
ACCENT_BLUE = "#e5f4ff"  # Приглушенный голубой акцентный цвет

# Стили для главного окна
MAIN_WINDOW_STYLE = f"""
    QWidget {{
        background-color: {WHITE};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
"""

# Стили для меток
LABEL_STYLE = f"""
    QLabel {{
        color: {BLACK};
        font-size: 18px;
        font-weight: 500;
        qproperty-alignment: AlignCenter;
        padding: 5px;
    }}
"""

# Стили для основных кнопок (черные)
PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {WHITE};
        color: {BLACK};
        border: 2px solid {LIGHT_GRAY};
        border-radius: 4px;
        font-size: 14px;
        min-width: 120px;
        min-height: 30px;
    }}

    QPushButton:hover {{
        background-color: {LIGHT_GRAY};
        color: {BLACK};
    }}

    QPushButton:pressed {{
        background-color: {ACCENT_BLUE};
        border-color: {ACCENT_BLUE};
        color: {BLACK};
    }}
"""

# Стили для таблицы
DATA_TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {WHITE};
        border: none;
        color: {BLACK};
        gridline-color: {DARK_GRAY};
        outline: 0;
        font-size: 14px;
    }}

    QHeaderView::section {{
        background-color: {LIGHT_GRAY};
        padding: 8px;
        border: 1px solid {DARK_GRAY};
        color: {BLACK};
        font-weight: 600;
    }}

    QTableWidget::item {{
        padding: 6px;
        border-right: 1px solid {DARK_GRAY};
        border-bottom: 1px solid {DARK_GRAY};
    }}

    QTableWidget::item:selected {{
        background-color: {ACCENT_BLUE};
        color: {BLACK};
        font-weight: bold;
    }}

    QTableCornerButton::section {{
        background: {LIGHT_GRAY};
        border: 2px solid {DARK_GRAY};
    }}
"""

SEARCH_STYLE = f"""
    QLineEdit {{
        background-color: {WHITE};
        color: {BLACK};
        border: 2px solid {DARK_GRAY};
        border-radius: 4px;
        min-height: 30px;
        font-size: 14px;
        min-width: 200px;
    }}
    
    QLineEdit:hover {{
        background-color: {LIGHT_GRAY};
    }}
    
    QLineEdit::placeholder {{
        color: {DARK_GRAY};
        font-style: italic;
    }}
"""

# Стили для выпадающих списков
DROPDOWN_STYLE = f"""
    QComboBox {{
        background-color: {WHITE};
        color: {BLACK};
        border: 2px solid {DARK_GRAY};
        border-radius: 1px;
        min-width: 180px;
        min-height: 30px;
        font-size: 14px;
        selection-background-color: {ACCENT_BLUE};
        selection-color: {WHITE};
    }}

    QComboBox:hover {{
        background-color: {LIGHT_GRAY};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 2px solid {DARK_GRAY};
    }}

    QComboBox::down-arrow {{
        image: url({arrow_path});
        width: 14px;
        height: 14px;
    }}

    QComboBox QAbstractItemView {{
        border: 2px solid {DARK_GRAY};
        background: {WHITE};
        color: {BLACK};
        selection-background-color: {ACCENT_BLUE};
        selection-color: {WHITE};
        outline: none;
        font-size: 14px;
    }}
"""

DROPDOWN_DELEGATE_STYLE = f"""
    QLineEdit {{
        background-color: {WHITE};
        color: {BLACK};
        border: 2px solid {DARK_GRAY};
        border-radius: 4px;
        min-height: 30px;
        font-size: 14px;
        min-width: 200px;
    }}
    
    QListWidget {{
        background-color: {WHITE};
        color: {BLACK};
        font-size: 8pt;
        padding: 2px;
        min-height: 300px;
    }}
    
    QListWidget::item {{
        padding: 2px;
    }}
    
    QListWidget::item:selected {{
        background: {ACCENT_BLUE};
        color: {BLACK};
    }}
    
    QListWidget::item:focus {{
        border: none !important; 
        outline: none !important;
    }}
    
    #MainList {{
        min-width: 170px;
    }}
    
    #SubList {{
        min-width: 350px;
    }}
"""

# Стиль для панелей инструментов
TOOL_PANEL_STYLE = f"""
    QHBoxLayout, QVBoxLayout {{
        background-color: {WHITE};
        border-radius: 4px;
        border: 2px solid {DARK_GRAY};
        margin: 0;
        padding: 0;
    }}
"""

# Стили для кнопок действий
ACTION_BUTTONS_STYLE = f"""
    QToolButton {{
        background-color: {WHITE};
        border: 2px solid {DARK_GRAY};
        border-radius: 4px;
        min-width: 24px;
        min-height: 24px;
    }}

    QToolButton:hover {{
        background-color: {LIGHT_GRAY};
    }}

    QToolButton:pressed {{
        background-color: {ACCENT_BLUE};
        color: {BLACK};
    }}
"""

# Стили для вкладок
TAB_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background: {WHITE};
    }}

    QTabBar::tab {{
        background: {LIGHT_GRAY};
        color: {BLACK};
        padding: 8px 16px;
        border: 2px solid {DARK_GRAY};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}

    QTabBar::tab:selected {{
        background: {WHITE};
        color: {BLACK};
        border-color: {DARK_GRAY};
        font-weight: bold;
    }}

    QTabBar::tab:hover {{
        background: {WHITE};
    }}
"""

# Стили для контекстных меню
CONTEXT_MENU_STYLE = f"""
    QMenu {{
        background-color: {WHITE};
        border: 2px solid {DARK_GRAY};
        padding: 4px;
    }}

    QMenu::item {{
        padding: 6px 24px 6px 16px;
        color: {BLACK};
    }}

    QMenu::item:selected {{
        background-color: {ACCENT_BLUE};
        color: {WHITE};
        font-weight: bold;
    }}
"""

SPIN_BOX_STYLE = """
    QSpinBox {
        background-color: white;
        color: black;
    }
    
    QTableWidget QSpinBox {
        color: black !important;
    }
    
    /* Стиль для текста при редактировании */
    QAbstractItemView:edit {
        color: black !important;
    }
"""
