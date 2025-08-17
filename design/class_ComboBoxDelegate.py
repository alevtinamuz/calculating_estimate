from PyQt6.QtCore import Qt, QPoint, QStringListModel, QLocale, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QSpinBox, QComboBox, QHBoxLayout, QWidget, QStyledItemDelegate, QVBoxLayout, QLineEdit, \
    QListWidget, QListWidgetItem, QDoubleSpinBox, QLabel
from PyQt6.QtGui import QDoubleValidator, QValidator, QCursor, QMovie

import getters
import os
from design.styles import DROPDOWN_DELEGATE_STYLE, SPIN_BOX_STYLE


class DoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Устанавливаем локаль (например, русскую, чтобы по умолчанию использовалась запятая)
        self.setLocale(QLocale("en"))  # или QLocale('en') для точки

        curLocal = QLocale("en")
    
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

class DataLoaderThread(QThread):
    data_loaded = pyqtSignal(object)


    def __init__(self, load_func, *args):
        super().__init__()
        self.load_func = load_func
        self.args = args

    def run(self):
        try:
            result = self.load_func(*self.args)
            self.data_loaded.emit(result)
        except Exception as e:
            print(f"Error in loader thread: {e}")
            self.data_loaded.emit(None)


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, table_widget, supabase, main_window, model):
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
        self.section_id = None
        self.model = model

    def commitAndClose(self, editor):
        """Сохраняет данные и закрывает редактор"""
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.EndEditHint.SubmitModelCache)

    def createEditor(self, parent, option, index):
        self.current_row = index.row()
        self.current_col = index.column()

        gif_path = os.path.join(os.path.dirname(__file__), "spinner.gif")
        # self.loading_label = QLabel(parent)
        # self.loading_movie = QMovie(gif_path)
        # self.loading_label.setMovie(self.loading_movie)
        # self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        section_index = self.model.find_section_by_row(self.current_row)
        section_name = self.model.estimate[section_index].name
        self.section_id = getters.get_section_by_name(self.supabase, section_name)

        if self.table.columnSpan(index.row(), index.column()) > 10:
            editor = QWidget(parent, Qt.WindowType.Popup)
            editor.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            editor.setStyleSheet(DROPDOWN_DELEGATE_STYLE)

            layout = QVBoxLayout(editor)
            layout.setContentsMargins(2, 2, 2, 2)

            # layout.addWidget(self.loading_label)
            # self.loading_movie.start()
            editor.sections_list = QListWidget(editor)
            layout.addWidget(editor.sections_list)

            editor.loading_label = QLabel(editor.sections_list)
            editor.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            editor.loading_movie = QMovie(gif_path)
            editor.loading_label.setMovie(editor.loading_movie)

            # Растягиваем на весь список
            def update_loading_geometry():
                editor.loading_label.setGeometry(
                    0, 0,
                    editor.sections_list.width(),
                    editor.sections_list.height()
                )

            editor.sections_list.showEvent = lambda e: update_loading_geometry()
            editor.loading_movie.start()

            # self.sections_list.hide()

            self.sections_list = editor.sections_list

            self.loader_worker = DataLoaderThread(self.load_initial_data)
            self.loader_worker.data_loaded.connect(lambda: self.on_data_loaded(editor, index))
            self.loader_worker.start()

            # self.load_initial_data()

            # current_value = index.data(Qt.ItemDataRole.DisplayRole)

            # if current_value:
            #     self.set_current_value_section(current_value)

            # self.sections_list.itemDoubleClicked.connect(
            #     lambda: self.commitAndClose(editor)  # Новый метод
            # )
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

                # layout.addWidget(self.loading_label)
                # self.loading_movie.start()

                editor.search_line_edit = QLineEdit(editor)
                editor.search_line_edit.setPlaceholderText("Поиск...")
                editor.search_line_edit.textChanged.connect(self.filter_items)
                layout.addWidget(editor.search_line_edit)

                combo_container = QWidget(editor)
                combo_layout = QHBoxLayout(combo_container)
                combo_layout.setContentsMargins(0, 0, 0, 0)

                # combo_layout.addWidget(self.loading_label)
                # self.loading_movie.start()

                # Ваши комбобоксы
                editor.main_list = QListWidget(combo_container)
                editor.sub_list = QListWidget(combo_container)

                editor.main_list.setWordWrap(True)  # Включаем перенос текста
                editor.sub_list.setWordWrap(True)

                editor.main_list.setObjectName("MainList")
                editor.sub_list.setObjectName("SubList")

                editor.main_list.setStyleSheet(DROPDOWN_DELEGATE_STYLE)
                editor.sub_list.setStyleSheet(DROPDOWN_DELEGATE_STYLE)

                editor.main_list.itemClicked.connect(self.update_sub_list)

                editor.main_loading_movie = QMovie(gif_path)
                editor.main_loading_label = QLabel(editor.main_list)
                editor.main_loading_label.setMovie(editor.main_loading_movie)
                editor.main_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                editor.main_loading_label.setGeometry(editor.main_list.rect())

                editor.sub_loading_movie = QMovie(gif_path)
                editor.sub_loading_label = QLabel(editor.sub_list)
                editor.sub_loading_label.setMovie(editor.sub_loading_movie)
                editor.sub_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                editor.sub_loading_label.setGeometry(editor.sub_list.rect())

                editor.main_loading_movie.start()
                editor.sub_loading_movie.start()

                combo_layout.addWidget(editor.main_list)
                combo_layout.addWidget(editor.sub_list)
                layout.addWidget(combo_container)

                self.main_list = editor.main_list
                self.sub_list = editor.sub_list
                self.search_line_edit = editor.search_line_edit

                self.loader_worker = DataLoaderThread(self.load_initial_data, index.column())
                self.loader_worker.data_loaded.connect(lambda: self.on_column_data_loaded(editor, current_value))
                self.loader_worker.start()

                def focus():
                    try:
                        self.search_line_edit.setFocus()

                    except Exception as e:
                        print(f"Focus error: {e}")

                QTimer.singleShot(200, lambda: focus())

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

    def on_data_loaded(self, editor, index):
        """Handle data loaded for the sections list"""
        try:
            if not editor or not hasattr(editor, 'sections_list'):
                return

            if hasattr(editor, 'loading_movie'):
                editor.loading_movie.stop()
            if hasattr(editor, 'loading_label'):
                editor.loading_label.hide()

            editor.sections_list.show()

            if index.data(Qt.ItemDataRole.DisplayRole):
                self.set_current_value_section(index.data(Qt.ItemDataRole.DisplayRole))

            editor.sections_list.itemDoubleClicked.connect(lambda: self.commitAndClose(editor))

            # Обновляем геометрию после загрузки данных
            # self.updateEditorGeometry(editor, None, index)

        except Exception as e:
            print(f"Error in on_data_loaded: {e}")

    def on_column_data_loaded(self, editor, current_value):
        """Handle data loaded for column-specific lists"""
        try:
            if not editor:
                return

            if hasattr(editor, 'main_loading_movie'):
                editor.main_loading_movie.stop()
            if hasattr(editor, 'main_loading_label'):
                editor.main_loading_label.hide()
            if hasattr(editor, 'sub_loading_movie'):
                editor.sub_loading_movie.stop()
            if hasattr(editor, 'sub_loading_label'):
                editor.sub_loading_label.hide()

            if hasattr(editor, 'search_line_edit'):
                editor.search_line_edit.show()
            if hasattr(editor, 'main_list'):
                editor.main_list.show()
            if hasattr(editor, 'sub_list'):
                editor.sub_list.show()

                if current_value:
                    self.set_current_value(current_value)

                editor.sub_list.itemDoubleClicked.connect(lambda: self.commitAndClose(editor))

                # Убираем принудительное изменение размеров для main_list и sub_list
                editor.adjustSize()  # Просто делаем автоподбор размеров

        except Exception as e:
            print(f"Error in on_column_data_loaded: {e}")

    def destroyEditor(self, editor, index):
        try:
            if hasattr(self, 'loader_worker') and self.loader_worker.isRunning():
                self.loader_worker.quit()
                self.loader_worker.wait()
        except Exception as e:
            print(f"Error in destroyEditor: {e}")
        finally:
            super().destroyEditor(editor, index)

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

        search_text = ""
        if isinstance(text, str):
            search_text = text
        elif isinstance(text, QListWidgetItem):
            search_text = text.text()
        # Вызываем обновление только если есть текст для поиска

        if search_text:
            self.update_sub_list(search_text)

    def updateEditorGeometry(self, editor, option, index):
        """Позиционирование редактора с учетом границ экрана"""

        if self.table.columnSpan(index.row(), index.column()) > 10:
            if not hasattr(editor, 'sections_list'):
                return

            # Получаем геометрию ячейки
            rect = option.rect if option else editor.geometry()
            viewport = editor.parent()
            cursor_pos = QCursor.pos()
            global_pos = viewport.mapToGlobal(rect.bottomLeft())
            screen = viewport.screen().availableGeometry()

            # Рассчитываем размеры на основе содержимого
            width = editor.sections_list.sizeHintForColumn(0)# + отступы
            item_height = editor.sections_list.sizeHintForRow(0)
            visible_items = min(10, editor.sections_list.count())
            height = item_height * visible_items + 10

            # Ограничиваем минимальные/максимальные размеры
            width = max(250, min(width, 500))
            height = max(200, min(height, 600))

            # Позиционирование
            editor_x = max(screen.left(), cursor_pos.x() - width // 2)
            editor_x = min(editor_x, screen.right() - width)

            if global_pos.y() + height > screen.bottom():
                editor_y = global_pos.y() - height - rect.height()
            else:
                editor_y = global_pos.y()

            if editor_y < screen.top():
                editor_y = screen.top()

            # Устанавливаем размеры и позицию
            editor.setFixedSize(width, height)
            editor.move(editor_x, editor_y)
            editor.sections_list.setFixedSize(width - 10, height - 10)
        elif index.column() in [1, 6]:  # Только для нужных колонок
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

    def load_initial_data(self, column=0):
        """Загрузка начальных данных в комбобоксы"""
        category_type = "works" if column == 1 else "materials"
        try:
            if self.table.columnSpan(self.current_row, self.current_col) > 10:
                sections = self.supabase.table("sections").select("*").execute().data
                self.sections_list.clear()

                for section in sections:
                    item = QListWidgetItem(section['name'])
                    item.setData(Qt.ItemDataRole.UserRole, section['id'])
                    self.sections_list.addItem(item)

                self.sections_list.setCurrentRow(0)

                return

            self.main_list.clear()
            self.sub_list.clear()

            if category_type == "materials":
                categories = self.supabase.table(f"{category_type}_categories").select('*').execute().data

            else:
                categories = getters.get_categories_by_section_id(self.supabase, self.section_id)
                if not categories:
                    categories = self.supabase.table(f"{category_type}_categories").select('*').execute().data

            # Получаем все работы
            all_works = self.supabase.table(f"{category_type}").select('*').execute().data

            # Если есть section_id и это не материалы, фильтруем работы по категориям раздела
            if category_type == "works" and self.section_id:
                # Получаем ID категорий, связанных с разделом
                section_categories = getters.get_categories_by_section_id(self.supabase, self.section_id)
                section_category_ids = [cat['id'] for cat in section_categories]

                # Фильтруем работы - оставляем только те, которые принадлежат категориям раздела
                self.data = [work for work in all_works
                            if work.get('category_id') in section_category_ids]
            else:
                self.data = all_works

            # self.data = self.supabase.table(f"{category_type}").select('*').execute().data
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
        if self.table.columnSpan(self.current_row, self.current_col) > 10:

            if not self.sections_list.currentItem():
                self.sections_list.setCurrentRow(0)

            selected_item = self.sections_list.currentItem()
            if selected_item:
                selected_text = selected_item.text()
            # selected_id = selected_item.data(Qt.ItemDataRole.UserRole)

                model.setData(index, selected_text)
                model.setData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

            return

        if index.column() in [1, 6]:  # Обрабатываем только колонки с названиями

            if not self.sub_list.currentItem():
                self.sub_list.setCurrentRow(0)

            selected_item = self.sub_list.currentItem()
            if selected_item:
                selected_text = selected_item.text()
                selected_id = selected_item.data(Qt.ItemDataRole.UserRole)

                model.setData(index, selected_text)

                model.setData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

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
                    current_quantity = self.table.item(index.row(), 3).text() if self.table.item(index.row(), 3) else 1.0
                    model.setData(quantity_index, float(current_quantity))

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
                        current_quantity = self.table.item(index.row(), 8).text() if self.table.item(index.row(), 8) else 1.0
                        model.setData(quantity_index, float(current_quantity))

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

            except Exception as e:
                print(f"Не удалось обновить количество: {e}")

    def destroyEditor(self, editor, index):
        """Очищаем ссылки при уничтожении редактора"""
        self.current_editor = None
        super().destroyEditor(editor, index)
