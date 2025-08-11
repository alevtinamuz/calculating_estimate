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
    def __init__(self, parent, supabase, main_window):
        super().__init__(parent)
        self.supabase = supabase
        self.current_editor = None
        self.current_row = -1
        self.current_col = -1
        self.editor_pos_offset = QPoint(-70, 0)
        self.main_window = main_window
        self.search_line_edit = None
        self.last_selected_id = None
        
    def commitAndClose(self, editor):
        """Сохраняет данные и закрывает редактор"""
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.EndEditHint.SubmitModelCache)

    def createEditor(self, parent, option, index):
        self.current_row = index.row()
        self.current_col = index.column()

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

        search_text = ""
        if isinstance(text, str):
            search_text = text
        elif isinstance(text, QListWidgetItem):
            search_text = text.text()
        print({search_text})
        # Вызываем обновление только если есть текст для поиска
        
        if search_text:
            self.update_sub_list(search_text)

    def updateEditorGeometry(self, editor, option, index):
        """Позиционирование редактора с учетом границ экрана"""
        if index.column() in [1, 6]:  # Только для нужных колонок
            try:
                # Получаем геометрию ячейки
                rect = option.rect
                viewport = editor.parent()

                global_pos = viewport.mapToGlobal(rect.bottomLeft())

                # Получаем информацию об экране
                screen = viewport.screen()
                screen_geometry = screen.availableGeometry()

                # Рассчитываем размеры редактора
                editor_height = editor.sizeHint().height()
                editor_width = max(rect.width(), 300)

                editor_x = global_pos.x() - 30

                if global_pos.y() + editor_height > screen_geometry.bottom():
                    editor_y = global_pos.y() - editor_height - rect.height()
                else:
                    editor_y = global_pos.y()
                if editor_y < screen_geometry.top():
                    editor_y = screen_geometry.top()

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

    def load_initial_data(self, column):
        """Загрузка начальных данных в комбобоксы"""
        category_type = "works" if column == 1 else "materials"
        try:
            categories = self.supabase.table(f"{category_type}_categories").select('*').execute().data
            self.data = self.supabase.table(f"{category_type}").select('*').execute().data
            self.main_list.clear()
            self.sub_list.clear()
            all_categories_item = QListWidgetItem("Все категории")
            all_categories_item.setData(Qt.ItemDataRole.UserRole, 0)
            self.main_list.addItem(all_categories_item)
            empty_el = QListWidgetItem("-")
            empty_el.setData(Qt.ItemDataRole.UserRole, 0)  # Используем 0 как специальный ID
            empty_el.setData(Qt.ItemDataRole.UserRole + 1, True)  # Флаг "всегда видимый"
            self.sub_list.addItem(empty_el)

            for cat in categories:
                item = QListWidgetItem(cat['name'])
                item.setData(Qt.ItemDataRole.UserRole, cat['id'])  # Сохраняем id в UserRole
                self.main_list.addItem(item)
                
            for item in self.data:
                entity = QListWidgetItem(item['name'])
                entity.setData(Qt.ItemDataRole.UserRole, item['id'])
                self.sub_list.addItem(entity)
                
            
            self.main_list.setCurrentRow(0)

            # Загружаем подчиненные элементы
            self.update_sub_list()

        except Exception as e:
            print(f"Data loading error: {e}")

    def update_sub_list(self, text=""):
        """Обновление подчиненного комбобокса"""
        if hasattr(self, 'main_list') and self.main_list.count() > 0:
            cat_item = self.main_list.currentItem()
            # Получаем сохранённый id (аналог .currentData() в QComboBox)
            cat_id = cat_item.data(Qt.ItemDataRole.UserRole)

            text = text if isinstance(text, str) else ""

            try:
                for i in range(self.sub_list.count()):
                    self.sub_list.item(i).setHidden(False)
                    
                for i in range(self.sub_list.count()):
                    item = self.sub_list.item(i)
                    item_data = item.data(Qt.ItemDataRole.UserRole)
                    
                    if not item_data:
                        continue
                    
                    entity_data = next((x for x in getattr(self, 'data', []) if x['id'] == item_data), None)
                    
                    if not entity_data:
                        print ({entity_data})
                        continue
                
                    if cat_id and entity_data.get('category_id') != cat_id:
                        item.setHidden(True)
                        continue
                        
                    # Фильтр по тексту
                    if text:
                        name_match = text in entity_data['name'].lower()
                        keywords_match = text in entity_data.get('keywords', '').lower()
                        if not name_match and not keywords_match:
                            item.setHidden(True)

            except Exception as e:
                print(f"Sub-combo update error: {e}")

    def setModelData(self, editor, model, index):
        """Сохраняет выбранное значение в модель"""
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
