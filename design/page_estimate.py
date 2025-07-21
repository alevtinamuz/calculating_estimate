from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, \
    QPushButton, QMainWindow

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.classes import MaterialItem, WorkItem
from design.styles import LABEL_STYLE, DATA_TABLE_STYLE, PRIMARY_BUTTON_STYLE


class PageEstimate(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        self.supabase = supabase
        self.works = []
        self.table_estimate = None
        self.table_manager = None
        self.main_widget = None
        self.main_layout = None

    def create_page_estimate(self):
        """Создает страницу со сметой"""
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
        """Создает таблицу для подсчета сметы"""
        try:
            estimate_container = QWidget()
            layout = QVBoxLayout(estimate_container)

            # Создаем таблицу как атрибут класса
            self.table_estimate = QTableWidget()

            self.table_manager = EstimateTableManager(self.table_estimate, self.supabase, self)

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
        """Добавляет строку с работой в таблицу"""
        try:
            self.table_manager.add_row_work()

        except Exception as e:
            self.show_error("Не удалось добавить строку работы", str(e))

    def add_row_material(self):
        """Добавляет строку с материалами в таблицу для выбранной работы"""
        try:
            self.table_manager.add_row_material()

        except Exception as e:
            self.show_error("Не удалось добавить строку материалов", str(e))

    def delete_selected_work(self):
        """Удаляет выбранную работу"""
        try:
            self.table_manager.delete_selected_work()
        except Exception as e:
            self.show_error("Не удалось удалить работу", str(e))

    def delete_selected_material(self):
        """Удаляет выбранный материал"""
        try:
            self.table_manager.delete_selected_material()
        except Exception as e:
            self.show_error("Не удалось удалить материал", str(e))

    def create_button_panel(self):
        """Создает кнопки для добавления работ и материалов"""
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)

        add_work_btn = self.create_button("Добавить работу", lambda: self.add_row_work())
        add_material_btn = self.create_button("Добавить материал", lambda: self.add_row_material())
        delete_work_btn = self.create_button("Удалить работу", lambda: self.delete_selected_work())
        delete_material_btn = self.create_button("Удалить материал", lambda: self.delete_selected_material())

        button_layout.addWidget(add_work_btn)
        button_layout.addWidget(add_material_btn)
        button_layout.addWidget(delete_work_btn)
        button_layout.addWidget(delete_material_btn)

        return button_panel

    def create_button(self, text, handler):
        """Создает кнопку"""
        btn = QPushButton(text)
        btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        btn.clicked.connect(handler)

        return btn

    def show_error(self, title, message):
        """Выводит QMessageBox с ошибкой"""
        QMessageBox.critical(self, title, message)


class EstimateTableManager:
    def __init__(self, table_widget, supabase, page_estimate):
        self.table = table_widget
        self.supabase = supabase
        self.works = []
        self.current_row_mapping = {}
        self.page_estimate = page_estimate

    def setup_table(self):
        """Настройка таблицы"""
        self.configure_table_appearance()
        self.setup_headers()
        self.setup_delegates()

    def configure_table_appearance(self):
        """Настраивает внешний вид таблицы"""
        self.table.setStyleSheet(DATA_TABLE_STYLE)
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
        delegate = ComboBoxDelegate(self.table, self.supabase, self.page_estimate)
        self.table.setItemDelegate(delegate)

    def add_row_work(self):
        """Добавляет новую работу с автоматическим объединением"""
        try:
            self.table.setUpdatesEnabled(False)

            # Добавляем работу в модель
            new_work = WorkItem()
            self.works.append(new_work)

            # Вставляем строку
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Заполняем строку работы
            self.fill_work_row(row_pos, len(self.works))

            # Обновляем маппинг и объединения
            self.rebuild_mapping()
            self.update_all_spans()
            self.renumber_works()

            # Выделяем новую работу
            self.table.selectRow(row_pos)

        except Exception as e:
            print(f"Ошибка при добавлении работы: {e}")
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def add_row_material(self):
        """Добавляет материал к ВЫДЕЛЕННОЙ работе с объединением"""
        try:
            self.table.setUpdatesEnabled(False)

            # Если нет работ, добавляем новую
            if not self.works:
                self.add_row_work()
                return

            # Находим выделенную работу
            work_idx, work_start_row = self.find_selected_work()

            # Добавляем материал в модель
            self.works[work_idx].materials.append(MaterialItem())
            materials_count = len(self.works[work_idx].materials)

            # Вставляем строку в правильное место
            insert_row = work_start_row + materials_count
            self.table.insertRow(insert_row)

            # Заполняем строку материала
            self.fill_material_row(insert_row)

            # Обновляем объединения
            self.update_spans_for_work(work_idx, work_start_row)

            # Выделяем новый материал
            self.table.selectRow(insert_row)

        except Exception as e:
            print(f"Ошибка при добавлении материала: {e}")
            # Откатываем изменения в модели при ошибке
            if work_idx is not None and len(self.works[work_idx].materials) > 0:
                self.works[work_idx].materials.pop()
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def delete_selected_work(self):
        """Удаляет выбранную работу и все её материалы"""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для удаления")
            return

        selected_row = selected_ranges[0].topRow()
        work_idx, work_start_row = self.find_selected_work()

        if work_idx is None:
            QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для удаления")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(
            self.page_estimate,
            "Подтверждение",
            f"Вы уверены, что хотите удалить работу '{self.works[work_idx].name}' и все её материалы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.table.setUpdatesEnabled(False)

            # Удаляем строки из таблицы
            work_height = len(self.works[work_idx].materials) + 1
            for _ in range(work_height):
                self.table.removeRow(work_start_row)

            # Удаляем работу из модели
            del self.works[work_idx]

            # Обновляем маппинг, объединения и нумерацию
            self.rebuild_mapping()
            self.update_all_spans()
            self.renumber_works()

        except Exception as e:
            print(f"Ошибка при удалении работы: {e}")
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def delete_selected_material(self):
        """Удаляет выбранный материал"""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбран ни один материал для удаления")
            return

        selected_row = selected_ranges[0].topRow()
        work_idx, work_start_row = self.find_selected_work()

        if work_idx is None:
            QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбран ни один материал для удаления")
            return

        # Определяем, выделена ли строка работы (первый материал)
        is_first_material = selected_row == work_start_row
        materials_count = len(self.works[work_idx].materials)

        # Если это первый и единственный материал
        if is_first_material and materials_count == 1:
            QMessageBox.warning(self.page_estimate, "Предупреждение",
                                "Нельзя удалить единственный материал работы. Удалите всю работу.")
            return

        # Определяем индекс материала
        material_idx = selected_row - work_start_row - (0 if is_first_material else 1)

        # Проверяем, что индекс материала корректен
        if material_idx < 0 or material_idx >= materials_count:
            QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбран ни один материал для удаления")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(
            self.page_estimate,
            "Подтверждение",
            "Вы уверены, что хотите удалить выбранный материал?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.table.setUpdatesEnabled(False)

            if is_first_material:
                # Для первого материала перемещаем следующий материал на место первого
                next_material_row = work_start_row + 1

                # Копируем данные из следующего материала в строку работы
                for col in range(6, self.table.columnCount()):
                    item = self.table.item(next_material_row, col)
                    if item:
                        new_item = QTableWidgetItem(item.text())
                        new_item.setFlags(item.flags())
                        new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
                        self.table.setItem(work_start_row, col, new_item)

                # Удаляем строку следующего материала
                self.table.removeRow(next_material_row)
            else:
                # Для обычных материалов просто удаляем строку
                self.table.removeRow(selected_row)

            # Удаляем материал из модели
            del self.works[work_idx].materials[material_idx]

            # Обновляем объединения для работы
            self.update_spans_for_work(work_idx, work_start_row)

        except Exception as e:
            print(f"Ошибка при удалении материала: {e}")
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def update_spans_for_work(self, work_idx, work_start_row):
        """Обновляет объединения ячеек для конкретной работы"""
        work = self.works[work_idx]
        span_height = len(work.materials) + 1

        # Сбрасываем объединения для этой работы
        for row in range(work_start_row, work_start_row + span_height):
            for col in range(6):
                self.table.setSpan(row, col, 1, 1)

        # Устанавливаем новые объединения, если есть материалы
        if span_height > 1:
            for col in range(6):
                self.table.setSpan(work_start_row, col, span_height, 1)

    def find_selected_work(self):
        """Точное определение выделенной работы с учетом объединенных ячеек"""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return None, None

        selected_row = selected_ranges[0].topRow()

        current_row = 0
        for i, work in enumerate(self.works):
            work_height = len(work.materials) + 1
            if current_row <= selected_row < current_row + work_height:
                return i, current_row
            current_row += work_height

        return None, None

    def update_all_spans(self):
        """Обновляем ВСЕ объединения ячеек"""
        # Сначала сбрасываем все объединения
        for row in range(self.table.rowCount()):
            for col in range(6):  # Объединяем только первые 6 колонок
                self.table.setSpan(row, col, 1, 1)

        # Затем устанавливаем новые объединения
        current_row = 0
        for work in self.works:
            span_height = len(work.materials) + 1
            if span_height > 1:  # Объединяем только если есть материалы
                for col in range(6):
                    self.table.setSpan(current_row, col, span_height, 1)
            current_row += span_height

    def fill_work_row(self, row, number):
        """Заполняет строку работы"""
        # Номер работы
        item = QTableWidgetItem(str(number))
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item.setData(Qt.ItemDataRole.UserRole, "work_number")
        self.table.setItem(row, 0, item)

        # Наименование работы (редактируемое)
        item = QTableWidgetItem("")
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
        item.setData(Qt.ItemDataRole.UserRole, "work_name")
        self.table.setItem(row, 1, item)

        # Остальные ячейки работы
        editable_cols = [2, 3, 4, 5]  # Ед. изм., К-во, ФОТ на ед., ФОТ всего
        for col in editable_cols:
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            item.setData(Qt.ItemDataRole.UserRole, f"work_col_{col}")
            self.table.setItem(row, col, item)

        # Ячейки материалов
        for col in range(6, self.table.columnCount()):
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            item.setData(Qt.ItemDataRole.UserRole, f"material_col_{col}")
            self.table.setItem(row, col, item)

    def fill_material_row(self, row):
        """Заполняет строку материала"""
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            if col >= 6:  # Колонки материалов
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, f"material_col_{col}")
            else:
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, col, item)

    def calculate_work_start_row(self, work_idx):
        """Вычисляет стартовую строку работы"""
        return sum(len(self.works[i].materials) + 1 for i in range(work_idx))

    def rebuild_mapping(self):
        """Обновляет mapping работ и их строк"""
        self.current_row_mapping = {}
        current_row = 0
        for i, work in enumerate(self.works):
            end_row = current_row + len(work.materials)
            self.current_row_mapping[i] = (current_row, end_row)
            current_row = end_row + 1

    def renumber_works(self):
        """Обновляет нумерацию работ"""
        for i, (start_row, _) in self.current_row_mapping.items():
            item = self.table.item(start_row, 0)
            if item:
                item.setText(str(i + 1))
