from PyQt6.QtCore import Qt, QPoint, QRectF, QMarginsF
from PyQt6.QtGui import QFont, QPainter, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem, QTableWidget, QHeaderView

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.classes import MaterialItem, WorkItem
from design.styles import DATA_TABLE_STYLE


class EstimateTableManager:
    def __init__(self, table_widget, table_results, supabase, page_estimate):
        self.table = table_widget
        self.table_results = table_results
        self.supabase = supabase
        self.page_estimate = page_estimate

        self.model = EstimateDataModel(table_widget)

        self.view = TableViewManager(table_widget)
        self.view.set_model(self.model)

        self.view_results = TableResultsViewManager(table_results)
        self.view_results.set_model(self.model)

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

            selected_ranges = self.table.selectedRanges()
            if not selected_ranges:
                insert_pos = self.table.rowCount()
                work_idx = len(self.model.works)
            else:
                work_idx, work_start_row = self.view.find_selected_work()

                if work_idx is None:
                    insert_pos = self.table.rowCount()
                    work_idx = len(self.model.works)
                else:
                    insert_pos = work_start_row + self.model.works[work_idx].height
                    work_idx += 1

            self.model.add_work_at_position(work_idx, insert_pos)

            self.table.insertRow(insert_pos)
            self.view.fill_work_row(insert_pos, work_idx + 1)

            for i in range(work_idx + 1, len(self.model.works)):
                self.model.works[i].number += 1
                if self.table.item(self.model.works[i].row, 0):
                    self.table.item(self.model.works[i].row, 0).setText(str(self.model.works[i].number))

            # Обновляем объединения
            self.view.update_all_spans()
            self.table.selectRow(insert_pos)

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
            try:
                for row in range(top_left.row(), bottom_right.row() + 1):
                    for col in range(top_left.column(), bottom_right.column() + 1):
                        self.model.update_model_from_table(row, col)
                        self.view.update_table_from_model(row, col)
                        self.view_results.update_result_table()

            except Exception as e:
                print(f"Ошибка при обновлении данных: {e}")
                QMessageBox.critical(self.page_estimate, "Ошибка", "Не удалось обновить данные")


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
        # self.adjust_column_widths()

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
        self.table.verticalHeader().setVisible(False)

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
        materials_count = self.model.works[work_idx].height

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

        for i, work in enumerate(self.model.works):
            if work.row <= selected_row < work.row + work.height:
                return i, work.row

        return None, None

    def clear_all_data(self):
        """Полностью очищает таблицу"""
        self.table.setRowCount(0)

    def update_all_spans(self):
        """Обновляем ВСЕ объединения ячеек"""
        # Сначала сбрасываем все объединения
        for row in range(self.table.rowCount()):
            for col in range(6):  # Объединяем только первые 6 колонок
                self.table.setSpan(row, col, 1, 1)

            self.table.setSpan(row, 11, 1, 1)
            self.table.setSpan(row, 12, 1, 1)

        # Затем устанавливаем новые объединения
        current_row = 0
        for work in self.model.works:
            span_height = work.height

            if span_height > 0:  # Объединяем только если есть материалы
                for col in range(6):
                    self.table.setSpan(current_row, col, span_height, 1)

                self.table.setSpan(current_row, 11, span_height, 1)
                self.table.setSpan(current_row, 12, span_height, 1)
            current_row += span_height

    def update_spans_for_work(self, work_idx, work_start_row):
        """Обновляет объединения ячеек для конкретной работы"""
        work = self.model.works[work_idx]
        span_height = work.height

        # Сбрасываем объединения для этой работы
        for row in range(work_start_row, work_start_row + span_height):
            for col in range(6):
                self.table.setSpan(row, col, 1, 1)

            self.table.setSpan(row, 11, 1, 1)
            self.table.setSpan(row, 12, 1, 1)

        # Устанавливаем новые объединения, если есть материалы
        if span_height > 1:
            for col in range(6):
                self.table.setSpan(work_start_row, col, span_height, 1)
            self.table.setSpan(work_start_row, 11, span_height, 1)
            self.table.setSpan(work_start_row, 12, span_height, 1)

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

    def update_table_from_model(self, row, col):
        try:
            work_index, _ = self.model.find_work_by_row(row)

            work = self.model.works[work_index]

            total_sum = self.model.total_sum_work_and_materials(work_index)
            item_col_12 = QTableWidgetItem(str(total_sum))
            current_col_12 = self.table.item(row, 12).text() if self.table.item(row, 12) else ""

            if item_col_12.text() != current_col_12:
                self.table.setItem(row, 12, item_col_12)

            if col == 3 or col == 4:
                item_col_5 = QTableWidgetItem(str(work.total))

                current_col_5 = self.table.item(row, 5).text() if self.table.item(row, 5) else ""
                if item_col_5.text() != current_col_5:
                    self.table.setItem(row, 5, item_col_5)

            elif col == 8 or col == 9:
                material_total = work.materials[row - work.row].total
                item_col_10 = QTableWidgetItem(str(material_total))
                current_col_10 = self.table.item(row, 10).text() if self.table.item(row, 10) else ""

                if item_col_10.text() != current_col_10:
                    self.table.setItem(row, 10, item_col_10)

                item_col_11 = QTableWidgetItem(str(work.total_materials))
                current_col_11 = self.table.item(row, 11).text() if self.table.item(row, 11) else ""

                if item_col_11.text() != current_col_11:
                    self.table.setItem(work.row, 11, item_col_11)

        except Exception as e:
            print(f"Ошибка при обновлении таблицы из модели: {e}")

    def adjust_column_widths(self):
        screen_width = self.table.parent().window().screen().availableGeometry().width()

        table_width = screen_width - 30

        # Устанавливаем фиксированную ширину таблицы
        self.table.setFixedWidth(table_width)

        percents_section = {
            0: 0.035,  # п/п
            1: 0.14,  # Наименование работ
            2: 0.04,  # Ед. изм
            3: 0.05,  # К-во
            4: 0.075,  # ФОТ на ед
            5: 0.075,  # ФОТ всего
            6: 0.14,  # Материалы
            7: 0.04,  # Ед. изм
            8: 0.05,  # К-во
            9: 0.075,  # Цена
            10: 0.075,  # Сумма
            11: 0.075,  # Сумма по материалам
            12: 0.075  # Всего
        }

        for col, percent in percents_section.items():
            width = int(table_width * percent)
            self.table.setColumnWidth(col, width)


class TableResultsViewManager:
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
        self.table.setColumnCount(2)
        self.table.setRowCount(4)

        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)

        self.table.setItem(0, 0, QTableWidgetItem("Доставка материала, работа грузчиков, подьем материала, "
                                                  "тарирование мусора, вынос/вывоз мусора (15% от стоимости "
                                                  "материалов)"))
        self.table.setItem(1, 0, QTableWidgetItem("Итого без НДС"))
        self.table.setItem(2, 0, QTableWidgetItem("В т.ч. ФОТ"))
        self.table.setItem(3, 0, QTableWidgetItem("В т.ч. Материалы"))

    def adjust_column_widths(self):
        screen_width = self.table.window().screen().availableGeometry().width()

        table_width = screen_width - 30

        # Устанавливаем фиксированную ширину таблицы
        self.table.setFixedWidth(table_width)

        percents_section = {
            0: 0.865,  # п/п
            1: 0.075,  # Наименование работ
        }

        for col, percent in percents_section.items():
            width = int(table_width * percent)
            self.table.setColumnWidth(col, width)

    def update_result_table(self):
        works_sum = sum([work.total for work in self.model.works])
        materials_sum = sum([work.total_materials for work in self.model.works])
        total_sum = works_sum + materials_sum

        self.table.setItem(0, 1, QTableWidgetItem(str(round(materials_sum * 0.15, 2))))

        self.table.setItem(1, 1, QTableWidgetItem(str(total_sum)))

        self.table.setItem(2, 1, QTableWidgetItem(str(works_sum)))

        self.table.setItem(3, 1, QTableWidgetItem(str(materials_sum)))


class EstimateDataModel:
    def __init__(self, table):
        self.works = []
        self.table = table

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

    def add_work_at_position(self, work_index, row_position):
        """Добавляет работу в указанную позицию"""
        work = WorkItem()
        work.row = row_position
        work.number = work_index + 1  # Нумерация с 1

        # Вставляем работу в указанную позицию
        self.works.insert(work_index, work)

        # Обновляем позиции последующих работ
        for i in range(work_index + 1, len(self.works)):
            self.works[i].row += 1

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

            if col <= 5 and row == work_start_row:
                if col == 1:  # Наименование работы
                    self.works[work_idx].name = value if value else ""
                elif col == 2:  # Ед. изм.
                    self.works[work_idx].unit = value if value else ""
                elif col == 3:  # Количество
                    self.works[work_idx].quantity = round(float(value), 1) if value else 0.0
                    self.update_work_total(work_idx)
                elif col == 4:  # ФОТ на ед.
                    self.works[work_idx].labor_cost = round(float(value), 1) if value else 0.0
                    self.update_work_total(work_idx)

            else:
                material_idx = row - work_start_row

                if col == 6:  # Наименование материала
                    self.works[work_idx].materials[material_idx].name = value if value else ""
                elif col == 7:  # Ед. изм. материала
                    self.works[work_idx].materials[material_idx].unit = value if value else ""
                elif col == 8:  # Количество материала
                    self.works[work_idx].materials[material_idx].quantity = round(float(value), 1) if value else 0.0

                    self.update_material_total(work_idx, material_idx)
                elif col == 9:  # Цена материала
                    self.works[work_idx].materials[material_idx].price = round(float(value), 1) if value else 0.0

                    self.update_material_total(work_idx, material_idx)
        except Exception as e:
            print(f"Ошибка при обновлении модели из таблицы: {e}")

    def find_work_by_row(self, row):
        """Находит работу по номеру строки в таблице"""

        for work in self.works:
            if work.row <= row < work.row + work.height:
                return work.number - 1, work.row

        return None, None

    def update_work_total(self, work_idx):
        self.works[work_idx].total = round(self.works[work_idx].quantity * self.works[work_idx].labor_cost, 1)

    def update_material_total(self, work_idx, material_idx):
        material = self.works[work_idx].materials[material_idx]
        self.works[work_idx].materials[material_idx].total = round(material.quantity * material.price, 1)

        s = 0.0
        for i in range(len(self.works[work_idx].materials)):
            s += self.works[work_idx].materials[i].total

        self.works[work_idx].total_materials = round(s, 1)

    def total_sum_work_and_materials(self, work_idx):
        return round(self.works[work_idx].total_materials + self.works[work_idx].total, 1)
