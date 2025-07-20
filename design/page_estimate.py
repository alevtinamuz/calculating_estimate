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

        # self.create_page_estimate()

    def create_page_estimate(self):
        """Создает вторую страницу (смета)"""
        page_estimate = QWidget()
        layout = QVBoxLayout()

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
            self.table_estimate.setObjectName("estimateTable")

            # Настройки таблицы
            self.table_estimate.setStyleSheet(TABLE_STYLE)
            self.table_estimate.setShowGrid(False)
            self.table_estimate.setEditTriggers(
                QTableWidget.EditTrigger.DoubleClicked |
                QTableWidget.EditTrigger.EditKeyPressed
            )
            self.table_estimate.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table_estimate.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

            # Заголовки
            headers = [
                "№ п/п", "Наименование работ и затрат", "Ед. изм.", "К-во",
                "Фактический ФОТ на ед., руб", "ФОТ всего, руб", "Наименование материалов",
                "Ед. изм.", "К-во", "Цена, руб", "Сумма, руб", "Всего, руб"
            ]
            self.table_estimate.setColumnCount(len(headers))
            self.table_estimate.setHorizontalHeaderLabels(headers)
            self.table_estimate.setRowCount(0)  # Начальная строка

            # Делегат
            delegate = ComboBoxDelegate(self.table_estimate, self.supabase, self)
            self.table_estimate.setItemDelegate(delegate)

            layout.addWidget(self.table_estimate)

            button_layout = QHBoxLayout()

            add_work_button = QPushButton("Добавить работу")
            add_work_button.clicked.connect(lambda: self.add_row_to_estimate(is_work=True))
            add_work_button.setStyleSheet(BUTTON_STYLE)

            add_material_button = QPushButton("Добавить материал")
            add_material_button.clicked.connect(lambda: self.add_row_to_estimate(is_work=False))
            add_material_button.setStyleSheet(BUTTON_STYLE)

            button_layout.addWidget(add_work_button)
            button_layout.addWidget(add_material_button)

            layout.addLayout(button_layout)

            estimate_container.setLayout(layout)

            print("Таблица успешно создана")

            return estimate_container

        except Exception as e:
            print(f"Ошибка создания таблицы: {e}")
            raise

    def add_row_to_estimate(self, is_work=True):
        try:
            # print('до')
            # table = self.findChild(QTableWidget, "estimateTable")
            table = self.table_estimate
            # print(table)
            row_count = table.rowCount()
            table.insertRow(row_count)

            if is_work:
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

                # Устанавливаем делегаты для ячеек работы
                for col in [1, 2, 3, 4, 5]:
                    table.setItem(row_count, col, QTableWidgetItem(""))

                for col in range(table.columnCount()):
                    if not table.item(row_count, col):  # Если ячейка еще не создана
                        item = QTableWidgetItem("")
                        table.setItem(row_count, col, item)

                    # Устанавливаем атрибут для работы
                    item = table.item(row_count, col)
                    item.setData(Qt.ItemDataRole.UserRole, "is_work")
            else:
                # Добавляем материал к последней работе
                if not self.works:
                    self.add_row_to_estimate(is_work=True)
                    return

                self.works[-1].materials.append(MaterialItem())

                # Находим первую строку работы (она могла быть выше)
                work_row = self.find_work_row(row_count)

                # Объединяем ячейки работы вертикально с материалом
                for col in range(6):  # Колонки 0-5
                    table.setSpan(work_row, col, row_count - work_row + 1, 1)  # Объединяем по вертикали

                # Заполняем ячейки материала
                for col in range(6, table.columnCount()):
                    item = QTableWidgetItem("")
                    item.setData(Qt.ItemDataRole.UserRole, "is_material")
                    table.setItem(row_count, col, item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить строку: {str(e)}")

    def find_work_row(self, material_row):
        """Находит строку работы для указанной строки материала"""
        # table = self.findChild(QTableWidget, "estimateTable")
        table = self.table_estimate
        row = material_row - 1
        while row >= 0:
            if table.item(row, 0) and table.item(row, 0).data(Qt.ItemDataRole.UserRole) == "is_work":
                return row
            row -= 1

        return material_row
