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
from design.styles import MAIN_WINDOW_STYLE, LABEL_STYLE, BUTTON_STYLE, TABLE_STYLE, TOOL_BUTTON_STYLE, TAB_STYLE, \
    TABLE_SELECTION_LAYOUT_STYLE, COMBO_BOX_STYLE


class MainWindow(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        self.setWindowTitle("Calculating estimate")
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.works = []

        # Инициализация Supabase
        self.supabase = supabase

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
        self.page_db = self.create_page_db()
        self.page_estimate = self.create_page_estimate()
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

        page_db = QWidget()
        layout = QVBoxLayout(page_db)

        header_of_widget = self.create_header_of_table()
        layout.addWidget(header_of_widget)

        self.label = QLabel("База данных")
        self.label.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.label)

        # Таблица для данных
        self.table_db = self.create_table_db()
        layout.addWidget(self.table_db)

        self.load_data_from_supabase()

        page_db.setLayout(layout)

        return page_db

    def on_table_changed(self, table_name):
        """Обработчик изменения выбранной таблицы"""
        self.current_table = table_name
        self.load_data_from_supabase()

    def create_page_estimate(self):
        """Создает вторую страницу (смета)"""
        page_estimate = QWidget()
        layout = QVBoxLayout()

        self.label_estimate = QLabel("Страница сметы")
        self.label_estimate.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.label_estimate)

        self.table_estimate = self.create_table_estimate()
        layout.addWidget(self.table_estimate)

        page_estimate.setLayout(layout)

        return page_estimate

    def load_data_from_supabase(self):
        """Загружает данные из Supabase и отображает их в таблице"""
        try:
            gif_path = os.path.join(os.path.dirname(__file__), "spinner.gif")
            loading_movie = QMovie(gif_path)
            self.label.setMovie(loading_movie)
            loading_movie.start()
            QApplication.processEvents()
            self.label.setVisible(True)

            self.table_db.setVisible(False)
            QApplication.processEvents()

            if self.current_table in ['works_categories', 'materials_categories']:
                data = getters.sort_by_id(self.supabase, self.current_table, 'id')  # Для категорий - простая загрузка
            else:
                data = getters.sort_by_id(self.supabase, self.current_table,
                                          'category_id')  # Для остальных - с сортировкой

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

            self.table_db.verticalHeader().setVisible(False)
            self.table_db.setShowGrid(False)
            self.table_db.setFrameShape(QTableWidget.Shape.NoFrame)

            self.table_db.setStyleSheet(TABLE_STYLE)

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
            price_input.setPrefix("₽ ")  # Добавляем символ рубля
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
        global new_price, new_unit, category_combo_material, category_combo_work, price_input, unit_input, current_category, current_unit, current_price, current_name, title
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
            price_input.setPrefix("₽ ")  # Добавляем символ рубля
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
                current_category_name_work = getters.get_entity_by_id(self.supabase, 'works_categories',
                                                                      current_category)
                category_combo_work.setCurrentText(current_category_name_work[0]['name'])
                form_layout.addRow("Категория работ:", category_combo_work)
            if self.current_table == 'materials':
                category_combo_material = QComboBox()
                categories_material = getters.get_all_table(self.supabase, 'materials_categories')
                for category in categories_material:
                    category_combo_material.addItem(category['name'], userData=category['id'])
                current_category_name_material = getters.get_entity_by_id(self.supabase, 'materials_categories',
                                                                          current_category)
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
        global reply
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

    def create_table_selector(self):
        # Создаем выпадающий список для выбора таблицы
        table_selector = QComboBox()
        table_selector.setStyleSheet(COMBO_BOX_STYLE)  # Применяем стиль
        table_selector.addItems(["works", "works_categories", "materials", "materials_categories"])
        table_selector.setCurrentText(self.current_table)
        table_selector.currentTextChanged.connect(self.on_table_changed)

        return table_selector

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

        percents_section = {
            0: 0.1,
            1: 0.2,
            2: 0.5,
            3: 0.1,
            4: 0.1
        }

        percents_category = {
            0: 0.1,
            1: 0.9
        }

        if self.current_table in ['works_categories', 'materials_categories']:
            for col, percent in percents_category.items():
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
                self.table_db.setColumnWidth(col, int(total_width * percent))

        elif self.current_table in ['works', 'materials']:
            for col, percent in percents_section.items():
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
                self.table_db.setColumnWidth(col, int(total_width * percent))
        header.setStretchLastSection(False)

    def create_table_estimate(self):
        try:
            estimate_container = QWidget()
            layout = QVBoxLayout(estimate_container)

            # Создаем таблицу как атрибут класса
            self.table_estimate = QTableWidget()
            self.table_estimate.setObjectName("estimateTable")

            # Настройки таблицы
            self.table_estimate.setStyleSheet(TABLE_STYLE)
            self.table_estimate.setShowGrid(False)
            self.table_estimate.setEditTriggers(
                QTableWidget.EditTrigger.DoubleClicked |
                QTableWidget.EditTrigger.EditKeyPressed
            )
            self.table_estimate.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table_estimate.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

            # Заголовки
            headers = [
                "№ п/п", "Наименование работ и затрат", "Ед. изм.", "К-во",
                "Фактический ФОТ на ед., руб", "ФОТ всего, руб", "Наименование материалов",
                "Ед. изм.", "К-во", "Цена, руб", "Сумма, руб", "Всего, руб"
            ]
            self.table_estimate.setColumnCount(len(headers))
            self.table_estimate.setHorizontalHeaderLabels(headers)
            self.table_estimate.setRowCount(0)  # Начальная строка

            # Делегат
            delegate = ComboBoxDelegate(self.table_estimate, self.supabase, self)
            self.table_estimate.setItemDelegate(delegate)

            layout.addWidget(self.table_estimate)

            button_layout = QHBoxLayout()

            add_work_button = QPushButton("Добавить работу")
            add_work_button.clicked.connect(lambda: self.add_row_to_estimate(is_work=True))
            add_work_button.setStyleSheet(BUTTON_STYLE)

            add_material_button = QPushButton("Добавить материал")
            add_material_button.clicked.connect(lambda: self.add_row_to_estimate(is_work=False))
            add_material_button.setStyleSheet(BUTTON_STYLE)

            button_layout.addWidget(add_work_button)
            button_layout.addWidget(add_material_button)

            layout.addLayout(button_layout)

            estimate_container.setLayout(layout)

            print("Таблица успешно создана")
            return estimate_container

        except Exception as e:
            print(f"Ошибка создания таблицы: {e}")
            raise

    def add_row_to_estimate(self, is_work=True):
        try:
            table = self.findChild(QTableWidget, "estimateTable")
            row_count = table.rowCount()
            table.insertRow(row_count)

            if is_work:
                # Добавляем новую работу
                self.works.append(WorkItem())
                # Устанавливаем номер строки
                last_num = 0
                for row in range(table.rowCount() - 1):
                    item = table.item(row, 0)
                    if item and item.text().isdigit():
                        last_num = max(last_num, int(item.text()))

                # Устанавливаем новый номер (последний + 1)
                item = QTableWidgetItem(str(last_num + 1))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_count, 0, item)

                # Устанавливаем делегаты для ячеек работы
                for col in [1, 2, 3, 4, 5]:
                    table.setItem(row_count, col, QTableWidgetItem(""))

                for col in range(table.columnCount()):
                    if not table.item(row_count, col):  # Если ячейка еще не создана
                        item = QTableWidgetItem("")
                        table.setItem(row_count, col, item)

                    # Устанавливаем атрибут для работы
                    item = table.item(row_count, col)
                    item.setData(Qt.ItemDataRole.UserRole, "is_work")
            else:
                # Добавляем материал к последней работе
                if not self.works:
                    self.add_row_to_estimate(is_work=True)
                    return

                self.works[-1].materials.append(MaterialItem())

                # Находим первую строку работы (она могла быть выше)
                work_row = self.find_work_row(row_count)

                # Объединяем ячейки работы вертикально с материалом
                for col in range(6):  # Колонки 0-5
                    table.setSpan(work_row, col, row_count - work_row + 1, 1)  # Объединяем по вертикали

                # Заполняем ячейки материала
                for col in range(6, table.columnCount()):
                    item = QTableWidgetItem("")
                    item.setData(Qt.ItemDataRole.UserRole, "is_material")
                    table.setItem(row_count, col, item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить строку: {str(e)}")

    def find_work_row(self, material_row):
        """Находит строку работы для указанной строки материала"""
        table = self.findChild(QTableWidget, "estimateTable")
        row = material_row - 1
        while row >= 0:
            if table.item(row, 0) and table.item(row, 0).data(Qt.ItemDataRole.UserRole) == "is_work":
                return row
            row -= 1
        return material_row
