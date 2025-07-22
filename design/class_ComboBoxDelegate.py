import os
from supabase import create_client, Client

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QSpinBox, QComboBox, QHBoxLayout, QWidget, QStyledItemDelegate, QVBoxLayout, QLineEdit
from dotenv import load_dotenv

import getters
from design.classes import WorkItem, MaterialItem
from design.styles import DROPDOWN_DELEGATE_STYLE


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent, supabase, main_window):
        super().__init__(parent)
        self.supabase = supabase
        self.current_editor = None
        self.current_row = -1
        self.current_col = -1
        self.editor_pos_offset = QPoint(-70, 0)
        self.main_window = main_window
        self.search_line_edit = None

    def createEditor(self, parent, option, index):
        self.current_row = index.row()
        self.current_col = index.column()

        if index.column() in [1, 6]:
            try:
                editor = QWidget(parent, Qt.WindowType.Popup)
                editor.setWindowFlag(Qt.WindowType.FramelessWindowHint)
                editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                editor.setStyleSheet(DROPDOWN_DELEGATE_STYLE)

                layout = QVBoxLayout(editor)
                layout.setContentsMargins(2, 2, 2, 2)

                self.search_line_edit = QLineEdit(editor)
                self.search_line_edit.setPlaceholderText("Поиск...")
                # self.search_line_edit.textChanged.connect(self.)
                layout.addWidget(self.search_line_edit)

                combo_container = QWidget(editor)
                combo_layout = QHBoxLayout(combo_container)
                combo_layout.setContentsMargins(0, 0, 0, 0)

                # Ваши комбобоксы
                self.main_combo = QComboBox(combo_container)
                self.sub_combo = QComboBox(combo_container)

                self.main_combo.currentIndexChanged.connect(self.update_sub_combo)

                combo_layout.addWidget(self.main_combo)
                combo_layout.addWidget(self.sub_combo)
                layout.addWidget(combo_container)

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

    def setModelData(self, editor, model, index):
        """Сохраняет выбранное значение в модель"""
        if index.column() in [1, 6]:  # Обрабатываем только колонки с названиями
            selected_id = self.sub_combo.currentData()
            selected_text = self.sub_combo.currentText()
            model.setData(index, selected_text)

            try:
                # Определяем тип сущности (работа или материал)
                entity_type = "works" if index.column() == 1 else "materials"
                entities = getters.get_entity_by_id(self.supabase, entity_type, selected_id)

                if not entities:
                    print(f"Не найдена сущность с ID: {selected_id}")
                    return

                entity = entities[0]

                if index.column() == 1:  # Обработка работы
                    # Проверяем и расширяем список работ при необходимости
                    while index.row() >= len(self.main_window.works):
                        self.main_window.works.append(WorkItem())

                    work = self.main_window.works[index.row()]
                    work.name = selected_text
                    work.unit = entity['unit']

                    # Обновляем ячейки цены и единиц измерения
                    price_index = model.index(index.row(), 4)
                    model.setData(price_index, entity['price'])

                    unit_index = model.index(index.row(), 2)
                    model.setData(unit_index, entity['unit'])

                elif index.column() == 6:  # Обработка материала
                    # Находим родительскую работу для этого материала
                    work_row = index.row()
                    while work_row >= 0 and not model.index(work_row, 0).data():
                        work_row -= 1

                    if work_row >= 0:
                        # Проверяем границы списка работ
                        if work_row >= len(self.main_window.works):
                            # Добавляем новую работу, если не существует
                            self.main_window.works.append(WorkItem())

                        # Добавляем новый материал к работе
                        material = MaterialItem()
                        material.name = selected_text
                        material.unit = entity['unit']
                        material.price = entity['price']

                        self.main_window.works[work_row].materials.append(material)

                        # Обновляем ячейки цены и единиц измерения материала
                        price_index = model.index(index.row(), 9)
                        model.setData(price_index, entity['price'])

                        unit_index = model.index(index.row(), 7)
                        model.setData(unit_index, entity['unit'])

            except IndexError as ie:
                print(f"Ошибка индекса при обновлении данных: {ie}")
            except Exception as e:
                print(f"Не удалось обновить данные: {e}")

        elif index.column() in [3, 8]:  # Для ячеек с количеством
            try:
                value = editor.value()
                model.setData(index, value)
            except Exception as e:
                print(f"Не удалось обновить количество: {e}")

    def destroyEditor(self, editor, index):
        """Очищаем ссылки при уничтожении редактора"""
        self.current_editor = None
        self.main_combo = None
        self.sub_combo = None
        super().destroyEditor(editor, index)