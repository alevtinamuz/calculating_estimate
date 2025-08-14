from PyQt6.QtCore import Qt, QPoint, QStringListModel, QLocale
from PyQt6.QtWidgets import QSpinBox, QComboBox, QHBoxLayout, QWidget, QStyledItemDelegate, QVBoxLayout, QLineEdit, \
    QListWidget, QListWidgetItem, QDoubleSpinBox
from PyQt6.QtGui import QDoubleValidator, QValidator

import getters
from design.styles import DROPDOWN_DELEGATE_STYLE, SPIN_BOX_STYLE


class DoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Устанавливаем локаль (например, русскую, чтобы по умолчанию использовалась запятая)
        self.setLocale(QLocale("en"))  # или QLocale('en') для точки

        curLocal = QLocale("en")

        print(curLocal.decimalPoint())
    
    def validate(self, text, pos):
        # Разрешаем и точку, и запятую
        if ',' in text:
            text = text.replace(',', '.')  # заменяем точку на запятую
            pos = text.find('.') + 1 if '.' in text else pos
        return super().validate(text, pos)
    
    def valueFromText(self, text):
        # Приводим введённый текст к формату с запятой
        text = text.replace(',', '.')
        return super().valueFromText(text)
    
    def textFromValue(self, value):
        # Форматируем вывод в соответствии с локалью
        # return self.locale().toString(value, 'f', self.decimals())
        return f"{value:.{self.decimals()}f}".replace(',', '.')

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, table_widget, supabase, main_window):
        super().__init__(table_widget)
        self.supabase = supabase
        self.table = table_widget
        self.current_editor = None
        self.current_row = -1
        self.current_col = -1
        self.editor_pos_offset = QPoint(-70, 0)
        self.main_window = main_window
        self.search_line_edit = None
        self.last_selected_id = None
        self.sections_list = None
        self.main_list = None
        self.sub_list = None
        
    def commitAndClose(self, editor):
        """Сохраняет данные и закрывает редактор"""
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.EndEditHint.SubmitModelCache)

    def createEditor(self, parent, option, index):
        self.current_row = index.row()
        self.current_col = index.column()

        if self.table.columnSpan(index.row(), index.column()) > 10:
            editor = QWidget(parent, Qt.WindowType.Popup)
            editor.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            editor.setStyleSheet(DROPDOWN_DELEGATE_STYLE)

            layout = QVBoxLayout(editor)

            # self.search_line_edit = QLineEdit(editor)
            # self.search_line_edit.setPlaceholderText("Поиск...")
            # # self.search_line_edit.textChanged.connect(self.filter_items)
            # layout.addWidget(self.search_line_edit)

            self.sections_list = QListWidget(editor)
            layout.addWidget(self.sections_list)

            self.load_initial_data()

            current_value = index.data(Qt.ItemDataRole.DisplayRole)

            if current_value:
                self.set_current_value_section(current_value)

            return editor

        if index.column() in [1, 6]:
            try:
                editor = QWidget(parent, Qt.WindowType.Popup)
                editor.setWindowFlag(Qt.WindowType.FramelessWindowHint)
                editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                editor.setStyleSheet(DROPDOWN_DELEGATE_STYLE)

                current_value = index.data(Qt.ItemDataRole.DisplayRole)

                layout = QVBoxLayout(editor)
                layout.setContentsMargins(2, 2, 2, 2)

                self.search_line_edit = QLineEdit(editor)
                self.search_line_edit.setPlaceholderText("Поиск...")
                self.search_line_edit.textChanged.connect(self.filter_items)
                layout.addWidget(self.search_line_edit)

                combo_container = QWidget(editor)
                combo_layout = QHBoxLayout(combo_container)
                combo_layout.setContentsMargins(0, 0, 0, 0)

                # Ваши комбобоксы
                self.main_list = QListWidget(combo_container)
                self.sub_list = QListWidget(combo_container)

                self.main_list.setWordWrap(True)  # Включаем перенос текста
                self.sub_list.setWordWrap(True)

                self.main_list.setObjectName("MainList")
                self.sub_list.setObjectName("SubList")

                self.main_list.setStyleSheet(DROPDOWN_DELEGATE_STYLE)
                self.sub_list.setStyleSheet(DROPDOWN_DELEGATE_STYLE)

                self.main_list.itemClicked.connect(self.update_sub_list)

                combo_layout.addWidget(self.main_list)
                combo_layout.addWidget(self.sub_list)
                layout.addWidget(combo_container)

                # Заполнение данными
                self.load_initial_data(index.column())

                if current_value:
                    self.set_current_value(current_value)

                self.current_editor = editor
                
                self.sub_list.itemDoubleClicked.connect(
                    lambda: self.commitAndClose(editor)  # Новый метод
                )

                return editor

            except Exception as e:
                print(f"Editor error: {e}")
                return super().createEditor(parent, option, index)

        elif index.column() in [3, 8]:  # Ячейки с количеством
            editor = DoubleSpinBox(parent)
            editor.setMinimum(0.00)
            editor.setMaximum(999999.99)
            editor.setDecimals(2)
            editor.setSingleStep(1.00)

            editor.setLocale(QLocale(QLocale.Language.English))

            editor.setStyleSheet(SPIN_BOX_STYLE)

            return editor

    def set_current_value_section(self, current_value):
        """Устанавливает текущее значение в комбобоксы"""
        if not current_value:
            return

        # Ищем значение в sub_list
        for i in range(self.sections_list.count()):
            item = self.sections_list.item(i)
            # Получаем текст (аналог .currentText() в QComboBox)
            item_text = item.text()
            # Получаем сохранённый id (аналог .currentData() в QComboBox)
            item_id = item.data(Qt.ItemDataRole.UserRole)

            if item_text == current_value:
                self.sections_list.setCurrentRow(i)
                self.last_selected_id = item_id
                break

    def set_current_value(self, current_value):
        """Устанавливает текущее значение в комбобоксы"""
        if not current_value:
            return

        # Ищем значение в sub_list
        for i in range(self.sub_list.count()):
            item = self.sub_list.item(i)
            # Получаем текст (аналог .currentText() в QComboBox)
            item_text = item.text()
            # Получаем сохранённый id (аналог .currentData() в QComboBox)
            item_id = item.data(Qt.ItemDataRole.UserRole)

            if item_text == current_value:
                self.sub_list.setCurrentRow(i)
                self.last_selected_id = item_id
                break

    def filter_items(self, text):
        """Фильтрует элементы в sub_list по введенному тексту"""
        if not hasattr(self, 'sub_list') or not self.sub_list.count():
            return

        if text:
            self.update_sub_list(text)

    def updateEditorGeometry(self, editor, option, index):
        """Позиционирование редактора с учетом границ экрана"""

        # if self.table.columnSpan(index.row(), index.column()) > 10:

        if index.column() in [0, 6]:  # Только для нужных колонок
            try:
                # Получаем геометрию ячейки
                rect = option.rect
                viewport = editor.parent()

                global_pos = viewport.mapToGlobal(rect.bottomLeft())

                # Получаем информацию об экране
                screen = viewport.screen()
                screen_geometry = screen.availableGeometry()

                # Рассчитываем размеры редактора
                editor_height = 300
                editor_width = max(rect.width(), 300)
                #
                editor_x = global_pos.x() - 30
                editor_y = global_pos.y()
                #
                # if global_pos.y() + editor_height > screen_geometry.bottom():
                #     editor_y = global_pos.y() - editor_height - rect.height()
                # else:
                #     editor_y = global_pos.y()
                # if editor_y < screen_geometry.top():
                #     editor_y = screen_geometry.top()

                # Применяем вычисленные координаты
                editor.move(QPoint(editor_x, editor_y))
                editor.resize(editor_width, editor_height)

            except Exception as e:
                print(f"Editor geometry error: {e}")
                # Фоллбэк на стандартное поведение
                super().updateEditorGeometry(editor, option, index)
        else:
            # Для других колонок - стандартное поведение
            super().updateEditorGeometry(editor, option, index)

    def load_initial_data(self, column=0):
        """Загрузка начальных данных в комбобоксы"""
        entity_type = "works" if column == 1 else "materials"
        try:

            if self.table.columnSpan(self.current_row, self.current_col) > 10:
                sections = self.supabase.table("sections").select("*").execute().data
                self.sections_list.clear()
                print(*[section['name'] for section in sections])

                for section in sections:
                    item = QListWidgetItem(section['name'])
                    item.setData(Qt.ItemDataRole.UserRole, section['id'])
                    self.sections_list.addItem(item)

                self.sections_list.setCurrentRow(0)

                return

            categories = self.supabase.table(f"{entity_type}_categories").select('*').execute().data
            self.main_list.clear()
            all_categories_item = QListWidgetItem("Все категории")
            all_categories_item.setData(Qt.ItemDataRole.UserRole, 0)
            self.main_list.addItem(all_categories_item)

            for cat in categories:
                item = QListWidgetItem(cat['name'])
                item.setData(Qt.ItemDataRole.UserRole, cat['id'])  # Сохраняем id в UserRole
                self.main_list.addItem(item)

            self.main_list.setCurrentRow(0)

            # Загружаем подчиненные элементы
            self.update_sub_list()

        except Exception as e:
            print(f"Data loading error: {e}")

    def update_sub_list(self, text=""):
        """Обновление подчиненного комбобокса"""
        if hasattr(self, 'main_list') and self.main_list.count() > 0:
            cat_item = self.main_list.currentItem()
            # Получаем текст (аналог .currentText() в QComboBox)
            cat_text = cat_item.text()
            # Получаем сохранённый id (аналог .currentData() в QComboBox)
            cat_id = cat_item.data(Qt.ItemDataRole.UserRole)

            entity_type = "works" if self.current_col == 1 else "materials"
            items = []

            try:
                if text:
                    items = getters.get_entity_by_substr(self.supabase, entity_type, text, cat_id)
                if not items:
                    if cat_id:
                        items = self.supabase.table(entity_type) \
                            .select('*') \
                            .eq('category_id', cat_id) \
                            .execute().data
                    else:
                        items = self.supabase.table(entity_type) \
                            .select('*') \
                            .execute().data

                self.sub_list.clear()
                empty_el = QListWidgetItem("-")
                empty_el.setData(Qt.ItemDataRole.UserRole, 0)
                self.sub_list.addItem(empty_el)

                for item in items:
                    el = QListWidgetItem(item['name'])
                    el.setData(Qt.ItemDataRole.UserRole, item['id'])  # Сохраняем id в UserRole
                    self.sub_list.addItem(el)

            except Exception as e:
                print(f"Sub-combo update error: {e}")

    def setModelData(self, editor, model, index):
        """Сохраняет выбранное значение в модель"""
        if self.table.columnSpan(self.current_row, self.current_col) > 10:

            if not self.sections_list.currentItem():
                self.sections_list.setCurrentRow(0)

            selected_item = self.sections_list.currentItem()
            selected_text = selected_item.text()
            # selected_id = selected_item.data(Qt.ItemDataRole.UserRole)

            model.setData(index, selected_text)

            return

        if index.column() in [1, 6]:  # Обрабатываем только колонки с названиями

            if not self.sub_list.currentItem():
                self.sub_list.setCurrentRow(0)

            selected_item = self.sub_list.currentItem()
            selected_text = selected_item.text()
            selected_id = selected_item.data(Qt.ItemDataRole.UserRole)

            model.setData(index, selected_text)

            try:
                # Определяем тип сущности (работа или материал)
                entity_type = "works" if index.column() == 1 else "materials"
                entities = getters.get_entity_by_id(self.supabase, entity_type, selected_id)

                entity = entities[0]

                if index.column() == 1:  # Обработка работы

                    # Обновляем ячейки цены и единиц измерения
                    price_index = model.index(index.row(), 4)
                    model.setData(price_index, entity['price'])

                    unit_index = model.index(index.row(), 2)
                    model.setData(unit_index, entity['unit'])
                    
                    quantity_index = model.index(index.row(), 3)
                    model.setData(quantity_index, 1.0)

                elif index.column() == 6:  # Обработка материала

                    # Находим родительскую работу для этого материала
                    work_row = index.row()

                    while work_row >= 0 and not model.index(work_row, 0).data():
                        work_row -= 1

                    if work_row >= 0:

                        # Обновляем ячейки цены и единиц измерения материала
                        price_index = model.index(index.row(), 9)
                        model.setData(price_index, entity['price'])

                        unit_index = model.index(index.row(), 7)
                        model.setData(unit_index, entity['unit'])
                        
                        quantity_index = model.index(index.row(), 8)
                        model.setData(quantity_index, 1.0)

            except IndexError as ie:
                print(f"Ошибка индекса при обновлении данных: {ie}")
            except Exception as e:
                print(f"Не удалось обновить данные: {e}")

        elif index.column() in [3, 8]:  # Для ячеек с количеством
            try:
                value = editor.text()
                # model.setData(index, float(value))
                model.setData(index, value, Qt.ItemDataRole.EditRole)
                # Сохраняем отображаемое значение с точкой
                model.setData(index, f"{value}", Qt.ItemDataRole.DisplayRole)

                print(model.data(index))
            except Exception as e:
                print(f"Не удалось обновить количество: {e}")

    def destroyEditor(self, editor, index):
        """Очищаем ссылки при уничтожении редактора"""
        self.current_editor = None
        super().destroyEditor(editor, index)
