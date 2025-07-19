import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QSpacerItem, QSizePolicy,
                             QTableWidgetItem, QTableWidget, QHeaderView,
                             QMessageBox, QToolButton, QStackedWidget,
                             QTabWidget, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QCursor
from supabase import create_client, Client
from dotenv import load_dotenv
import setters

from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, TABLE_STYLE, TOOL_BUTTON_STYLE, TAB_STYLE, \
    TABLE_SELECTION_LAYOUT_STYLE, COMBO_BOX_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculating estimate")
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # Инициализация Supabase
        self.supabase_init()

        # Словарь для хранения кнопок действий
        self.action_buttons = {}
        self.current_hovered_row = -1
        self.current_table = 'works'

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

        table_selection_layout_widget = self.create_table_selector()
        layout.addWidget(table_selection_layout_widget)

        self.label = QLabel("База данных")
        self.label.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.label)

        # Таблица для данных
        self.table_db = self.create_table_db()
        layout.addWidget(self.table_db)

        self.refresh_button = self.create_refresh_button()
        layout.addWidget(self.refresh_button)

        self.load_data_from_supabase()
        
        self.page_db.setLayout(layout)

    def on_table_changed(self, table_name):
        """Обработчик изменения выбранной таблицы"""
        self.current_table = table_name
        self.load_data_from_supabase()

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
            data = []
            batch_size = 1000
            for i in range(0, 2500, batch_size):
                batch = self.supabase.table(self.current_table).select('*').range(i, i + batch_size - 1).execute()
                data.extend(batch.data)

            if not data:
                self.label.setText("Нет данных для отображения")
                return

            # Очищаем предыдущие данные и кнопки
            self.table_db.clear()
            self.hide_all_tool_buttons()
            self.action_buttons.clear()

            # Устанавливаем размеры таблицы
            self.table_db.setRowCount(len(data))
            self.table_db.setColumnCount(len(data[0].keys()))

            # Устанавливаем заголовки
            headers = list(data[0].keys())
            self.table_db.setHorizontalHeaderLabels(headers)

            # Заполняем таблицу данными
            for row_idx, row_data in enumerate(data):
                for col_idx, (key, value) in enumerate(row_data.items()):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_db.setItem(row_idx, col_idx, item)

                # if self.current_table == 'works':
                    edit_btn = self.create_edit_btn(row_idx)
                    delete_btn = self.create_delete_btn(row_idx)
                    self.action_buttons[row_idx] = (edit_btn, delete_btn)
                # # Создаем кнопки действий
                # edit_btn = self.create_edit_btn(row_idx)
                # delete_btn = self.create_delete_btn(row_idx)
                #
                # # Сохраняем ссылки на кнопки
                # self.action_buttons[row_idx] = (edit_btn, delete_btn)

            # Настраиваем заголовки таблицы
            header = self.table_db.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            self.table_db.verticalHeader().setVisible(False)
            self.table_db.setShowGrid(False)
            self.table_db.setFrameShape(QTableWidget.Shape.NoFrame)

            # self.label.setText(f"Загружено {len(data)} записей")

            # Ресайз колонок по содержимому
            self.table_db.resizeColumnsToContents()
            # self.label.setText("Данные успешно загружены")
            self.table_db.setStyleSheet(TABLE_STYLE)
            self.adjust_column_widths()
            print("Данные обновлены")

        except Exception as e:
            self.label.setText(f"Ошибка загрузки: {str(e)}")
            print('Error:', e)

    def eventFilter(self, source, event):
        """Обработка событий мыши для показа/скрытия кнопок"""
        if source is self.table_db.viewport():
            if event.type() == QEvent.Type.MouseMove:
                index = self.table_db.indexAt(event.pos())
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
                self.set_pos_action_buttons(row)

    def hide_all_tool_buttons(self):
      """Скрывает все кнопки, кроме кнопок выбранной строки"""
      selected_row = self.get_selected_row()
      for row, buttons in self.action_buttons.items():
          if row != selected_row:
              for btn in buttons:
                  btn.hide()
                  
    def get_selected_row(self):
      """Возвращает номер выбранной строки или -1 если нет выбора"""
      selected = self.table_db.selectedItems()
      return selected[0].row() if selected else -1

    def edit_row(self, row):
        """Обработка редактирования строки"""
        record_id = self.table_db.item(row, 0).text()
        
        # if self.current_table in ['works', 'materials']:
        #   msg_box = QMessageBox(self)
        #   msg_box.setWindowTitle('Изменить запись')
        #   msg_box.setText('Введите новое название:')
        #   input_field = QLineEdit()
        #   input_field.setPlaceholderText('Новое название.')
        #   msg_box.layout().addWidget(input_field, 1, 1)
        #   msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        #   msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        print(f"Редактирование записи с ID: {record_id}")

    def delete_row(self, row):
        """Обработка удаления строки"""
        record_id = self.table_db.item(row, 0).text()

        if self.current_table in ['works', 'materials']:
          reply = QMessageBox.question(
              self, 'Удаление записи',
              f'Вы уверены, что хотите удалить запись с ID {record_id}?',
              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
          )
        elif self.current_table in ['works_categories', 'materials_categories']:
          reply = QMessageBox.question(
              self, 'Удаление категории',
              f'Вы уверены, что хотите удалить категорию с ID {record_id}?',
              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
          )

        if reply == QMessageBox.StandardButton.Yes:
            try:
              if self.current_table == 'works':
                setters.delete_work(self.supabase, record_id)
              elif self.current_table == 'materials':
                setters.delete_material(self.supabase, record_id)
              elif self.current_table == 'works_categories':
                setters.delete_work_category(self.supabase, record_id)
              elif self.current_table == 'materials_categories':
                setters.delete_material_category(self.supabase, record_id)
              if self.current_table in ['works', 'materials']:
                self.label.setText(f"Запись с ID {record_id} удалена")
              elif self.current_table in ['works_categories', 'materials_categories']:
                self.label.setText(f"Категория с ID {record_id} удалена")
              self.load_data_from_supabase()
            except Exception as e:
                self.label.setText(f"Ошибка удаления: {str(e)}")
                print('Error:', e)

    def update_buttons_position(self):
        """Обновляет позиции кнопок при прокрутке или изменении размера"""
        if self.current_hovered_row >= 0:
            pos = self.table_db.viewport().mapFromGlobal(QCursor.pos())
            self.show_tool_buttons(self.current_hovered_row, pos)

    def create_edit_btn(self, row_idx=None):
        edit_btn = QToolButton()
        edit_btn.setObjectName("editToolButton")
        edit_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        edit_btn.setText("✏️")
        edit_btn.setToolTip("Редактировать")
        edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_row(r))

        # Размещаем кнопки поверх таблицы
        edit_btn.setParent(self.table_db.viewport())
        edit_btn.hide()

        return edit_btn

    def create_delete_btn(self, row_idx=None):
        delete_btn = QToolButton()
        delete_btn.setObjectName("deleteToolButton")
        delete_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        delete_btn.setText("🗑️")
        delete_btn.setToolTip("Удалить")
        delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

        # Размещаем кнопки поверх таблицы
        delete_btn.setParent(self.table_db.viewport())
        delete_btn.hide()

        return delete_btn

    def create_refresh_button(self):
        # Кнопка загрузки данных
        refresh_button = QPushButton("Обновить данные")
        refresh_button.setStyleSheet(BUTTON_STYLE)
        refresh_button.clicked.connect(self.load_data_from_supabase)

        return refresh_button

    def create_table_db(self):
        table_db = QTableWidget()
        table_db.setStyleSheet(TABLE_STYLE)
        table_db.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_db.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Выделение всей строки
        table_db.setSelectionMode(QTableWidget.SelectionMode.SingleSelection) 
        table_db.setMouseTracking(True)  # Включаем отслеживание мыши
        table_db.viewport().installEventFilter(self)  # Устанавливаем фильтр событий

        table_db.itemSelectionChanged.connect(self.on_row_selected)

        print("таблица создана")

        return table_db
      
    def on_row_selected(self):
      """Обработчик выбора строки - показывает кнопки для выбранной строки"""
      selected = self.table_db.selectedItems()
      if selected:
          row = selected[0].row()
          self.current_hovered_row = row  # Сохраняем выбранную строку
          self.show_tool_buttons(row, None)

    def set_pos_action_buttons(self, row):
        edit_btn, delete_btn = self.action_buttons[row]

        # Получаем прямоугольник всей строки
        rect = self.table_db.visualRect(self.table_db.model().index(row, 0))

        # Получаем ширину видимой области таблицы
        table_width = self.table_db.viewport().width()

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

    def supabase_init(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

    def create_table_selector(self):
        # Создаем горизонтальный layout для выбора таблицы
        table_selection_layout = QHBoxLayout()
        table_selection_layout_widget = QWidget()
        table_selection_layout_widget.setLayout(table_selection_layout)
        table_selection_layout_widget.setStyleSheet(TABLE_SELECTION_LAYOUT_STYLE)

        self.label = QLabel("Выберите таблицу:")
        self.label.setStyleSheet(LABEL_STYLE)
        table_selection_layout.addWidget(self.label)

        # Создаем выпадающий список для выбора таблицы
        self.table_selector = QComboBox()
        self.table_selector.setStyleSheet(COMBO_BOX_STYLE)  # Применяем стиль
        self.table_selector.addItems(["works", "works_categories", "materials", "materials_categories"])
        self.table_selector.setCurrentText(self.current_table)
        self.table_selector.currentTextChanged.connect(self.on_table_changed)
        table_selection_layout.addWidget(self.table_selector)

        # Добавляем растягивающийся элемент
        table_selection_layout.addStretch()

        return table_selection_layout_widget
      
    def adjust_column_widths(self):
      header = self.table_db.horizontalHeader()
      reserved_space = 80
      total_width = self.table_db.viewport().width() - reserved_space
      
      if self.current_table in ['works_categories', 'materials_categories']:
          header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
          header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
          
          self.table_db.setColumnWidth(1, total_width - self.table_db.columnWidth(0))
          
      elif self.current_table in ['works', 'materials']:
          header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
          header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
          header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
          header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
          header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
          
          used_width = sum(self.table_db.columnWidth(i) for i in [0,1,3,4])
          remaining_width = max(100, total_width - used_width)
          self.table_db.setColumnWidth(2, remaining_width)
      header.setMinimumSectionSize(80)
      header.setStretchLastSection(False)