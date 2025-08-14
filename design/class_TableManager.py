from PyQt6.QtCore import Qt, QPoint, QRectF, QMarginsF
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QTextOption
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem, QTableWidget, QHeaderView

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.classes import MaterialItem, WorkItem, SectionItem
from design.styles import DATA_TABLE_STYLE, RESULT_TABLE_STYLE, ESTIMATE_TABLE_STYLE


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

    def add_row_section(self):
        """Добавляет новую работу с автоматическим объединением"""
        try:
            self.table.setUpdatesEnabled(False)

            insert_pos = self.table.rowCount()

            self.model.add_section()

            self.view.add_section_row()

            self.table.selectRow(insert_pos)

        except Exception as e:
            print(f"Ошибка при добавлении раздела: {e}")
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def add_row_work(self):
        """Добавляет новую работу с автоматическим объединением"""
        try:
            self.table.setUpdatesEnabled(False)

            selected_ranges = self.table.selectedRanges()

            selected_row = selected_ranges[0].topRow()

            self.model.add_work(selected_row + 1)
            self.view.add_work_row(selected_row + 1)
            # self.view.fill_work_row(selected_row + 1)

            self.view.renumber_rows()

            # Обновляем объединения
            # self.view.update_all_spans()
            self.table.selectRow(selected_row + 1)

        except Exception as e:
            print(f"Ошибка при добавлении работы: {e}")
            raise
        finally:
            self.table.setUpdatesEnabled(True)

    def add_row_material(self):
        """Добавляет материал к ВЫДЕЛЕННОЙ работе с объединением"""
        try:
            self.view.table.setUpdatesEnabled(False)

            selected_ranges = self.table.selectedRanges()

            selected_row = selected_ranges[0].topRow()

            # Если нет работ, добавляем новую
            # if not self.model.estimate[section_index].works:
            #     QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для добавления "
            #                                                                 "материала")
            #     return

            # work_idx, work_start_row = self.view.find_selected_work()

            self.model.add_material(selected_row)
            self.view.add_material_row(selected_row)

            self.view.update_spans_for_work(selected_row)

        except Exception as e:
            print(f"Ошибка при добавлении материала: {e}")
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

            selected_row = selected_ranges[0].topRow()

            section_index = self.model.find_section_by_row(selected_row)
            work_idx = self.model.find_work_by_row(selected_row, section_index)

            # work_idx, work_start_row = self.view.find_selected_work()

            if work_idx is None:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбрана ни одна работа для удаления")
                return

            # section_index = self.model.find_section_by_row(work_start_row)

            # Подтверждение удаления
            reply = QMessageBox.question(
                self.page_estimate,
                "Подтверждение",
                f"Вы уверены, что хотите удалить работу '{self.model.estimate[section_index].works[work_idx].name}' и все её материалы?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            self.view.table.setUpdatesEnabled(False)

            self.view.delete_selected_work(selected_row)
            self.model.delete_work(selected_row)

            # self.view.update_all_spans()
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

            section_index = self.model.find_section_by_row(selected_row)

            work_idx = self.model.find_work_by_row(selected_row, section_index)

            # work_idx, work_start_row = self.view.find_selected_work()

            work = self.model.estimate[section_index].works[work_idx]

            if work_idx is None:
                QMessageBox.warning(self.page_estimate, "Предупреждение", "Не выбран ни один материал для удаления")
                return

            # Определяем, выделена ли строка работы (первый материал)
            is_first_material = selected_row == work.row
            section_index = self.model.find_section_by_row(work.row)
            materials_count = self.model.estimate[section_index].works[work_idx].height

            # Если это первый и единственный материал
            if is_first_material and materials_count == 1:
                QMessageBox.warning(self.page_estimate, "Предупреждение",
                                    "Нельзя удалить единственный материал работы. Удалите всю работу.")
                return

            # Определяем индекс материала
            material_idx = selected_row - work.row - (0 if is_first_material else 1)

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

            self.view.delete_selected_material(work.row, selected_row, is_first_material)
            self.model.delete_material(selected_row)
            # self.view.update_spans_for_work(work_idx, work_start_row)

            self.view.update_table_from_model(work.row, 11)
            self.view.update_table_from_model(work.row, 12)
            # self.view_results.update_result_table()

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
            self.view_results.clear_all_data()

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
                        # self.view_results.update_result_table()
                        self.table.resizeRowToContents(row)

            except Exception as e:
                print(f"Ошибка при обновлении данных: {e}")
                QMessageBox.critical(self.page_estimate, "Ошибка", "Не удалось обновить данные")


class TableViewManager:
    def __init__(self, table):
        self.table = table
        self.model = None

        self.setup_table()

        self.add_section_row()

        self.table.selectRow(0)

    def set_model(self, model):
        self.model = model

    def setup_table(self):
        """Настройка таблицы"""
        self.configure_table_appearance()
        self.setup_headers()

    def configure_table_appearance(self):
        """Настраивает внешний вид таблицы"""
        self.table.setStyleSheet(ESTIMATE_TABLE_STYLE)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.EditKeyPressed
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setWordWrap(True)

    def setup_headers(self):
        """Устанавливает заголовки таблицы"""
        headers = [
            "№ п/п", "Наименование работ и затрат", "Ед. изм.", "К-во",
            "Фактический ФОТ на ед., руб", "ФОТ всего, руб", "Наименование материалов",
            "Ед. изм.", "К-во", "Цена, руб", "Сумма, руб", "Сумма по всем материалам", "Всего, руб"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        # self.table.horizontalHeader().setVisible(False)

        self.table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                height: 0;
                padding: 0;
                width: 0;
                border-right: 1px solid #E5E5E5;
                background-color: #FFFFFF;
            }
        """)

        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap)

    def renumber_rows(self):
        """Обновляет нумерацию работ"""
        # for row in range(self.table.rowCount()):
        #     self.table.setItem(row, 0, QTableWidgetItem(""))

        for section in self.model.estimate:
            for work in section.works:
                item = QTableWidgetItem(str(work.number))
                self.table.setItem(work.row, 0, item)

    def add_section_row(self):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        self.table.selectRow(row_pos)

        self.table.setSpan(row_pos, 0, 1, 12)

        self.table.selectRow(row_pos)

    def add_work_row(self, row):
        self.table.insertRow(row)
    #
    #     section_index = self.model.find_section_by_row(row_pos)
    #
    #     self.fill_work_row(row_pos, len(self.model.estimate[section_index].works))
    #
        self.table.selectRow(row)

    def add_material_row(self, row):
        section_index = self.model.find_section_by_row(row)

        work_index = self.model.find_work_by_row(row, section_index)

        work = self.model.estimate[section_index].works[work_index]

        insert_row = work.row + work.height - 1
        self.table.insertRow(insert_row)

        self.table.selectRow(insert_row)

    def clear_all_data(self):
        """Полностью очищает таблицу"""
        self.table.setRowCount(0)
        self.add_section_row()
        self.table.selectRow(0)

    # def update_all_spans(self):
    #     """Обновляем ВСЕ объединения ячеек"""
    #     # Сначала сбрасываем все объединения
    #     for row in range(self.table.rowCount()):
    #         for col in range(6):  # Объединяем только первые 6 колонок
    #             self.table.setSpan(row, col, 1, 1)
    #
    #         self.table.setSpan(row, 11, 1, 1)
    #         self.table.setSpan(row, 12, 1, 1)
    #
    #     # Затем устанавливаем новые объединения
    #     current_row = 0
    #     section_index = self.model.find_section_by_row(current_row)
    #
    #     for work in self.model.estimate[section_index].works:
    #         span_height = work.height
    #
    #         if span_height > 0:  # Объединяем только если есть материалы
    #             for col in range(6):
    #                 self.table.setSpan(current_row, col, span_height, 1)
    #
    #             self.table.setSpan(current_row, 11, span_height, 1)
    #             self.table.setSpan(current_row, 12, span_height, 1)
    #         current_row += span_height

    def update_spans_for_work(self, row):
        """Обновляет объединения ячеек для конкретной работы"""
        section_index = self.model.find_section_by_row(row)

        work_index = self.model.find_work_by_row(row, section_index)

        work = self.model.estimate[section_index].works[work_index]
        span_height = work.height

        # Сбрасываем объединения для этой работы
        for row in range(work.row, work.row + span_height):
            for col in range(6):
                self.table.setSpan(row, col, 1, 1)

            self.table.setSpan(row, 11, 1, 1)
            self.table.setSpan(row, 12, 1, 1)

        # Устанавливаем новые объединения, если есть материалы
        if span_height > 1:
            for col in range(6):
                self.table.setSpan(work.row, col, span_height, 1)
            self.table.setSpan(work.row, 11, span_height, 1)
            self.table.setSpan(work.row, 12, span_height, 1)

    def delete_selected_work(self, row):
        """Удаляет выбранную работу и все её материалы"""
        section_index = self.model.find_section_by_row(row)
        work_idx = self.model.find_work_by_row(row, section_index)

        work = self.model.estimate[section_index].works[work_idx]
        work_height = work.height
        print("\n height,", work_height, "\n")

        for _ in range(work_height):
            self.table.removeRow(work.row)

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

            section_index = self.model.find_section_by_row(row)

            work_index = self.model.find_work_by_row(row, section_index)

            work = self.model.estimate[section_index].works[work_index]

            # total_sum = self.model.total_sum_work_and_materials(work_index)
            # item_col_12 = QTableWidgetItem(str(total_sum))
            # current_col_12 = self.table.item(row, 12).text() if self.table.item(row, 12) else ""

            # if item_col_12.text() != current_col_12:
            #     self.table.setItem(row, 12, item_col_12)

            if col == 3 or col == 4:
                item_col_5 = QTableWidgetItem(str(work.total_work))

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

            elif col == 11:
                item_col_11 = QTableWidgetItem(str(work.total_materials))
                current_col_11 = self.table.item(row, 11).text() if self.table.item(row, 11) else ""

                if item_col_11.text() != current_col_11:
                    self.table.setItem(work.row, 11, item_col_11)

        except Exception as e:
            print(f"Ошибка при обновлении таблицы из модели: {e}")

    def adjust_column_widths(self):
        screen_width = self.table.parent().window().screen().availableGeometry().width()

        table_width = screen_width - 50

        # Устанавливаем фиксированную ширину таблицы
        self.table.setFixedWidth(table_width)

        percents_section = {
            0: 0.035,  # п/п
            1: 0.14,  # Наименование работ
            2: 0.04,  # Ед. изм
            3: 0.07,  # К-во
            4: 0.075,  # ФОТ на ед
            5: 0.075,  # ФОТ всего
            6: 0.14,  # Материалы
            7: 0.04,  # Ед. изм
            8: 0.07,  # К-во
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
        self.table.setStyleSheet(RESULT_TABLE_STYLE)
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

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        headers = [
            "Доставка материала, работа грузчиков, подъем материала, "
            "тарирование мусора, вынос/вывоз мусора (15% от стоимости материалов)",
            "Итого без НДС",
            "В т.ч. ФОТ",
            "В т.ч. Материалы"
        ]
        
        for row, text in enumerate(headers):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, item)

    def adjust_column_widths(self):
        screen_width = self.table.window().screen().availableGeometry().width()

        table_width = screen_width - 50

        # Устанавливаем фиксированную ширину таблицы
        self.table.setFixedWidth(table_width)

        percents_section = {
            0: 0.908,  # п/п
            1: 0.075,  # Наименование работ
        }

        for col, percent in percents_section.items():
            width = int(table_width * percent)
            self.table.setColumnWidth(col, width)

    # def update_result_table(self):
    #     works_sum = sum([work.total_work for work in self.model.works])
    #     materials_sum = sum([work.total_materials for work in self.model.works])
    #     total_sum = works_sum + materials_sum
    #
    #     self.table.setItem(0, 1, QTableWidgetItem(str(round(materials_sum * 0.15, 2))))
    #
    #     self.table.setItem(1, 1, QTableWidgetItem(str(total_sum)))
    #
    #     self.table.setItem(2, 1, QTableWidgetItem(str(works_sum)))
    #
    #     self.table.setItem(3, 1, QTableWidgetItem(str(materials_sum)))

    def clear_all_data(self):
        self.table.setItem(0, 1, QTableWidgetItem(""))

        self.table.setItem(1, 1, QTableWidgetItem(""))

        self.table.setItem(2, 1, QTableWidgetItem(""))

        self.table.setItem(3, 1, QTableWidgetItem(""))


class EstimateDataModel:
    def __init__(self, table):
        self.estimate = [SectionItem()]
        self.table = table

    def add_section(self):
        self.estimate.append(SectionItem())
        self.estimate[-1].row = self.table.rowCount()

    def find_section_by_row(self, row):
        """Находит раздел по номеру строки в таблице"""
        try:
            for i in range(len(self.estimate)):
                if self.estimate[i].row <= row <= self.estimate[i].row + self.estimate[i].height:
                    return i

            return None
        except Exception as e:
            print(f"find_section_by_row Не удалось найти индекс раздела : {e}")

    def find_work_by_row(self, row, section_index):
        """Возвращает индекс работы в массиве по заданной строке"""
        try:
            for i in range(len(self.estimate[section_index].works)):
                work = self.estimate[section_index].works[i]
                if work.row <= row < work.row + work.height:
                    return i

            return None
        except Exception as e:
            print(f"find_work_by_row Не удалось найти индекс работы: {e}")

    def add_work(self, row):
        try:
            section_index = self.find_section_by_row(row - 1)

            work = WorkItem()
            work.row = row
            work.number = row - self.estimate[section_index].row  # Нумерация с 1

            # Вставляем работу в указанную позицию
            self.estimate[section_index].works.insert(work.number - 1, work)

            self.estimate[section_index].height += 1

            # Обновляем позиции последующих работ
            for i in range(work.number, len(self.estimate[section_index].works)):

                # if self.estimate[section_index].works[i].row > row:
                self.estimate[section_index].works[i].number += 1
                self.estimate[section_index].works[i].row += 1

                for k in range(len(self.estimate[section_index].works[i].materials)):
                    self.estimate[section_index].works[i].materials[k].row += 1

            for i in range(section_index + 1, len(self.estimate)):
                self.estimate[i].row += 1

                for j in range(len(self.estimate[i].works)):
                    self.estimate[i].works[j].row += 1

                    for k in range(len(self.estimate[i].works[j].materials)):
                        self.estimate[i].works[j].materials[k].row += 1

        except Exception as e:
            print(f"add_work Не удалось добавить работу (в модель): {e}")

    def add_material(self, row):
        try:
            section_index = self.find_section_by_row(row)

            work_index = self.find_work_by_row(row, section_index)

            self.estimate[section_index].works[work_index].materials.append(MaterialItem())

            self.estimate[section_index].works[work_index].materials[-1].row = row + 1

            self.estimate[section_index].works[work_index].height += 1
            self.estimate[section_index].height += 1

            for i in range(work_index + 1, len(self.estimate[section_index].works)):
                self.estimate[section_index].works[i].row += 1

            for i in range(section_index + 1, len(self.estimate)):
                self.estimate[i].row += 1
                for j in range(len(self.estimate[i].works)):
                    self.estimate[i].works[j].row += 1
                    for k in range(len(self.estimate[i].works[j].materials)):
                        self.estimate[i].works[j].materials[k].row += 1

        except Exception as e:
            print(f"add_material Не удалось добавить материал (в модель): {e}")

    def delete_work(self, row):
        section_index = self.find_section_by_row(row)

        work_index = self.find_work_by_row(row, section_index)

        work_height = self.estimate[section_index].works[work_index].height

        self.estimate[section_index].height -= work_height

        print("\n HEIGHT", work_height, "\n")

        for i in range(work_index + 1, len(self.estimate[section_index].works)):
            self.estimate[section_index].works[i].number -= 1
            self.estimate[section_index].works[i].row -= work_height
            for k in range(len(self.estimate[section_index].works[i].materials)):
                self.estimate[section_index].works[i].materials[k].row -= work_height

        for i in range(section_index + 1, len(self.estimate)):
            self.estimate[i].row -= work_height
            for j in range(len(self.estimate[i].works)):
                self.estimate[i].works[j].row -= work_height
                for k in range(len(self.estimate[i].works[j].materials)):
                    self.estimate[i].works[j].materials[k].row -= work_height

        del self.estimate[section_index].works[work_index]

    def delete_material(self, row):
        section_index = self.find_section_by_row(row)

        work_index = self.find_work_by_row(row, section_index)

        material_index = 0

        for i in range(len(self.estimate[section_index].works[work_index].materials)):
            if self.estimate[section_index].works[work_index].materials[i].row == row:
                material_index = i
                print("hello")

        ###### добавить смещение материалов в той же работе # вроде есть

        for i in range(material_index + 1, len(self.estimate[section_index].works[work_index].materials)):
            self.estimate[section_index].works[work_index].materials[i].row -= 1

        for i in range(work_index + 1, len(self.estimate[section_index].works)):
            self.estimate[section_index].works[i].row -= 1

        for i in range(section_index + 1, len(self.estimate)):
            self.estimate[i].row -= 1
            for j in range(len(self.estimate[i].works)):
                self.estimate[i].works[j].row -= 1
                for k in range(len(self.estimate[i].works[j].materials)):
                    self.estimate[i].works[j].materials[k].row -= 1

        print("material_index", material_index)

        del self.estimate[section_index].works[work_index].materials[material_index]

        self.estimate[section_index].works[work_index].height -= 1
        self.estimate[section_index].height -= 1

        # self.update_total_materials(work_index)

    def clear_all_data(self):
        self.estimate.clear()

        self.estimate.append(SectionItem())

    def update_model_from_table(self, row, col):
        """Обновляет модель на основе изменений в таблице"""
        try:
            section_index = self.find_section_by_row(row)
            # print("section_index", section_index)

            if section_index is None:
                print("section_index is None")
                return

            work_idx = self.find_work_by_row(row, section_index)
            # print("work_idx", work_idx)

            work_start_row = self.estimate[section_index].works[work_idx].row
            # print("work_start_row", work_start_row)

            if work_idx is None:
                print("work_idx is None")
                return

            item = self.table.item(row, col)
            if not item:
                return

            value = item.text()

            # print("value", value)

            if col <= 5 and row == work_start_row:
                if col == 1:  # Наименование работы
                    self.estimate[section_index].works[work_idx].name = value if value else ""
                elif col == 2:  # Ед. изм.
                    self.estimate[section_index].works[work_idx].unit = value if value else ""
                elif col == 3:  # Количество
                    self.estimate[section_index].works[work_idx].quantity = round(float(value), 2) if value else 0.00
                    # self.update_work_total(work_idx)
                elif col == 4:  # ФОТ на ед.
                    self.estimate[section_index].works[work_idx].labor_cost = round(float(value), 2) if value else 0.00
                    # self.update_work_total(work_idx)

            else:
                material_idx = row - work_start_row

                if col == 6:  # Наименование материала
                    self.estimate[section_index].works[work_idx].materials[material_idx].name = value if value else ""
                elif col == 7:  # Ед. изм. материала
                    self.estimate[section_index].works[work_idx].materials[material_idx].unit = value if value else ""
                elif col == 8:  # Количество материала
                    self.estimate[section_index].works[work_idx].materials[material_idx].quantity = round(float(value), 2) if value else 0.00

                    # self.update_material_total(work_idx, material_idx)
                    # self.update_total_materials(work_idx)
                elif col == 9:  # Цена материала
                    self.estimate[section_index].works[work_idx].materials[material_idx].price = round(float(value), 2) if value else 0.00

                    # self.update_material_total(work_idx, material_idx)
                    # self.update_total_materials(work_idx)
        except Exception as e:
            print(f"Ошибка при обновлении модели из таблицы: {e}")

    # def find_work_by_row(self, row):
    #     """Находит работу по номеру строки в таблице"""
    #
    #     for work in self.estimate[section_index].works:
    #         if work.row <= row < work.row + work.height:
    #             return work.number - 1, work.row
    #
    #     return None, None

    # def update_work_total(self, work_idx):
    #     self.estimate[section_index]
    #     .works[work_idx].total_work = round(self.estimate[section_index]
    #     .works[work_idx].quantity * self.works[work_idx].labor_cost, 2)

    # def update_material_total(self, work_idx, material_idx):
    #     material = self.works[work_idx].materials[material_idx]
    #     self.works[work_idx].materials[material_idx].total = round(material.quantity * material.price, 2)

    # def update_total_materials(self, work_idx):
    #     s = 0.0
    #     for i in range(len(self.works[work_idx].materials)):
    #         s += self.works[work_idx].materials[i].total
    #
    #     self.works[work_idx].total_materials = round(s, 2)
    #
    # def total_sum_work_and_materials(self, work_idx):
    #     return round(self.works[work_idx].total_materials + self.works[work_idx].total_work, 2)
