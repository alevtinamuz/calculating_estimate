from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, \
    QPushButton, QMainWindow

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.classes import MaterialItem, WorkItem
from design.styles import LABEL_STYLE, TABLE_STYLE, BUTTON_STYLE


class PageEstimate(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        self.supabase = supabase
        self.works = []
        self.table_estimate = None
        self.data_handler = EstimateDataHandler(supabase)
        self.table_manager = None
        self.main_widget = None
        self.main_layout = None

    def create_page_estimate(self):
        """Создает вторую страницу (смета)"""
        page_estimate = QWidget()
        layout = QVBoxLayout()

        self.main_widget = page_estimate
        self.main_layout = layout

        label_estimate = QLabel("Страница сметы")
        label_estimate.setStyleSheet(LABEL_STYLE)
        layout.addWidget(label_estimate)

        table_estimate = self.create_table_estimate()
        layout.addWidget(table_estimate)

        page_estimate.setLayout(layout)

        return page_estimate

    def create_table_estimate(self):
        try:
            estimate_container = QWidget()
            layout = QVBoxLayout(estimate_container)

            # Создаем таблицу как атрибут класса
            self.table_estimate = QTableWidget()

            self.table_manager = EstimateTableManager(self.table_estimate, self.supabase)

            self.table_manager.setup_table()

            layout.addWidget(self.table_estimate)

            button_panel = self.create_button_panel()
            layout.addWidget(button_panel)

            estimate_container.setLayout(layout)

            print("Таблица успешно создана")

            return estimate_container

        except Exception as e:
            self.show_error("Ошибка создания таблицы", str(e))
            print(f"Ошибка создания таблицы: {e}")
            raise

    def add_row_work(self):
        try:
            self.table_manager.add_row_work()

        except Exception as e:
            self.show_error("Не удалось добавить строку работы", str(e))

    def add_row_material(self):
        try:

            self.table_manager.add_row_material()

        except Exception as e:
            self.show_error("Не удалось добавить строку материалов", str(e))

    def create_button_panel(self):
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)

        add_work_btn = self.create_button("Добавить работу", lambda: self.add_row_work())
        add_material_btn = self.create_button("Добавить материал", lambda: self.add_row_material())

        button_layout.addWidget(add_work_btn)
        button_layout.addWidget(add_material_btn)

        return button_panel

    def create_button(self, text, handler):
        btn = QPushButton(text)
        btn.setStyleSheet(BUTTON_STYLE)
        btn.clicked.connect(handler)

        return btn

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)


class EstimateTableManager:
    def __init__(self, table_widget, supabase):
        self.table = table_widget
        self.supabase = supabase
        self.works = []

    def setup_table(self):
        """Настройка таблицы"""
        self.configure_table_appearance()
        self.setup_headers()
        self.setup_delegates()

    def configure_table_appearance(self):
        """Настраивает внешний вид таблицы"""
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.EditKeyPressed
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def setup_headers(self):
        """Устанавливает заголовки таблицы"""
        headers = [
            "№ п/п", "Наименование работ и затрат", "Ед. изм.", "К-во",
            "Фактический ФОТ на ед., руб", "ФОТ всего, руб", "Наименование материалов",
            "Ед. изм.", "К-во", "Цена, руб", "Сумма, руб", "Всего, руб"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def setup_delegates(self):
        """Устанавливает делегаты, кем бы они ни были"""
        delegate = ComboBoxDelegate(self.table, self.supabase, self)
        self.table.setItemDelegate(delegate)

    def add_row_work(self):
        """Добавляет строку с работой"""
        table = self.table
        row_count = table.rowCount()
        table.insertRow(row_count)

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

        for col in range(table.columnCount()):
            if not table.item(row_count, col):  # Если ячейка еще не создана
                item = QTableWidgetItem("")
                table.setItem(row_count, col, item)

            # Устанавливаем атрибут для работы
            item = table.item(row_count, col)
            item.setData(Qt.ItemDataRole.UserRole, "is_work")

    def add_row_material(self):
        """Добавляет строку с материалами для выбранной работы"""
        table = self.table

        # 1. Находим индекс выделенной работы в списке self.works
        work_idx = self.find_selected_work_index()
        if work_idx < 0 or work_idx >= len(self.works):
            work_idx = len(self.works) - 1

        # 2. Вычисляем позицию вставки в таблице
        insert_row = self.get_work_end_row(work_idx) + 1

        # 3. Вставляем новую строку
        table.insertRow(insert_row)

        # 4. Добавляем материал в модель данных
        self.works[work_idx].materials.append(MaterialItem())

        # 5. Полностью перестраиваем объединение ячеек
        self.rebuild_all_spans()

        # 6. Заполняем ячейки материала
        for col in range(6, table.columnCount()):
            item = QTableWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, "is_material")
            table.setItem(insert_row, col, item)

        # 7. Обновляем выделение
        self.update_selection(insert_row)

    def find_selected_work_index(self):
        """Находит индекс выделенной работы в self.works"""
        table = self.table
        selected_items = table.selectedItems()

        if not selected_items or not self.works:
            return len(self.works) - 1

        selected_row = selected_items[0].row()
        current_row = 0

        for i, work in enumerate(self.works):
            work_height = len(work.materials) + 1
            if current_row <= selected_row < current_row + work_height:
                return i
            current_row += work_height

        return len(self.works) - 1

    def get_work_end_row(self, work_idx):
        """Возвращает последнюю строку указанной работы в таблице"""
        if work_idx < 0 or work_idx >= len(self.works):
            return 0

        end_row = 0
        for i in range(work_idx + 1):
            end_row += len(self.works[i].materials) + 1

        return end_row - 1

    def rebuild_all_spans(self):
        """Полностью перестраивает все объединения ячеек"""
        table = self.table
        current_row = 0

        # 1. Сначала сбрасываем все объединения
        for row in range(table.rowCount()):
            for col in range(6):
                table.setSpan(row, col, 1, 1)

        # 2. Затем устанавливаем новые объединения
        for work in self.works:
            span_height = len(work.materials) + 1

            for col in range(6):
                table.setSpan(current_row, col, span_height, 1)

            current_row += span_height

    def update_selection(self, row):
        """Обновляет выделение строки"""
        table = self.table
        table.clearSelection()

        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                item.setSelected(True)


class EstimateDataHandler:
    def __init__(self, supabase):
        self.supabase = supabase
        self.works = []

    def add_work_item(self):
        new_work = WorkItem()
        self.works.append(new_work)
        return new_work

    def add_material_to_work(self, work_index):
        if 0 <= work_index < len(self.works):
            new_material = MaterialItem()
            self.works[work_index].materials.append(new_material)
            return new_material
        return None


# class PageEstimate2(QMainWindow):
#     def __init__(self, supabase):
#         super().__init__()
#         self.supabase = supabase
#         self.data_handler = EstimateDataHandler(supabase)
#         self.table_manager = None
#         # self.init_ui()
#
#     # def init_ui(self):
#         # self.setWindowTitle("Смета")
#         # self._create_main_widget()
#         # self.setup_layout()
#
#     def _create_main_widget(self):
#         self.main_widget = QWidget()
#         self.main_layout = QVBoxLayout(self.main_widget)
#
#         self._create_header()
#         self._create_table_section()
#         self._create_button_panel()
#
#         self.setCentralWidget(self.main_widget)
#
#     def _create_header(self):
#         self.header_label = QLabel("Страница сметы")
#         self.header_label.setStyleSheet(LABEL_STYLE)
#         self.main_layout.addWidget(self.header_label)
#
#     def _create_table_section(self):
#         self.table_container = QWidget()
#         self.table_layout = QVBoxLayout(self.table_container)
#
#         self.table_estimate = QTableWidget()
#         self.table_manager = EstimateTableManager(self.table_estimate, self.supabase)
#         self.table_manager.setup_table()
#
#         self.table_layout.addWidget(self.table_estimate)
#         self.main_layout.addWidget(self.table_container)
#
#     def _create_button_panel(self):
#         self.button_panel = QWidget()
#         self.button_layout = QHBoxLayout(self.button_panel)
#
#         self.add_work_btn = self.create_button("Добавить работу", self._add_work)
#         self.add_material_btn = self.create_button("Добавить материал", self._add_material)
#
#         self.button_layout.addWidget(self.add_work_btn)
#         self.button_layout.addWidget(self.add_material_btn)
#         self.main_layout.addWidget(self.button_panel)
#
#
#     def _add_work(self):
#         try:
#             self._insert_work_row()
#             self.data_handler.add_work_item()
#         except Exception as e:
#             self._show_error("Ошибка добавления работы", str(e))
#
#     def _add_material(self):
#         try:
#             if not self.data_handler.works:
#                 self._add_work()
#                 return
#
#             self._insert_material_row()
#             self.data_handler.add_material_to_work(-1)  # Добавляем к последней работе
#         except Exception as e:
#             self._show_error("Ошибка добавления материала", str(e))
#
#     def _show_error(self, title, message):
#         QMessageBox.critical(self, title, message)
#
#     def _insert_work_row(self):
#         """Добавляет новую строку работы в таблицу сметы"""
#         try:
#             # Получаем текущее количество строк
#             row_position = self.table_estimate.rowCount()
#             self.table_estimate.insertRow(row_position)
#
#             # Добавляем работу через data handler
#             work_item = self.data_handler.add_work_item()
#
#             # Настраиваем ячейки через table manager
#             self._configure_work_row(row_position, work_item)
#
#             # Устанавливаем номер п/п
#             self._update_row_numbers()
#
#         except Exception as e:
#             self._show_error("Ошибка добавления работы", str(e))
#             # Откатываем изменения если не удалось
#             self.table_estimate.removeRow(row_position)
#             raise
#
#     def _configure_work_row(self, row, work_item):
#         """Конфигурирует ячейки строки работы"""
#         # Номер п/п (будет обновлен в _update_row_numbers)
#         num_item = QTableWidgetItem("")
#         num_item.setData(Qt.ItemDataRole.UserRole, "work_number")
#         self.table_estimate.setItem(row, 0, num_item)
#
#         # Основные колонки работы
#         columns = [
#             (1, "work_name", "Наименование работы"),
#             (2, "work_unit", "ед.изм."),
#             (3, "work_quantity", "1"),
#             (4, "work_salary_per_unit", "0"),
#             (5, "work_total_salary", "0")
#         ]
#
#         for col, field, default in columns:
#             item = QTableWidgetItem(default)
#             item.setData(Qt.ItemDataRole.UserRole, field)
#             item.setData(Qt.ItemDataRole.UserRole + 1, work_item)  # Связь с объектом WorkItem
#             self.table_estimate.setItem(row, col, item)
#
#         # Пустые колонки для материалов (будут заполнены при добавлении материалов)
#         for col in range(6, self.table_estimate.columnCount()):
#             item = QTableWidgetItem("")
#             item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
#             self.table_estimate.setItem(row, col, item)
#
#     def _insert_material_row(self):
#         """Добавляет строку материала к последней работе"""
#         try:
#             if not self.data_handler.works:
#                 self._insert_work_row()
#
#             # Получаем последнюю работу
#             last_work = self.data_handler.works[-1]
#             material_item = self.data_handler.add_material_to_work(-1)
#
#             # Находим родительскую строку работы
#             work_row = self._find_work_row_for_material()
#             if work_row is None:
#                 raise ValueError("Не найдена строка работы для материала")
#
#             # Вставляем строку материала
#             material_row = work_row + last_work.materials_count()
#             self.table_estimate.insertRow(material_row)
#
#             # Конфигурируем строку материала
#             self._configure_material_row(material_row, work_row, material_item)
#
#             # Обновляем объединение ячеек работы
#             self._update_work_cell_spans(work_row)
#
#         except Exception as e:
#             self._show_error("Ошибка добавления материала", str(e))
#             if material_row:
#                 self.table_estimate.removeRow(material_row)
#             raise
#
#     def _configure_material_row(self, material_row, work_row, material_item):
#         """Конфигурирует ячейки строки материала"""
#         # Колонки материала
#         columns = [
#             (6, "material_name", "Наименование материала"),
#             (7, "material_unit", "ед.изм."),
#             (8, "material_quantity", "1"),
#             (9, "material_price", "0"),
#             (10, "material_total", "0"),
#             (11, "row_total", "0")
#         ]
#
#         for col, field, default in columns:
#             item = QTableWidgetItem(default)
#             item.setData(Qt.ItemDataRole.UserRole, field)
#             item.setData(Qt.ItemDataRole.UserRole + 1, material_item)
#
#             # Особые флаги для итоговых колонок
#             if col in (10, 11):
#                 item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
#
#             self.table_estimate.setItem(material_row, col, item)
#
#         # Делаем ячейки работы нередактируемыми в строке материала
#         for col in range(0, 6):
#             if not self.table_estimate.item(material_row, col):
#                 item = QTableWidgetItem("")
#                 item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
#                 self.table_estimate.setItem(material_row, col, item)
#
#     def _find_work_row_for_material(self):
#         """Находит строку работы для добавления материала"""
#         for row in range(self.table_estimate.rowCount()):
#             item = self.table_estimate.item(row, 0)
#             if item and item.data(Qt.ItemDataRole.UserRole) == "work_number":
#                 return row
#         return None
#
#     def _update_work_cell_spans(self, work_row):
#         """Обновляет объединение ячеек для строки работы"""
#         material_count = self.data_handler.works[-1].materials_count()
#         if material_count > 0:
#             for col in range(6):
#                 self.table_estimate.setSpan(
#                     work_row, col,
#                     material_count + 1,  # Работа + материалы
#                     1
#                 )
#
#     def _update_row_numbers(self):
#         """Обновляет нумерацию строк работ"""
#         row_num = 1
#         for row in range(self.table_estimate.rowCount()):
#             item = self.table_estimate.item(row, 0)
#             if item and item.data(Qt.ItemDataRole.UserRole) == "work_number":
#                 item.setText(str(row_num))
#                 row_num += 1
