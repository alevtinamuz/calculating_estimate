import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QSpacerItem, QSizePolicy,
                            QTableWidgetItem, QTableWidget, QHeaderView,
                            QMessageBox, QToolButton, QStackedWidget,
                            QTabWidget, QComboBox, QLineEdit, QApplication, QDialog, QDialogButtonBox, QMenu, QSpinBox, QStyledItemDelegate,
                            QDoubleSpinBox, QFormLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QCursor
from supabase import create_client, Client
from dotenv import load_dotenv
import setters, getters

from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, TABLE_STYLE, TOOL_BUTTON_STYLE, TAB_STYLE, \
    TABLE_SELECTION_LAYOUT_STYLE, COMBO_BOX_STYLE, MENU_STYLE
from getters import get_materials_by_substr, get_works_by_substr, get_materials_by_category, get_works_by_category


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
        layout = QVBoxLayout(self.page_db)
        
        header_of_widget = self.create_header_of_table()
        layout.addWidget(header_of_widget)

        self.label = QLabel("База данных")
        self.label.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.label)

        # Таблица для данных
        self.table_db = self.create_table_db()
        layout.addWidget(self.table_db)

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

        self.table_estimate = self.create_table_estimate()
        layout.addWidget(self.table_estimate)

        self.page_estimate.setLayout(layout)

    def load_data_from_supabase(self):
        """Загружает данные из Supabase и отображает их в таблице"""
        try:
            self.label.setText("Загрузка данных...")
            self.label.setVisible(True) 
            self.table_db.setVisible(False)
            QApplication.processEvents()

            if self.current_table in ['works_categories', 'materials_categories']:
                data = getters.sort_by_id(self.supabase, self.current_table, 'id')  # Для категорий - простая загрузка
            else:
                data = getters.sort_by_id(self.supabase, self.current_table, 'category_id')  # Для остальных - с сортировкой

            if not data:
                self.label.setText("Нет данных для отображения")
                return

            category_names = {}
            if self.current_table in ['works', 'materials']:
                category_table = 'works_categories' if self.current_table == 'works' else 'materials_categories'
                categories = getters.get_all_table(self.supabase, category_table)
                category_names = {str(category['id']): category['name'] for category in categories}

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
                    # Заменяем category_id на название категории, но сохраняем оригинальный ID
                    if key == 'category_id' and self.current_table in ['works', 'materials']:
                        original_id = value
                        value = category_names.get(str(value), str(value))
                        item = QTableWidgetItem(str(value))
                        item.setData(Qt.ItemDataRole.UserRole, original_id)  # Сохраняем оригинальный ID
                    else:
                        item = QTableWidgetItem(str(value))

                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_db.setItem(row_idx, col_idx, item)

                edit_btn = self.create_edit_btn(row_idx)
                delete_btn = self.create_delete_btn(row_idx)
                self.action_buttons[row_idx] = (edit_btn, delete_btn)
                # # Создаем кнопки действий
                # edit_btn = self.create_edit_btn(row_idx)
                # delete_btn = self.create_delete_btn(row_idx)
                #
                # # Сохраняем ссылки на кнопки
                # self.action_buttons[row_idx] = (edit_btn, delete_btn)

            self.table_db.verticalHeader().setVisible(False)
            self.table_db.setShowGrid(False)
            self.table_db.setFrameShape(QTableWidget.Shape.NoFrame)

            # self.label.setText(f"Загружено {len(data)} записей")
            # self.label.setText("Данные успешно загружены")
            self.table_db.setStyleSheet(TABLE_STYLE)


            from PyQt6.QtCore import QTimer
            self.table_db.viewport().update()
            self.table_db.updateGeometry()

            # Настраиваем ширину колонок
            self.adjust_column_widths()

            # Показываем таблицу
            self.label.setVisible(False) 
            self.table_db.setVisible(True)
            # self.label.setText("Данные успешно загружены")

            # Еще раз обновляем геометрию после отображения
            QTimer.singleShot(200, lambda: [
                self.adjust_column_widths(),
                self.table_db.viewport().update()
            ])


        except Exception as e:
            self.label.setText(f"Ошибка загрузки: {str(e)}")
            print('Error:', e)

    def finalize_table_setup(self):
      """Завершающая настройка таблицы после загрузки данных"""
      try:
          # Настраиваем размеры колонок
          self.adjust_column_widths()

          # Теперь показываем таблицу
          self.table_db.setVisible(True)

          # Принудительное обновление геометрии
          self.table_db.viewport().updateGeometry()
          self.table_db.updateGeometry()

          print(f"Таблица отображена, ширина: {self.table_db.width()}")
          print("Данные обновлены")

      except Exception as e:
          print(f"Ошибка при настройке таблицы: {str(e)}")

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

    def add_row(self, row):
      """Обработка редактирования строки с формой из нескольких полей"""
      # Определяем заголовок и текущие значения
      if self.current_table in ['works', 'materials']:
          title = "Добавление записи"
          current_name = "Введите название записи"
          current_price = 99.99
          current_unit = "м2"
          current_category = "Выберите категорию"
      elif self.current_table in ['works_categories', 'materials_categories']:
          title = "Добавление категории"
          current_name = "Введите название категории"
          
      # Создаем диалоговое окно
      dialog = QDialog(self)
      dialog.setWindowTitle(title)
      dialog.setMinimumWidth(300)

      # Основной layout
      main_layout = QVBoxLayout()

      # Создаем форму с полями
      form_layout = QFormLayout()

      # Поле "Название"
      name_input = QLineEdit()
      name_input.setText(current_name)
      form_layout.addRow("Название:", name_input)

      # Поле "Цена" (только для works/materials)
      if self.current_table in ['works', 'materials']:
          price_input = QDoubleSpinBox()
          price_input.setPrefix("₽ ")       # Добавляем символ рубля
          price_input.setMaximum(9999999999)
          price_input.setValue(current_price)
          form_layout.addRow("Цена:", price_input)
          unit_input = QLineEdit()
          unit_input.setText(current_unit)
          form_layout.addRow("Ед. изм.:", unit_input)
          if self.current_table == 'works':
            category_combo_work = QComboBox()
            categories_work = getters.get_all_table(self.supabase, 'works_categories')
            for category in categories_work:
              category_combo_work.addItem(category['name'], userData=category['id'])
            category_combo_work.setCurrentText(current_category)
            form_layout.addRow("Категория работ:", category_combo_work)
          if self.current_table == 'materials':
            category_combo_material = QComboBox()
            categories_material = getters.get_all_table(self.supabase, 'materials_categories')
            for category in categories_material:
              category_combo_material.addItem(category['name'], userData=category['id'])
            category_combo_material.setCurrentText(current_category)
            form_layout.addRow("Категория работ:", category_combo_material)


      main_layout.addLayout(form_layout)

      # Кнопки (Save/Cancel)
      button_box = QDialogButtonBox(
          QDialogButtonBox.StandardButton.Save |
          QDialogButtonBox.StandardButton.Cancel
      )
      button_box.accepted.connect(dialog.accept)
      button_box.rejected.connect(dialog.reject)
      main_layout.addWidget(button_box)

      dialog.setLayout(main_layout)

      # Обработка результата
      if dialog.exec() == QDialog.DialogCode.Accepted:
          new_name = name_input.text()

          # Проверка на пустое название
          if not new_name.strip():
              QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
              return

          try:
              # Добавляем цену для работ/материалов
              if self.current_table in ['works', 'materials']:
                  new_price = price_input.value()
                  new_unit = unit_input.text()

              # Обновляем данные в Supabase
              if self.current_table == 'works':
                  new_category_work = category_combo_work.currentData()
                  setters.add_work(self.supabase, new_category_work, new_name, new_price, new_unit)
              elif self.current_table == 'materials':
                  new_category_material = category_combo_material.currentData()
                  setters.add_material(self.supabase, new_category_material, new_name, new_price, new_unit)
              elif self.current_table == 'works_categories':
                  setters.add_work_category(self.supabase, new_name)
              elif self.current_table == 'materials_categories':
                  setters.add_material_category(self.supabase, new_name)

              # Обновляем таблицу
              self.load_data_from_supabase()
              QMessageBox.information(self, "Успех", "Данные успешно обновлены!")

          except Exception as e:
              QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")

    def edit_row(self, row):
      """Обработка редактирования строки с формой из нескольких полей"""
      record_id = self.table_db.item(row, 0).text()

      # Определяем заголовок и текущие значения
      if self.current_table in ['works', 'materials']:
          title = "Редактирование записи"
          current_name = self.table_db.item(row, 2).text()  # Название
          current_price = float(self.table_db.item(row, 3).text())  # Цена
          current_unit = self.table_db.item(row, 4).text()
          # Получаем оригинальный ID категории из UserRole
          current_category = self.table_db.item(row, 1).data(Qt.ItemDataRole.UserRole)
      elif self.current_table in ['works_categories', 'materials_categories']:
          title = "Редактирование категории"
          current_name = self.table_db.item(row, 1).text()  # Название категории

      # Создаем диалоговое окно
      dialog = QDialog(self)
      dialog.setWindowTitle(title)
      dialog.setMinimumWidth(300)

      # Основной layout
      main_layout = QVBoxLayout()

      # Создаем форму с полями
      form_layout = QFormLayout()

      # Поле "Название"
      name_input = QLineEdit()
      name_input.setText(current_name)
      form_layout.addRow("Название:", name_input)

      # Поле "Цена" (только для works/materials)
      if self.current_table in ['works', 'materials']:
          price_input = QDoubleSpinBox()
          price_input.setPrefix("₽ ")       # Добавляем символ рубля
          price_input.setMaximum(9999999999)
          price_input.setValue(current_price)
          form_layout.addRow("Цена:", price_input)
          unit_input = QLineEdit()
          unit_input.setText(current_unit)
          form_layout.addRow("Ед. изм.:", unit_input)
          if self.current_table == 'works':
            category_combo_work = QComboBox()
            categories_work = getters.get_all_table(self.supabase, 'works_categories')
            for category in categories_work:
              category_combo_work.addItem(category['name'], userData=category['id'])
            current_category_name_work = getters.get_category_by_id(self.supabase, 'works_categories', current_category)
            category_combo_work.setCurrentText(current_category_name_work[0]['name'])
            form_layout.addRow("Категория работ:", category_combo_work)
          if self.current_table == 'materials':
            category_combo_material = QComboBox()
            categories_material = getters.get_all_table(self.supabase, 'materials_categories')
            for category in categories_material:
              category_combo_material.addItem(category['name'], userData=category['id'])
            current_category_name_material = getters.get_category_by_id(self.supabase, 'materials_categories', current_category)
            category_combo_material.setCurrentText(current_category_name_material[0]['name'])
            form_layout.addRow("Категория работ:", category_combo_material)


      main_layout.addLayout(form_layout)

      # Кнопки (Save/Cancel)
      button_box = QDialogButtonBox(
          QDialogButtonBox.StandardButton.Save |
          QDialogButtonBox.StandardButton.Cancel
      )
      button_box.accepted.connect(dialog.accept)
      button_box.rejected.connect(dialog.reject)
      main_layout.addWidget(button_box)

      dialog.setLayout(main_layout)

      # Обработка результата
      if dialog.exec() == QDialog.DialogCode.Accepted:
          new_name = name_input.text()

          # Проверка на пустое название
          if not new_name.strip():
              QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
              return

          try:
              # Добавляем цену для работ/материалов
              if self.current_table in ['works', 'materials']:
                  new_price = price_input.value()
                  new_unit = unit_input.text()

              # Обновляем данные в Supabase
              if self.current_table == 'works':
                  new_category_work = category_combo_work.currentData()
                  setters.update_name_of_work(self.supabase, record_id, new_name)
                  setters.update_price_of_work(self.supabase, record_id, new_price)
                  setters.update_unit_of_works(self.supabase, record_id, new_unit)
                  setters.update_category_id_of_work(self.supabase, record_id, new_category_work)
              elif self.current_table == 'materials':
                  new_category_material = category_combo_material.currentData()
                  setters.update_name_of_materials(self.supabase, record_id, new_name)
                  setters.update_price_of_material(self.supabase, record_id, new_price)
                  setters.update_unit_of_materials(self.supabase, record_id, new_unit)
                  setters.update_category_id_of_material(self.supabase, record_id, new_category_material)
              elif self.current_table == 'works_categories':
                  setters.update_name_work_category(self.supabase, record_id, new_name)
              elif self.current_table == 'materials_categories':
                  setters.update_name_material_category(self.supabase, record_id, new_name)

              # Обновляем таблицу
              self.load_data_from_supabase()
              QMessageBox.information(self, "Успех", "Данные успешно обновлены!")

          except Exception as e:
              QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")

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
        refresh_button.setFixedSize(150, 30)
        refresh_button.clicked.connect(self.load_data_from_supabase)

        return refresh_button
      
    def create_add_button(self, row_idx=None):
        add_button = QPushButton("➕")
        add_button.setStyleSheet(BUTTON_STYLE)
        add_button.setFixedSize(150, 30)
        add_button.setToolTip("Добавить данные")
        add_button.clicked.connect(lambda _, r=row_idx: self.add_row(r))
        
        return add_button

    def create_table_db(self):
        table_db = QTableWidget()
        table_db.setStyleSheet(TABLE_STYLE)
        table_db.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_db.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Выделение всей строки
        table_db.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table_db.setMouseTracking(True)  # Включаем отслеживание мыши
        table_db.viewport().installEventFilter(self)  # Устанавливаем фильтр событий

        table_db.itemSelectionChanged.connect(self.on_row_selected)
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
        # Создаем выпадающий список для выбора таблицы
        self.table_selector = QComboBox()
        self.table_selector.setStyleSheet(COMBO_BOX_STYLE)  # Применяем стиль
        self.table_selector.addItems(["works", "works_categories", "materials", "materials_categories"])
        self.table_selector.setCurrentText(self.current_table)
        self.table_selector.currentTextChanged.connect(self.on_table_changed)
        
        return self.table_selector
        
        
    def create_header_of_table(self):
        """Создает фиксированный заголовок таблицы"""
        header_widget = QWidget()
        header_widget.setStyleSheet(TABLE_SELECTION_LAYOUT_STYLE)
        
        # Основной layout с фиксированными параметрами
        main_layout = QHBoxLayout(header_widget)
        main_layout.setContentsMargins(10, 5, 10, 5)  # Отступы: слева, сверху, справа, снизу
        main_layout.setSpacing(10)
        
        # Метка выбора таблицы
        label = QLabel("Выберите таблицу:")
        label.setStyleSheet(LABEL_STYLE)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(label)
        
        # Комбобокс выбора таблицы
        table_selector = self.create_table_selector()
        table_selector.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(table_selector)
        
        # Растягивающийся элемент между комбобоксом и кнопкой
        main_layout.addStretch()
        
        add_button = self.create_add_button()
        add_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(add_button)
        
        # Кнопка обновления с фиксированным размером
        refresh_button = self.create_refresh_button()
        refresh_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(refresh_button)
        
        # Фиксируем размер всего заголовка
        header_widget.setFixedHeight(60)  # Фиксированная высота заголовка
        
        return header_widget

    def adjust_column_widths(self):
        if not self.table_db.isVisible():
          return
        header = self.table_db.horizontalHeader()
        reserved_space = 80
        total_width = self.table_db.viewport().width() - reserved_space

        procents_section = {
          0: 0.1,
          1: 0.2,
          2: 0.5,
          3: 0.1,
          4: 0.1
        }

        procents_category = {
          0: 0.1,
          1: 0.9
        }

        if self.current_table in ['works_categories', 'materials_categories']:
            for col, procent in procents_category.items():
              header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
              self.table_db.setColumnWidth(col, int(total_width * procent))

        elif self.current_table in ['works', 'materials']:
            for col, procent in procents_section.items():
              header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
              self.table_db.setColumnWidth(col, int(total_width * procent))
        header.setStretchLastSection(False)

    def create_table_estimate(self):
        table_estimate = QTableWidget()
        table_estimate.setStyleSheet(TABLE_STYLE)
        table_estimate.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        table_estimate.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_estimate.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table_estimate.setMouseTracking(True)
        table_estimate.viewport().installEventFilter(self)
        table_estimate.itemSelectionChanged.connect(self.on_row_selected)

        headers = [
            "№ п/п", "Наименование работ и затрат", "Ед. изм.", "К-во",
            "Фактический ФОТ на ед.", "ФОТ всего", "Наименование материалов",
            "Ед. изм.", "К-во", "Цена", "Сумма", "Всего"
        ]
        table_estimate.setColumnCount(len(headers))
        table_estimate.setHorizontalHeaderLabels(headers)
        table_estimate.setRowCount(1)

        # Устанавливаем делегат для ячеек
        delegate = ComboBoxDelegate(table_estimate, self.supabase)
        table_estimate.setItemDelegate(delegate)

        table_estimate.setStyleSheet(TABLE_STYLE)

        return table_estimate


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent, supabase):
        super().__init__(parent)
        self.supabase = supabase
        self.current_editor = None
        self.current_row = -1
        self.current_col = -1
        self.editor_pos_offset = QPoint(-70, 0)

    def createEditor(self, parent, option, index):
        if index.column() in [1, 6]:
            try:
                editor = QWidget(parent, Qt.WindowType.Popup)
                editor.setWindowFlag(Qt.WindowType.FramelessWindowHint)
                editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                editor.setStyleSheet(COMBO_BOX_STYLE)

                layout = QHBoxLayout(editor)
                layout.setContentsMargins(2, 2, 2, 2)

                # Ваши комбобоксы
                self.main_combo = QComboBox(editor)
                self.sub_combo = QComboBox(editor)
                layout.addWidget(self.main_combo)
                layout.addWidget(self.sub_combo)

                # Заполнение данными
                self.load_initial_data(index.column())

                # Позиционирование при создании
                self.adjust_editor_position(editor, parent, index)

                self.current_editor = editor
                return editor

            except Exception as e:
                print(f"Editor error: {e}")
                return super().createEditor(parent, option, index)

        elif index.column() in [3, 8]:  # Ячейки с количеством
            editor = QSpinBox(parent)
            editor.setMinimum(0)
            editor.setMaximum(999999)

            return editor

    def adjust_editor_position(self, editor, parent, index):
        """Безопасное позиционирование редактора"""
        try:
            table = parent.parent()  # Получаем таблицу из viewport
            if not table:
                return

            rect = table.visualRect(index)
            global_pos = table.viewport().mapToGlobal(rect.bottomLeft())

            # Применяем смещение
            editor.move(global_pos + self.editor_pos_offset)
            editor.resize(max(rect.width(), 300), editor.sizeHint().height())

        except Exception as e:
            print(f"Positioning error: {e}")

    def updateEditorGeometry(self, editor, option, index):
        """Упрощенная версия без рекурсии"""
        if index.column() in [1, 6]:
            try:
                # Используем абсолютные координаты
                rect = option.rect
                global_pos = editor.parent().mapToGlobal(rect.bottomLeft())
                editor.move(global_pos + self.editor_pos_offset)
                editor.resize(max(rect.width(), 300), editor.sizeHint().height())
            except:
                super().updateEditorGeometry(editor, option, index)
        else:
            super().updateEditorGeometry(editor, option, index)

    def load_initial_data(self, column):
        """Загрузка начальных данных в комбобоксы"""
        entity_type = "works" if column == 1 else "materials"
        try:
            categories = self.supabase.table(f"{entity_type}_categories").select('*').execute().data
            self.main_combo.clear()
            for cat in categories:
                self.main_combo.addItem(cat['name'], cat['id'])

            # Загружаем подчиненные элементы
            self.update_sub_combo()

        except Exception as e:
            print(f"Data loading error: {e}")

    def update_sub_combo(self):
        """Обновление подчиненного комбобокса"""
        if hasattr(self, 'main_combo') and self.main_combo.count() > 0:
            cat_id = self.main_combo.currentData()
            entity_type = "works" if self.current_col == 1 else "materials"

            try:
                items = self.supabase.table(entity_type) \
                    .select('*') \
                    .eq('category_id', cat_id) \
                    .execute().data

                self.sub_combo.clear()
                for item in items:
                    self.sub_combo.addItem(item['name'], item['id'])

            except Exception as e:
                print(f"Sub-combo update error: {e}")

    def on_work_selected(self, index):
        """Обрабатывает выбор конкретной работы/материала"""
        if index >= 0:
            selected_text = self.sub_combo.currentText()
            self.commitData.emit(self.current_editor)  # Важно для сохранения данных

            # Устанавливаем значение в таблицу
            table = self.parent()
            item = table.item(self.current_row, self.current_col)
            if item is None:
                item = QTableWidgetItem(selected_text)
                table.setItem(self.current_row, self.current_col, item)
            else:
                item.setText(selected_text)

            print(f"Выбрано: {selected_text}")

    def setModelData(self, editor, model, index):
        """Сохраняет выбранное значение в модель"""
        if index.column() in [1, 6]:
            selected_text = self.sub_combo.currentText()
            model.setData(index, selected_text)
        elif index.column() in [3, 8]:  # Для ячеек с количеством
            # Получаем значение из QSpinBox и сохраняем в модель
            value = editor.value()
            model.setData(index, value)

    def destroyEditor(self, editor, index):
        """Очищаем ссылки при уничтожении редактора"""
        self.current_editor = None
        self.main_combo = None
        self.sub_combo = None
        super().destroyEditor(editor, index)
