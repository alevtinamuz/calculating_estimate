import os
import json
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHeaderView, QSizePolicy, QHBoxLayout, QComboBox, \
    QTableWidget, QPushButton, QToolButton, QMessageBox, QDialog, QDialogButtonBox, QLineEdit, QDoubleSpinBox, \
    QFormLayout, QTableWidgetItem, QApplication, QFileDialog, QCheckBox, QProgressDialog, QButtonGroup

import getters
import setters
from design.styles import LABEL_STYLE, TOOL_PANEL_STYLE, DROPDOWN_STYLE, DATA_TABLE_STYLE, PRIMARY_BUTTON_STYLE, \
    ACTION_BUTTONS_STYLE, SEARCH_STYLE

BACKUP_VERSION = "1.0"

class PageDB(QMainWindow):
    def __init__(self, supabase):
        super().__init__()

        self.supabase = supabase
        self.action_buttons = {}
        self.current_table = 'works'

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

    def load_data_from_supabase(self):
        """Загружает данные из Supabase и отображает их в таблице"""
        try:
            gif_path = os.path.join(os.path.dirname(__file__), "spinner.gif")
            loading_movie = QMovie(gif_path)
            self.label.setMovie(loading_movie)
            loading_movie.start()
            self.label.setVisible(True)

            self.table_db.setVisible(False)
            QApplication.processEvents()

            if self.current_table in ['works_categories', 'materials_categories']:
                data = getters.sort_by_id(self.supabase, self.current_table, 'id') 
                column_order = ['id', 'name']
                header_names = {
                    'id': 'ID',
                    'name': 'Название категории'
                }
            else:
                data = getters.sort_by_id(self.supabase, self.current_table, 'category_id') 
                column_order = ['id', 'category_id', 'name', 'price', 'unit']
                header_names = {
                    'id': 'ID',
                    'category_id': 'Категория',
                    'name': 'Название',
                    'price': 'Цена',
                    'unit': 'Ед. изм.'
                }

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
            self.table_db.setColumnCount(len(column_order))

            # Устанавливаем заголовки
            headers = [header_names[key] for key in column_order]
            self.table_db.setHorizontalHeaderLabels(headers)

            # Заполняем таблицу данными
            for row_idx, row_data in enumerate(data):
                for col_idx, column_name in enumerate(column_order):
                    value = row_data[column_name]
                    
                    # Заменяем category_id на название категории, но сохраняем оригинальный ID
                    if column_name == 'category_id' and self.current_table in ['works', 'materials']:
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

            self.table_db.setStyleSheet(DATA_TABLE_STYLE)

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

    def hide_all_tool_buttons(self):
        """Скрывает все кнопки"""
        for buttons in self.action_buttons.values():
            for btn in buttons:
                btn.hide()

    def add_row(self,row):
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
                form_layout.addRow("Категория работы:", category_combo_work)
            if self.current_table == 'materials':
                category_combo_material = QComboBox()
                categories_material = getters.get_all_table(self.supabase, 'materials_categories')
                for category in categories_material:
                    category_combo_material.addItem(category['name'], userData=category['id'])
                category_combo_material.setCurrentText(current_category)
                form_layout.addRow("Категория материала:", category_combo_material)

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
                current_category_name_work = getters.get_entity_by_id(self.supabase, 'works_categories', current_category)
                category_combo_work.setCurrentText(current_category_name_work[0]['name'])
                form_layout.addRow("Категория работ:", category_combo_work)
            if self.current_table == 'materials':
                category_combo_material = QComboBox()
                categories_material = getters.get_all_table(self.supabase, 'materials_categories')
                for category in categories_material:
                    category_combo_material.addItem(category['name'], userData=category['id'])
                current_category_name_material = getters.get_entity_by_id(self.supabase, 'materials_categories', current_category)
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
                
    def backup_database_to_file(self):
        """Выгрузка данных с группировкой по связанным таблицам"""
        try:
            # Создаем диалог выбора групп таблиц
            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор данных для выгрузки")
            dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Выберите данные для выгрузки:"))
            
            # Группы таблиц (только полные связанные группы)
            table_groups = {
                'works': QCheckBox("Работы с категориями работ"),
                'materials': QCheckBox("Материалы с категориями материалов")
            }
            
            # Включаем все группы по умолчанию
            for checkbox in table_groups.values():
                checkbox.setChecked(True)
                layout.addWidget(checkbox)
            
            # Кнопки
            btn_ok = QPushButton("Выгрузить")
            btn_cancel = QPushButton("Отмена")
            
            btn_ok.clicked.connect(dialog.accept)
            btn_cancel.clicked.connect(dialog.reject)
            
            layout.addWidget(btn_ok)
            layout.addWidget(btn_cancel)
            dialog.setLayout(layout)
            
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
                
            selected_groups = [name for name, checkbox in table_groups.items() if checkbox.isChecked()]
            if not selected_groups:
                QMessageBox.warning(self, "Ошибка", "Не выбрано ни одной группы данных!")
                return
            
            # Подготовка данных
            data = {
                'metadata': {
                    'backup_date': datetime.now().isoformat(),
                    'version': BACKUP_VERSION,
                    'tables': selected_groups
                }
            }
            
            # Прогресс-бар
            progress = QProgressDialog("Подготовка к выгрузке...", "Отмена", 0, len(selected_groups)*2, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Прогресс выгрузки")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            QApplication.processEvents()
            
            try:
                for group in selected_groups:
                    if group == 'works':
                        # Выгружаем категории работ
                        progress.setLabelText("Выгрузка категорий работ...")
                        data['works_categories'] = getters.get_all_table(self.supabase, 'works_categories')
                        progress.setValue(progress.value() + 1)
                        
                        # Выгружаем работы
                        progress.setLabelText("Выгрузка работ...")
                        data['works'] = getters.get_all_table(self.supabase, 'works')
                        progress.setValue(progress.value() + 1)
                        
                    elif group == 'materials':
                        # Выгружаем категории материалов
                        progress.setLabelText("Выгрузка категорий материалов...")
                        data['materials_categories'] = getters.get_all_table(self.supabase, 'materials_categories')
                        progress.setValue(progress.value() + 1)
                        
                        # Выгружаем материалы
                        progress.setLabelText("Выгрузка материалов...")
                        data['materials'] = getters.get_all_table(self.supabase, 'materials')
                        progress.setValue(progress.value() + 1)
                    
                    if progress.wasCanceled():
                        return
                
                # Сохранение в файл
                progress.setLabelText("Сохранение в файл...")
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "Сохранить резервную копию БД",
                    f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    "JSON Files (*.json)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        json.dump(data, file, ensure_ascii=False, indent=2)
                    
                    progress.setValue(len(selected_groups)*2)
                    QMessageBox.information(self, "Успех", f"Резервная копия сохранена в:\n{file_path}")
                    
            except Exception as e:
                progress.cancel()
                QMessageBox.critical(self, "Ошибка", f"Ошибка при выгрузке данных:\n{str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить резервную копию:\n{str(e)}")

    def restore_database_from_file(self):
        """Восстановление данных с учетом связей между таблицами"""
        try:
            # Выбор файла
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Выберите файл резервной копии",
                "",
                "JSON Files (*.json)"
            )
            
            if not file_path:
                return
                
            # Чтение и проверка файла
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            if 'metadata' not in data or 'tables' not in data['metadata']:
                QMessageBox.critical(self, "Ошибка", "Неверный формат файла резервной копии!")
                return
                
            # Доступные группы для восстановления (только полные связанные группы)
            available_groups = []
            if 'works' in data['metadata']['tables'] and 'works_categories' in data and 'works' in data:
                available_groups.append(('works', "Работы с категориями"))
            if 'materials' in data['metadata']['tables'] and 'materials_categories' in data and 'materials' in data:
                available_groups.append(('materials', "Материалы с категориями"))
                
            if not available_groups:
                QMessageBox.critical(self, "Ошибка", "В файле нет полных групп данных для восстановления!")
                return
                
            # Диалог выбора групп
            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор данных для восстановления")
            dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Выберите группы данных для восстановления:"))
            
            checkboxes = {}
            for group_id, group_name in available_groups:
                checkbox = QCheckBox(group_name)
                checkbox.setChecked(True)
                checkboxes[group_id] = checkbox
                layout.addWidget(checkbox)
            
            btn_ok = QPushButton("Восстановить")
            btn_cancel = QPushButton("Отмена")
            
            btn_ok.clicked.connect(dialog.accept)
            btn_cancel.clicked.connect(dialog.reject)
            
            layout.addWidget(btn_ok)
            layout.addWidget(btn_cancel)
            dialog.setLayout(layout)
            
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
                
            selected_groups = [group_id for group_id, checkbox in checkboxes.items() if checkbox.isChecked()]
            if not selected_groups:
                QMessageBox.warning(self, "Ошибка", "Не выбрано ни одной группы данных!")
                return
                
            # Подтверждение
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы уверены, что хотите восстановить выбранные данные?\nТекущие данные в этих таблицах будут перезаписаны!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
                
            # Прогресс-бар
            progress = QProgressDialog("Восстановление данных...", "Отмена", 0, len(selected_groups)*2, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Прогресс восстановления")
            progress.setMinimumDuration(0)
            
            try:
                for group in selected_groups:
                    if group == 'works':
                        # Восстанавливаем категории работ с оригинальными ID
                        progress.setLabelText("Восстановление категорий работ...")
                        setters.clear_table(self.supabase, 'works_categories')
                        
                        categories_data = [{'id': c['id'], 'name': c['name']} for c in data['works_categories']]
                        
                        setters.batch_insert_work_categories_with_ids(self.supabase, categories_data)
                            
                        progress.setValue(progress.value() + 1)

                        # Восстанавливаем работы
                        progress.setLabelText("Восстановление работ...")
                        setters.clear_table(self.supabase, 'works')
                        setters.batch_insert_works_fast(self.supabase, data['works'])
                        progress.setValue(progress.value() + 1)
                        
                    elif group == 'materials':
                        # Восстанавливаем категории материалов с оригинальными ID
                        progress.setLabelText("Восстановление категорий материалов...")
                        setters.clear_table(self.supabase, 'materials_categories')
                        
                        categories_data = [{'id': c['id'], 'name': c['name']} for c in data['materials_categories']]
                        
                        setters.batch_insert_material_categories_with_ids(self.supabase, categories_data)
                            
                        progress.setValue(progress.value() + 1)
                        
                        # Восстанавливаем материалы
                        progress.setLabelText("Восстановление материалов...")
                        setters.clear_table(self.supabase, 'materials')
                        setters.batch_insert_materials_fast(self.supabase, data['materials'])
                        progress.setValue(progress.value() + 1)
                    
                    if progress.wasCanceled():
                        return
                
                progress.setValue(len(selected_groups)*2)
                QMessageBox.information(self, "Успех", "Данные успешно восстановлены!")
                self.load_data_from_supabase()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка восстановления:\n{str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось восстановить данные:\n{str(e)}")
        
    def create_edit_btn(self, row_idx=None):
        edit_btn = QToolButton()
        edit_btn.setObjectName("editToolButton")
        edit_btn.setStyleSheet(ACTION_BUTTONS_STYLE)
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
        delete_btn.setStyleSheet(ACTION_BUTTONS_STYLE)
        delete_btn.setText("🗑️")
        delete_btn.setToolTip("Удалить")
        delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

        # Размещаем кнопки поверх таблицы
        delete_btn.setParent(self.table_db.viewport())
        delete_btn.hide()

        return delete_btn

    def create_refresh_button(self):
        # Кнопка загрузки данных
        refresh_button = QPushButton("Обновить")
        refresh_button.setStyleSheet(PRIMARY_BUTTON_STYLE)
        refresh_button.clicked.connect(self.load_data_from_supabase)

        return refresh_button

    def create_add_button(self, row_idx=None):
        add_button = QPushButton("Добавить")
        add_button.setStyleSheet(PRIMARY_BUTTON_STYLE)
        add_button.clicked.connect(lambda _, r=row_idx: self.add_row(r))

        return add_button
    
    def create_save_file_button(self):
        save_file_button = QPushButton("Выгрузить")
        save_file_button.setStyleSheet(PRIMARY_BUTTON_STYLE)
        save_file_button.clicked.connect(self.backup_database_to_file)
        
        return save_file_button

    def create_load_file_button(self):
        load_file_button = QPushButton("Загрузить")
        load_file_button.setStyleSheet(PRIMARY_BUTTON_STYLE)
        load_file_button.clicked.connect(self.restore_database_from_file)
        
        return load_file_button

    def create_search_widget(self):
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию и категории...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(SEARCH_STYLE)
        self.search_input.textChanged.connect(self.perform_search)
        
        return self.search_input

    def perform_search(self):
        CATEGORY_COLUMN = 1
        NAME_COLUMN = 2
        
        search_text = self.search_input.text().strip().lower()
        search_words = search_text.split()

        if not search_text:
            for row in range(self.table_db.rowCount()):
                self.table_db.setRowHidden(row, False)
            return
        
        for row in range(self.table_db.rowCount()):
            category_text = ""
            name_text = ""
            
            category_item = self.table_db.item(row, CATEGORY_COLUMN)
            if category_item:
                category_text = category_item.text().lower()
            
            name_item = self.table_db.item(row, NAME_COLUMN)
            if name_item:
                name_text = name_item.text().lower()
            
            # Объединяем текст из обеих колонок для поиска
            combined_text = f"{category_text} {name_text}"
            
            # Проверяем, что все слова поиска присутствуют в объединенном тексте
            match_found = all(word in combined_text for word in search_words)
            
            # Скрываем/показываем строку
            self.table_db.setRowHidden(row, not match_found)

    def create_table_db(self):
        table_db = QTableWidget()
        table_db.setStyleSheet(DATA_TABLE_STYLE)
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
            self.show_tool_buttons(row)
        else:
            self.hide_all_tool_buttons()

    def show_tool_buttons(self, row):
        """Показывает кнопки для выбранной строки"""
        self.hide_all_tool_buttons()
        
        if row in self.action_buttons:
            edit_btn, delete_btn = self.action_buttons[row]
            rect = self.table_db.visualRect(self.table_db.model().index(row, 0))
            table_width = self.table_db.viewport().width()
            btn_width = edit_btn.sizeHint().width()
            spacing = 5

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
        table_names = {
            "works": "Работы",
            "works_categories": "Категории работ",
            "materials": "Материалы",
            "materials_categories": "Категории материалов"
        }
        # Создаем выпадающий список для выбора таблицы
        table_selector = QComboBox()
        table_selector.setStyleSheet(DROPDOWN_STYLE)  # Применяем стиль
        for db_name, name in table_names.items():
            table_selector.addItem(name, db_name)
            if db_name == self.current_table:
                table_selector.setCurrentText(name)
        
        table_selector.currentTextChanged.connect(
            lambda text: self.on_table_changed(
                next(key for key, value in table_names.items() if value == text)
            )
        )
        return table_selector

    def create_header_of_table(self):
        """Создает фиксированный заголовок таблицы"""
        header_widget = QWidget()
        header_widget.setStyleSheet(TOOL_PANEL_STYLE)

        # Основной layout с фиксированными параметрами
        main_layout = QHBoxLayout(header_widget)
        # main_layout.setContentsMargins(0, 0, 0, 0)  # Отступы: слева, сверху, справа, снизу
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
        
        search_widget = self.create_search_widget()
        main_layout.addWidget(search_widget)

        # Растягивающийся элемент между комбобоксом и кнопкой
        main_layout.addStretch()
        
        load_file_button = self.create_load_file_button()
        load_file_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(load_file_button)
        
        save_file_button = self.create_save_file_button()
        save_file_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(save_file_button)

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
