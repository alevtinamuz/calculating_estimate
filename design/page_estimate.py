from PyQt6.QtCore import Qt, QMarginsF, QPoint, QRectF
from PyQt6.QtGui import QPageSize, QPainter, QPageLayout, QFont, QPen
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, \
    QPushButton, QMainWindow, QFileDialog
    
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from design.class_ComboBoxDelegate import ComboBoxDelegate
from design.class_TableManager import EstimateTableManager, EstimateDataModel
from design.classes import MaterialItem, WorkItem
from design.styles import LABEL_STYLE, DATA_TABLE_STYLE, PRIMARY_BUTTON_STYLE, MESSAGE_BOX_STYLE

from datetime import datetime

class PageEstimate(QMainWindow):
    def __init__(self, supabase):
        super().__init__()
        self.supabase = supabase
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

        page_estimate.setStyleSheet(MESSAGE_BOX_STYLE)

        return page_estimate

    def create_table_estimate(self):
        """Создает таблицу для подсчета сметы"""
        try:
            estimate_container = QWidget()
            layout = QVBoxLayout(estimate_container)

            # Создаем таблицу как атрибут класса
            self.table_estimate = QTableWidget()

            self.table_manager = EstimateTableManager(self.table_estimate, self.supabase, self)

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

    def clear_table(self):
        """Обработчик очистки таблицы"""
        try:
            self.table_manager.clear_all_data()
        except Exception as e:
            self.show_error("Ошибка очистки таблицы", str(e))

    def create_button_panel(self):
        """Создает кнопки для добавления работ и материалов"""
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)

        add_work_btn = self.create_button("Добавить работу", lambda: self.add_row_work())
        add_material_btn = self.create_button("Добавить материал", lambda: self.add_row_material())
        delete_work_btn = self.create_button("Удалить работу", lambda: self.delete_selected_work())
        delete_material_btn = self.create_button("Удалить материал", lambda: self.delete_selected_material())
        clear_table_btn = self.create_button("Очистить таблицу", lambda: self.clear_table())
        export_pdf_btn = self.create_button("Экспорт в PDF", lambda: self.export_to_pdf())

        button_layout.addWidget(add_work_btn)
        button_layout.addWidget(add_material_btn)
        button_layout.addWidget(delete_work_btn)
        button_layout.addWidget(delete_material_btn)
        button_layout.addWidget(clear_table_btn)
        button_layout.addWidget(export_pdf_btn)

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
        
    def safe_format_float(self, value, default="0.0"):
        try:
            return f"{float(str(value).replace(',', '.')):.1f}" if value else default
        except (ValueError, TypeError):
            return default
                
    def safe_str(self, value, default=""):
        return str(value).strip() if value else default   
            
    def export_to_pdf(self):
        """Экспортирует таблицу в PDF с использованием reportlab"""
        try:
            # Настройка документа
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как PDF", f"Смета_{current_date}.pdf", "PDF Files (*.pdf)"
            )
            if not file_path:
                return

            # Создаем документ PDF
            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(A4),
                leftMargin=5*mm,
                rightMargin=5*mm,
                topMargin=5*mm,
                bottomMargin=5*mm
            )

            # Регистрируем шрифты
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
            except:
                pass

            # Стили текста
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontName='Arial-Bold',
                fontSize=16,
                alignment=0,
                spaceAfter=5
            )
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Heading2'],
                fontName='Arial',
                fontSize=12,
                alignment=0,
                spaceAfter=10
            )
            table_header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontName='Arial-Bold',
                fontSize=8,
                alignment=1,
                leading=10
            )
            table_text_style = ParagraphStyle(
                'TableText',
                parent=styles['Normal'],
                fontName='Arial',
                fontSize=8,
                leading=10,
                wordWrap='LTR'
            )

            # Содержимое документа
            elements = []
            elements.append(Paragraph("Стоимость работ", title_style))

            # Подготовка данных таблицы
            headers = [
                "№", "Работы", "Ед.изм.", "Кол-во", 
                "ФОТ/ед.", "ФОТ", "Материалы", "Ед.изм.", 
                "Кол-во", "Цена", "Сумма", "Всего"
            ]
            data = [headers]

            # Ширины столбцов
            col_widths = [
                10*mm, 56*mm, 15*mm, 15*mm,
                20*mm, 20*mm, 56*mm, 15*mm,
                15*mm, 20*mm, 20*mm, 20*mm
            ]
            
            work_start_rows = {}

            for work_idx, work in enumerate(self.table_manager.model.works, 1):

                work_row = [
                    str(work_idx),
                    self.safe_str(work.name, "-"),
                    self.safe_str(work.unit, "-"),
                    self.safe_str(work.quantity, ""),
                    self.safe_format_float(work.labor_cost, "0.0"),
                    self.safe_format_float(work.total, "0.0"),
                ]
                
                if work.materials:
                    first_material = work.materials[0]
                    total_sum = self.table_manager.model.total_sum_work_and_materials(work_idx - 1)
                    
                    work_row.extend([
                        self.safe_str(first_material.name, "-"),
                        self.safe_str(first_material.unit, "-"),
                        self.safe_str(first_material.quantity, ""),
                        self.safe_format_float(first_material.price, "0.0"),
                        self.safe_format_float(work.total_materials, "0.0"),
                        self.safe_format_float(total_sum, "0.0")
                    ])
                    
                    data.append(work_row)
                    work_start_rows[work_idx] = len(data) - 1
                    
                    for material in work.materials[1:]:                     
                        material_row = [
                            "", "", "", "", "", "",
                            self.safe_str(material.name, "-"),
                            self.safe_str(material.unit, "-"),
                            self.safe_str(material.quantity, ""),
                            self.safe_format_float(material.price, "0.0"),
                            self.safe_format_float(work.total_materials, "0.0"),
                            ""
                        ]
                        data.append(material_row)
                else:
                    data.append(work_row)
                    work_start_rows[work_idx] = len(data) - 1
                    
            # Преобразуем данные в Paragraph
            table_data = []
            for i, row in enumerate(data):
                if i == 0:  # Заголовки
                    table_data.append([Paragraph(cell, table_header_style) for cell in row])
                else:
                    table_data.append([Paragraph(cell, table_text_style) for cell in row])

            # Создаем таблицу
            table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # Настройка стиля таблицы
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (6, 0), (6, -1), 'LEFT'),
                ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (1, 0), (1, -1), True),
                ('WORDWRAP', (6, 0), (6, -1), True),
            ]
            
            for work_idx, start_row in work_start_rows.items():
                work = self.table_manager.model.works[work_idx - 1]
                
                end_row = start_row
                if work.materials:
                    end_row = start_row + len(work.materials) - 1
                
                if end_row > start_row: 
                    for col in [0, 1, 2, 3, 4, 5, 10, 11]: 
                        table_style.append(('SPAN', (col, start_row), (col, end_row)))
                        
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            elements.append(Spacer(1, 10*mm))

            # Генерация PDF
            doc.build(elements)
            QMessageBox.information(self, "Успех", f"PDF успешно сохранен:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении PDF:\n{str(e)}")