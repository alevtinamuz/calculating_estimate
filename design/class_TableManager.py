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
        self.works = []
        self.current_row_mapping = {}
        self.page_estimate = page_estimate

    def setup_table(self):
        """Настройка таблицы"""
        self.configure_table_appearance()
        self.setup_headers()
        self.setup_delegates()
        self.connect_data_changes()

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

            # self.works[-1].materials.append(MaterialItem())

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
            if span_height > 0:  # Объединяем только если есть материалы
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

    def clear_all_data(self):
        """Полностью очищает таблицу и модель"""
        reply = QMessageBox.question(
            self.page_estimate,
            "Подтверждение",
            "Вы уверены, что хотите полностью очистить таблицу? Все данные будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.table.setUpdatesEnabled(False)

            # Очищаем таблицу
            self.table.setRowCount(0)

            # Очищаем модель
            self.works.clear()
            self.current_row_mapping.clear()

        except Exception as e:
            print(f"Ошибка при очистке таблицы: {e}")
            QMessageBox.critical(self.page_estimate, "Ошибка", "Не удалось очистить таблицу")
        finally:
            self.table.setUpdatesEnabled(True)

    def export_to_pdf(self):
        """Экспортирует таблицу в PDF с заголовком и горизонтальными шапками"""
        try:

            # Диалог выбора файла
            file_path, _ = QFileDialog.getSaveFileName(
                self.page_estimate,
                "Сохранить как PDF",
                "Смета.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Настройка принтера
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setResolution(120)

            # Устанавливаем поля страницы
            layout = QPageLayout()
            layout.setUnits(QPageLayout.Unit.Millimeter)
            layout.setMargins(QMarginsF(15, 20, 15, 15))
            printer.setPageLayout(layout)

            painter = QPainter()
            if not painter.begin(printer):
                raise Exception("Не удалось начать печать")

            self.table.setStyleSheet(DATA_TABLE_STYLE)

            title = "Смета работ и материалов"
            font = QFont("Arial", 14, QFont.Weight.Bold)
            painter.setFont(font)

            # Получаем размеры страницы
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)

            title_rect = QRectF(0, 0, page_rect.width(), 50)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, title)

            self.table.horizontalHeader().setVisible(True)
            table_width = self.table.viewport().width()
            table_height = self.table.viewport().height() + self.table.horizontalHeader().height()

            # Рассчитываем масштаб
            scale = min(
                (page_rect.width() - 40) / table_width,
                (page_rect.height() - title_rect.height() - 40) / table_height
            )

            # Центрируем таблицу
            painter.translate(
                (page_rect.width() - table_width * scale) / 2,
                title_rect.height() + 30
            )
            painter.scale(scale, scale)

            header = self.table.horizontalHeader()
            header.render(painter, QPoint(0, 0))

            painter.translate(0, header.height())
            self.table.viewport().render(painter)

            # Восстанавливаем исходное состояние
            painter.end()
            self.table.setStyleSheet(DATA_TABLE_STYLE)

            QMessageBox.information(
                self.page_estimate,
                "Успех",
                f"PDF успешно сохранен:\n{file_path}"
            )

        except Exception as e:
            # Гарантированно восстанавливаем стили
            self.table.setStyleSheet(DATA_TABLE_STYLE)
            QMessageBox.critical(
                self.page_estimate,
                "Ошибка",
                f"Ошибка при сохранении PDF:\n{str(e)}"
            )

    def update_works(self, work_index, name, unit, quantity, labor_cost):
        work = WorkItem()
        work.name = name
        work.unit = unit
        work.quantity = quantity
        work.labor_cost = labor_cost

        self.works[work_index] = work

    def update_materials(self, work_index, material_index, name, unit, quantity, price):
        material = MaterialItem()
        material.name = name
        material.unit = unit
        material.price = price
        material.quantity = quantity

        self.works[work_index][material_index] = material

    def connect_data_changes(self):
        """Подключает обработчик изменений данных в таблице"""
        self.table.model().dataChanged.connect(self.handle_data_change)

    def handle_data_change(self, top_left, bottom_right, roles):
        """Обрабатывает изменения данных в таблице"""
        if not roles or Qt.ItemDataRole.EditRole in roles:
            for row in range(top_left.row(), bottom_right.row() + 1):
                for col in range(top_left.column(), bottom_right.column() + 1):
                    self.update_model_from_table(row, col)

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

            # Определяем, работа это или материал
            if row == work_start_row:  # Это строка работы
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
            # Это строка материала
            if row == work_start_row:
                material_idx = 0
            else:
                material_idx = row - work_start_row - 1

            if 0 <= material_idx < len(self.works[work_idx].materials):
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

            for i in range(len(self.works)):
                for j in range(len(self.works[i].materials)):
                    print(i, self.works[i].name, j, self.works[i].materials[j].name)

        except Exception as e:
            print(f"Ошибка при обновлении модели из таблицы: {e}")

    def find_work_by_row(self, row):
        """Находит работу по номеру строки в таблице"""
        current_row = 0
        for i, work in enumerate(self.works):
            work_height = len(work.materials) + 1
            if current_row <= row < current_row + work_height:
                return i, current_row
            current_row += work_height
        return None, None