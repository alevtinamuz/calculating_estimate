from PyQt6.QtCore import Qt, QPoint, QRectF, QMarginsF
from PyQt6.QtGui import QFont, QPainter, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem, QTableWidget

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.classes import MaterialItem, WorkItem
from design.styles import DATA_TABLE_STYLE


class EstimateTableManager:
    def __init__(self, table_widget, supabase, page_estimate):
        self.table = table_widget
        self.supabase = supabase
        self.page_estimate = page_estimate

        self.model = EstimateDataModel(table_widget)

        self.view = TableViewManager(table_widget)
        self.view.set_model(self.model)

        self.setup_table()

    def setup_table(self):
        """Настройка таблицы"""
        self.setup_delegates()
        self.connect_data_changes()

    def setup_delegates(self):
        """Устанавливает делегаты, кем бы они ни были"""
        delegate = ComboBoxDelegate(self.table, self.supabase, self.page_estimate)
        self.table.setItemDelegate(delegate)

    def add_row_work(self):
        """Добавляет новую работу с автоматическим объединением"""
        try:
            self.table.setUpdatesEnabled(False)

            self.model.add_work()
            self.view.add_work_row()

            self.view.update_all_spans()
            self.view.renumber_rows()

        except Exception as e:
            print(f"Ошибка при добавлении работы: {e}")
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def add_row_material(self):
        """Добавляет материал к ВЫДЕЛЕННОЙ работе с объединением"""
        try:
            self.view.table.setUpdatesEnabled(False)

            # Если нет работ, добавляем новую
            if not self.model.works:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для добавления "
                                                                        "материала")
                return

            work_idx, work_start_row = self.view.find_selected_work()

            self.model.add_material(work_idx)
            self.view.add_material_row(work_idx, work_start_row)

            self.view.update_spans_for_work(work_idx, work_start_row)

        except Exception as e:
            print(f"Ошибка при добавлении материала: {e}")
            # Откатываем изменения в модели при ошибке
            raise
        finally:
            self.view.table.setUpdatesEnabled(True)

    def delete_selected_work(self):
        """Удаляет выбранную работу и все её материалы"""
        try:
            selected_ranges = self.table.selectedRanges()

            if not selected_ranges:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для удаления")
                return

            work_idx, work_start_row = self.view.find_selected_work()

            if work_idx is None:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для удаления")
                return

            # Подтверждение удаления
            reply = QMessageBox.question(
                self.page_estimate,
                "Подтверждение",
                f"Вы уверены, что хотите удалить работу '{self.model.works[work_idx].name}' и все её материалы?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            self.view.table.setUpdatesEnabled(False)

            self.view.delete_selected_work(work_idx, work_start_row)
            self.model.delete_work(work_idx)

            self.view.update_all_spans()
            self.view.renumber_rows()

        except Exception as e:
            print(f"Ошибка при удалении работы: {e}")
            raise
        finally:
            self.view.table.setUpdatesEnabled(True)

    def delete_selected_material(self):
        """Удаляет выбранный материал"""
        try:
            selected_ranges = self.view.table.selectedRanges()
            if not selected_ranges:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбран ни один материал для удаления")
                return

            selected_row = selected_ranges[0].topRow()
            work_idx, work_start_row = self.view.find_selected_work()

            if work_idx is None:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбран ни один материал для удаления")
                return

            # Определяем, выделена ли строка работы (первый материал)
            is_first_material = selected_row == work_start_row
            materials_count = self.model.works[work_idx].height

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

            self.view.table.setUpdatesEnabled(False)

            self.view.delete_selected_material(work_start_row, selected_row, is_first_material)
            self.model.delete_material(work_idx, material_idx)
            self.view.update_spans_for_work(work_idx, work_start_row)

        except Exception as e:
            print(f"Ошибка при удалении материала: {e}")
            raise

        finally:
            self.view.table.setUpdatesEnabled(True)

    def clear_all_data(self):
        """Полностью очищает таблицу и модель"""
        try:
            reply = QMessageBox.question(
                self.page_estimate,
                "Подтверждение",
                "Вы уверены, что хотите полностью очистить таблицу? Все данные будут удалены.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            self.view.clear_all_data()
            self.model.clear_all_data()

        except Exception as e:
            print(f"Ошибка при очистке таблицы: {e}")
            QMessageBox.critical(self.page_estimate, "Ошибка", "Не удалось очистить таблицу")

    def connect_data_changes(self):
        """Подключает обработчик изменений данных в таблице"""
        self.view.table.model().dataChanged.connect(self.handle_data_change)

    def handle_data_change(self, top_left, bottom_right, roles):
        """Обрабатывает изменения данных в таблице"""
        if not roles or Qt.ItemDataRole.EditRole in roles:
            for row in range(top_left.row(), bottom_right.row() + 1):
                for col in range(top_left.column(), bottom_right.column() + 1):
                    self.model.update_model_from_table(row, col)


class TableViewManager:
    def __init__(self, table):
        self.table = table
        self.model = None

        self.setup_table()

    def set_model(self, model):
        self.model = model

    def setup_table(self):
        """Настройка таблицы"""
        self.configure_table_appearance()
        self.setup_headers()

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
            "Ед. изм.", "К-во", "Цена, руб", "Сумма, руб", "Сумма по всем материалам", "Всего, руб"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

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
        # item.setData(Qt.ItemDataRole.UserRole, "work_name")
        self.table.setItem(row, 1, item)

        # Остальные ячейки работы
        editable_cols = [2, 3, 4, 5]  # Ед. изм., К-во, ФОТ на ед., ФОТ всего
        for col in editable_cols:
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            item.setData(Qt.ItemDataRole.UserRole, f"work_col_{col}")
            self.table.setItem(row, col, item)

    def fill_material_row(self, row):
        """Заполняет строку материала"""
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            if col >= 6:  # Колонки материалов
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, f"material_col_{col}")

            self.table.setItem(row, col, item)

    def renumber_rows(self):
        """Обновляет нумерацию работ"""
        for work in self.model.works:
            item = self.table.item(work.row, 0)
            if item:
                item.setText(str(work.number))

    def add_work_row(self):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)

        self.fill_work_row(row_pos, len(self.model.works))

        self.table.selectRow(row_pos)

    def add_material_row(self, work_idx, work_start_row):
        materials_count = len(self.model.works[work_idx].materials)
        print(materials_count, "now_height")
        materials_count = self.model.works[work_idx].height
        print(materials_count, "true_height")

        insert_row = work_start_row + materials_count - 1
        self.table.insertRow(insert_row)

        self.fill_material_row(insert_row)

        self.table.selectRow(insert_row)

    def find_selected_work(self):
        """Точное определение выделенной работы с учетом объединенных ячеек"""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return None, None

        selected_row = selected_ranges[0].topRow()

        return self.model.find_work_by_row(selected_row)

    def clear_all_data(self):
        """Полностью очищает таблицу"""
        self.table.setRowCount(0)

    def update_all_spans(self):
        """Обновляем ВСЕ объединения ячеек"""
        # Сначала сбрасываем все объединения
        for row in range(self.table.rowCount()):
            for col in range(6):  # Объединяем только первые 6 колонок
                self.table.setSpan(row, col, 1, 1)

        # Затем устанавливаем новые объединения
        current_row = 0
        for work in self.model.works:
            span_height = work.height

            if span_height > 0:  # Объединяем только если есть материалы
                for col in range(6):
                    self.table.setSpan(current_row, col, span_height, 1)
            current_row += span_height

    def update_spans_for_work(self, work_idx, work_start_row):
        """Обновляет объединения ячеек для конкретной работы"""
        work = self.model.works[work_idx]
        span_height = work.height

        # Сбрасываем объединения для этой работы
        for row in range(work_start_row, work_start_row + span_height):
            for col in range(6):
                self.table.setSpan(row, col, 1, 1)

        # Устанавливаем новые объединения, если есть материалы
        if span_height > 1:
            for col in range(6):
                self.table.setSpan(work_start_row, col, span_height, 1)

    def delete_selected_work(self, work_idx, work_start_row):
        """Удаляет выбранную работу и все её материалы"""
        work_height = self.model.works[work_idx].height
        for _ in range(work_height):
            self.table.removeRow(work_start_row)

    def delete_selected_material(self, work_start_row, selected_row, is_first_material):
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


class EstimateDataModel:
    def __init__(self, table):
        self.works = []
        self.table = table

    def update_work(self, work_index, name, unit, quantity, labor_cost):
        work = WorkItem()
        work.name = name
        work.unit = unit
        work.quantity = quantity
        work.labor_cost = labor_cost

        self.works[work_index] = work

    def update_material(self, work_index, material_index, name, unit, quantity, price):
        material = MaterialItem()
        material.name = name
        material.unit = unit
        material.price = price
        material.quantity = quantity

        self.works[work_index][material_index] = material

    def add_work(self):
        work = WorkItem()
        self.works.append(work)
        self.works[-1].row = self.table.rowCount()
        self.works[-1].number = len(self.works)

    def add_material(self, work_index):
        material = MaterialItem()
        self.works[work_index].materials.append(material)

        self.works[work_index].height += 1

        for i in range(work_index + 1, len(self.works)):
            self.works[i].row += 1

    def delete_work(self, work_index):
        work_height = self.works[work_index].height

        for i in range(work_index + 1, len(self.works)):
            self.works[i].row -= work_height
            self.works[i].number -= 1

        del self.works[work_index]

    def delete_material(self, work_index, material_index):
        for i in range(work_index + 1, len(self.works)):
            self.works[i].row -= 1

        del self.works[work_index].materials[material_index]

        self.works[work_index].height -= 1

    def clear_all_data(self):
        self.works.clear()

    def update_model_from_table(self, row, col):
        """Обновляет модель на основе изменений в таблице"""
        try:
            # Находим соответствующую работу и материал
            work_idx, work_start_row = self.find_work_by_row(row)
            if work_idx is None:
                return

            item = self.table.item(row, col)
            if not item:
                return

            value = item.text()
            user_data = item.data(Qt.ItemDataRole.UserRole)

            if col <= 5:
                if col == 1:  # Наименование работы
                    self.works[work_idx].name = value
                elif col == 2:  # Ед. изм.
                    self.works[work_idx].unit = value
                elif col == 3:  # Количество
                    self.works[work_idx].quantity = value
                elif col == 4:  # ФОТ на ед.
                    self.works[work_idx].labor_cost = value
                elif col == 5:  # ФОТ всего
                    pass  # Это вычисляемое поле, не сохраняем
            else:
                material_idx = row - work_start_row

                if col == 6:  # Наименование материала
                    self.works[work_idx].materials[material_idx].name = value
                elif col == 7:  # Ед. изм. материала
                    self.works[work_idx].materials[material_idx].unit = value
                elif col == 8:  # Количество материала
                    self.works[work_idx].materials[material_idx].quantity = value
                elif col == 9:  # Цена материала
                    self.works[work_idx].materials[material_idx].price = value
                elif col == 10:  # Сумма материала
                    pass  # Это вычисляемое поле, не сохраняем

            # for i in range(len(self.works)):
            #     for j in range(self.works[i].height):
            #         print(i, self.works[i].name, j, self.works[i].materials[j].name)

        except Exception as e:
            print(f"Ошибка при обновлении модели из таблицы: {e}")

    def find_work_by_row(self, row):
        """Находит работу по номеру строки в таблице"""

        for work in self.works:
            if work.row <= row < work.row + work.height:
                return work.number - 1, work.row

        return None, None
