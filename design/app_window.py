import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QSpacerItem, QSizePolicy, 
                            QTableWidgetItem, QTableWidget, QHeaderView, 
                            QMessageBox, QToolButton, QStackedWidget,
                            QTabWidget)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt
from supabase import create_client, Client
from dotenv import load_dotenv
import setters

from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, TABLE_STYLE, TOOL_BUTTON_STYLE, TAB_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculating estimate")
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Инициализация Supabase
        load_dotenv()
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        # setters.add_work(self.supabase, 2, "каракуля", 88.88, "шт")

        # setters.add_work(self.supabase, 2, "каракуля", 88.88, "шт")
        # Словарь для хранения кнопок действий
        self.action_buttons = {}
        self.current_hovered_row = -1
        

        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet(MAIN_WINDOW_STYLE)
        self.setCentralWidget(central_widget)

        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Таблица для отображения данных
        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создаем страницы
        self.create_page_db()
        self.create_page_estimate()
        self.update_buttons_position()
        

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
        self.table.setMouseTracking(True)  # Включаем отслеживание мыши
        self.table.viewport().installEventFilter(self)  # Устанавливаем фильтр событий
        
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
        """Загружает данные из Supabase и отображает их в таблице"""
        try:
            response = self.supabase.table('works').select('*').execute()
            data = response.data

            if not data:
                self.label.setText("Нет данных для отображения")
                return
            if not data:
                self.label.setText("Нет данных для отображения")
                return

            # Очищаем предыдущие данные и кнопки
            self.table.clear()
            self.hide_all_tool_buttons()
            self.action_buttons.clear()
            
            # Устанавливаем размеры таблицы
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(data[0].keys()))
            
            # Устанавливаем заголовки
            headers = list(data[0].keys())
            self.table.setHorizontalHeaderLabels(headers)
            
            # Заполняем таблицу данными
            for row_idx, row_data in enumerate(data):
                for col_idx, (key, value) in enumerate(row_data.items()):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
                
                # Создаем кнопки действий
                edit_btn = QToolButton()
                edit_btn.setObjectName("editToolButton")
                edit_btn.setStyleSheet(TOOL_BUTTON_STYLE)
                edit_btn.setText("✏️")
                edit_btn.setToolTip("Редактировать")
                edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_row(r))
                
                delete_btn = QToolButton()
                delete_btn.setObjectName("deleteToolButton")
                delete_btn.setStyleSheet(TOOL_BUTTON_STYLE)
                delete_btn.setText("🗑️")
                delete_btn.setToolTip("Удалить")
                delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))
                
                # Размещаем кнопки поверх таблицы
                edit_btn.setParent(self.table.viewport())
                delete_btn.setParent(self.table.viewport())
                edit_btn.hide()
                delete_btn.hide()
                
                # Сохраняем ссылки на кнопки
                self.action_buttons[row_idx] = (edit_btn, delete_btn)
            
            # Настраиваем заголовки таблицы
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            self.table.verticalHeader().setVisible(False)
            self.table.setShowGrid(False)
            self.table.setFrameShape(QTableWidget.Shape.NoFrame)
            
            self.label.setText(f"Загружено {len(data)} записей")
            

            # Ресайз колонок по содержимому
            self.table.resizeColumnsToContents()
            self.label.setText("Данные успешно загружены")

        except Exception as e:
            self.label.setText(f"Ошибка загрузки: {str(e)}")
            print('Error:', e)
            
    def eventFilter(self, source, event):
        """Обработка событий мыши для показа/скрытия кнопок"""
        if source is self.table.viewport():
            if event.type() == QEvent.Type.MouseMove:
                index = self.table.indexAt(event.pos())
                if index.isValid():
                    self.show_tool_buttons(index.row(), event.pos())
                else:
                    self.hide_all_tool_buttons()
            elif event.type() == QEvent.Type.Leave:
                self.hide_all_tool_buttons()
        return super().eventFilter(source, event)
      
    def show_tool_buttons(self, row, pos):
      """Показывает кнопки для строки под курсором в крайней правой позиции"""
      if row != self.current_hovered_row:
          self.hide_all_tool_buttons()
          self.current_hovered_row = row
          
          if row in self.action_buttons:
              edit_btn, delete_btn = self.action_buttons[row]
              
              # Получаем прямоугольник всей строки
              rect = self.table.visualRect(self.table.model().index(row, 0))
              
              # Получаем ширину видимой области таблицы
              table_width = self.table.viewport().width()
              
              # Размеры кнопок
              btn_width = edit_btn.sizeHint().width()
              spacing = 5
              
              # Позиционируем кнопки в крайней правой части видимой области
              delete_btn.move(
                  table_width - btn_width - spacing,
                  rect.top() + (rect.height() - delete_btn.sizeHint().height()) // 2
              )
              
              edit_btn.move(
                  table_width - 2 * btn_width - 2 * spacing,
                  rect.top() + (rect.height() - edit_btn.sizeHint().height()) // 2
              )
              
              edit_btn.show()
              delete_btn.show()

    def hide_all_tool_buttons(self):
        """Скрывает все кнопки действий"""
        self.current_hovered_row = -1
        for buttons in self.action_buttons.values():
            for btn in buttons:
                btn.hide()
    
    def edit_row(self, row):
        """Обработка редактирования строки"""
        record_id = self.table.item(row, 0).text()
        print(f"Редактирование записи с ID: {record_id}")
        
    
    def delete_row(self, row):
        """Обработка удаления строки"""
        record_id = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Вы уверены, что хотите удалить запись с ID {record_id}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                setters.delete_work(self.supabase, record_id)
                self.label.setText(f"Запись с ID {record_id} удалена")
                self.load_data_from_supabase()
            except Exception as e:
                self.label.setText(f"Ошибка удаления: {str(e)}")
                print('Error:', e)
                
    def update_buttons_position(self):
      """Обновляет позиции кнопок при прокрутке или изменении размера"""
      if self.current_hovered_row >= 0:
          pos = self.table.viewport().mapFromGlobal(QCursor.pos())
          self.show_tool_buttons(self.current_hovered_row, pos)
          self.label.setText(f"Ошибка: {str(e)}")
