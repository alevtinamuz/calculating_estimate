from PyQt6.QtCore import Qt, QMarginsF, QPoint, QRectF
from PyQt6.QtGui import QPageSize, QPainter, QPageLayout, QFont, QPen
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, \
    QPushButton, QMainWindow, QFileDialog, QSizePolicy
import webbrowser

import os

from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Image, LongTable
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

            self.table_estimate = QTableWidget()
            self.table_results = QTableWidget()
            self.table_manager = EstimateTableManager(self.table_estimate, self.table_results, self.supabase, self)

            layout.addWidget(self.table_estimate, stretch=20)
            layout.addWidget(self.table_results, stretch=7)

            self.table_manager.view.adjust_column_widths()
            self.table_manager.view_results.adjust_column_widths()

            button_panel = self.create_button_panel()
            layout.addWidget(button_panel, stretch=1)

            estimate_container.setLayout(layout)

            print("Таблица успешно создана")

            return estimate_container

        except Exception as e:
            self.show_error("Ошибка создания таблицы", str(e))
            print(f"Ошибка создания таблицы: {e}")
            raise

    def add_row_section(self):
        """Добавляет строку с работой в таблицу"""
        try:
            self.table_manager.add_row_section()

        except Exception as e:
            self.show_error("Не удалось добавить строку работы", str(e))

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

        add_section_btn = self.create_button("Добавить раздел", lambda: self.add_row_section())
        add_work_btn = self.create_button("Добавить работу", lambda: self.add_row_work())
        add_material_btn = self.create_button("Добавить материал", lambda: self.add_row_material())
        delete_work_btn = self.create_button("Удалить работу", lambda: self.delete_selected_work())
        delete_material_btn = self.create_button("Удалить материал", lambda: self.delete_selected_material())
        clear_table_btn = self.create_button("Очистить таблицу", lambda: self.clear_table())
        export_pdf_btn = self.create_button("Экспорт в PDF", lambda: self.export_to_pdf())

        button_layout.addWidget(add_section_btn)
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
                leftMargin=5 * mm,
                rightMargin=5 * mm,
                topMargin=5 * mm,
                bottomMargin=5 * mm
            )

            # Регистрируем шрифты
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-BoldItalic', 'arialbi.ttf'))
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
                alignment=TA_CENTER,
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
            summary_text_style = ParagraphStyle(
                'SummaryText',
                parent=styles['Normal'],
                fontName='Arial-BoldItalic',
                alignment=2,
                fontSize=8,
                leading=10
            )
            summary_value_style = ParagraphStyle(
                'SummaryValue',
                parent=styles['Normal'],
                fontName='Arial-BoldItalic',
                alignment=1,
                fontSize=8,
                leading=10
            )
            summary_title_style = ParagraphStyle(
                'SummaryTitle',
                parent=styles['Normal'],
                fontName='Arial-Bold',
                alignment=1,
                fontSize=8,
                leading=10
            )

            # Содержимое документа
            elements = []
            try:
                # Используем os.path для формирования пути к логотипу
                logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
                if os.path.exists(logo_path):
                    # Создаем таблицу с двумя колонками для логотипа и заголовка
                    logo_table_data = [
                        [Image(logo_path, width=100, height=100), Paragraph("Стоимость работ", title_style)]
                    ]
                    logo_table = Table(logo_table_data, colWidths=[100, doc.width - 100])
                    logo_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ]))
                    elements.append(logo_table)
                else:
                    elements.append(Paragraph("Стоимость работ", title_style))
                    print("Логотип не найден по пути:", logo_path)
            except Exception as logo_error:
                elements.append(Paragraph("Стоимость работ", title_style))
                print(f"Не удалось загрузить логотип: {logo_error}")

            # Подготовка данных таблицы
            headers = [
                "№ п/п", "Наименование работ и затрат", "Ед.изм.", "К-во",
                "Фактический ФОТ", "Фактический ФОТ", "Наименование материалов", "Ед.изм.",
                "", "", "", "Всего"
            ]

            fot_labels = [
                "", "", "", "",
                "на ед.", "всего", "", "",
                "К-во", "Цена", "Сумма", ""
            ]

            data = [headers, fot_labels]
            data_summary = []

            # Ширины столбцов
            col_widths = [
                10 * mm, 53 * mm, 15 * mm, 15 * mm,
                21 * mm, 21 * mm, 53 * mm, 15 * mm,
                15 * mm, 21 * mm, 21 * mm, 22 * mm
            ]

            work_start_rows = {}
            section_start_rows = {}

            for section_idx, section in enumerate(self.table_manager.model.estimate, 1):
                # Добавляем строку с разделом
                section_row = [Paragraph(section.name, table_header_style)] + [Paragraph("", table_text_style) for _ in range(len(headers) - 1)]
                data.append(section_row)
                section_start_rows[section_idx] = len(data) - 1

                for work_idx, work in enumerate(section.works, 1):
                    work_row = [
                        Paragraph(str(work_idx), table_text_style),
                        Paragraph(self.safe_str(work.name, "-"), table_text_style),
                        Paragraph(self.safe_str(work.unit, "-"), table_text_style),
                        Paragraph(self.safe_str(work.quantity, ""), table_text_style),
                        Paragraph(self.safe_format_float(work.labor_cost, "0.0"), table_text_style),
                        Paragraph(self.safe_format_float(work.total_work, "0.0"), table_text_style),
                    ]

                    if work.materials:
                        first_material = work.materials[0]
                        total_sum = self.table_manager.model.total_sum_work_and_materials(section_idx - 1, work_idx - 1)

                        work_row.extend([
                            Paragraph(self.safe_str(first_material.name, "-"), table_text_style),
                            Paragraph(self.safe_str(first_material.unit, "-"), table_text_style),
                            Paragraph(self.safe_str(first_material.quantity, ""), table_text_style),
                            Paragraph(self.safe_format_float(first_material.price, "0.0"), table_text_style),
                            Paragraph(self.safe_format_float(work.total_materials, "0.0"), table_text_style),
                            Paragraph(self.safe_format_float(total_sum, "0.0"), table_text_style)
                        ])

                        data.append(work_row)
                        work_start_rows[(section_idx, work_idx)] = len(data) - 1

                        for material in work.materials[1:]:
                            material_row = [
                                Paragraph("", table_text_style),
                                Paragraph("", table_text_style),
                                Paragraph("", table_text_style),
                                Paragraph("", table_text_style),
                                Paragraph("", table_text_style),
                                Paragraph("", table_text_style),
                                Paragraph(self.safe_str(material.name, "-"), table_text_style),
                                Paragraph(self.safe_str(material.unit, "-"), table_text_style),
                                Paragraph(self.safe_str(material.quantity, ""), table_text_style),
                                Paragraph(self.safe_format_float(material.price, "0.0"), table_text_style),
                                Paragraph(self.safe_format_float(work.total_materials, "0.0"), table_text_style),
                                Paragraph("", table_text_style)
                            ]
                            data.append(material_row)
                    else:
                        data.append(work_row)
                        work_start_rows[(section_idx, work_idx)] = len(data) - 1

            works_sum = sum(work.total_work for section in self.table_manager.model.estimate for work in section.works)
            materials_sum = sum(work.total_materials for section in self.table_manager.model.estimate for work in section.works)
            summary_sum = works_sum + materials_sum

            summary_data = [
                [
                    Paragraph(
                        "Доставка материала, работа грузчиков, подъем материала, тарирование мусора, вынос/вывоз мусора (15% от стоимости материалов):",
                        summary_text_style),
                    *[Paragraph("", table_text_style) for _ in range(10)],
                    Paragraph(self.safe_format_float(materials_sum * 0.15, "0.0"), summary_value_style)
                ],
                [
                    Paragraph("Сметный расчёт", summary_title_style),
                    *[Paragraph("", table_text_style) for _ in range(11)]
                ],
                [
                    Paragraph("Итого без НДС:", summary_text_style),
                    *[Paragraph("", table_text_style) for _ in range(10)],
                    Paragraph(self.safe_format_float(summary_sum + materials_sum * 0.15, "0.0"),
                              summary_value_style)
                ],
                [
                    Paragraph("В т.ч. ФОТ:", summary_text_style),
                    *[Paragraph("", table_text_style) for _ in range(10)],
                    Paragraph(self.safe_format_float(works_sum, "0.0"), summary_value_style)
                ],
                [
                    Paragraph("В т.ч. Материалы:", summary_text_style),
                    *[Paragraph("", table_text_style) for _ in range(10)],
                    Paragraph(self.safe_format_float(materials_sum, "0.0"), summary_value_style)
                ]
            ]

            # Преобразуем данные в Paragraph
            table_data = []
            for i, row in enumerate(data):
                if i == 0:  # Заголовки
                    table_data.append([Paragraph(cell, table_header_style) for cell in headers])
                elif i == 1:
                    table_data.append([Paragraph(str(label), table_header_style) for label in fot_labels])
                else:
                    table_data.append(row)
                    # table_data.append([Paragraph(cell, table_text_style) for cell in row])

            # Создаем таблицу
            table = LongTable(table_data, colWidths=col_widths, repeatRows=2)
            table_summary = LongTable(summary_data, colWidths=col_widths)

            # Настройка стиля таблицы
            table_style = [
                ('SPAN', (4, 0), (5, 0)),
                ('ALIGN', (4, 0), (4, 0), 'CENTER'),

                ('SPAN', (7, 0), (10, 0)),
                ('ALIGN', (4, 0), (4, 0), 'CENTER'),

                ('SPAN', (0, 0), (0, 1)),
                ('SPAN', (1, 0), (1, 1)),
                ('SPAN', (2, 0), (2, 1)),
                ('SPAN', (3, 0), (3, 1)),
                ('SPAN', (6, 0), (6, 1)),
                ('SPAN', (7, 0), (7, 1)),
                ('SPAN', (11, 0), (11, 1)),

                ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),
                ('FONTNAME', (0, 0), (-1, 1), 'Arial-Bold'),
                ('FONTSIZE', (0, 0), (-1, 1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 1), 4),

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

            for section_idx, start_section_row in section_start_rows.items():
                table_style.extend([
                    ('SPAN', (0, start_section_row), (11, start_section_row)),
                    ('BACKGROUND', (0, start_section_row), (11, start_section_row), colors.whitesmoke),
                    ('FONTNAME', (0, start_section_row), (11, start_section_row), 'Arial-Bold'),
                    ('ALIGN', (0, start_section_row), (11, start_section_row), 'CENTER'),  # Выравнивание по горизонтали
                    ('VALIGN', (0, start_section_row), (11, start_section_row), 'MIDDLE')
                ])

            for (s_idx, w_idx), start_row in work_start_rows.items():
                work = self.table_manager.model.estimate[s_idx - 1].works[w_idx - 1]
                end_row = start_row
                if work.materials:
                    end_row = start_row + len(work.materials) - 1

                if end_row > start_row:
                    for col in [0, 1, 2, 3, 4, 5, 10, 11]:
                        table_style.append(('SPAN', (col, start_row), (col, end_row)))

            summary_style = [
                ('SPAN', (0, 0), (10, 0)),
                ('SPAN', (0, 1), (11, 1)),
                ('ALIGN', (0, 1), (0, 1), 'CENTER'),
                ('BACKGROUND', (0, 1), (11, 1), colors.lightgrey),
                ('TEXTCOLOR', (0, 1), (11, 1), colors.black),
                ('SPAN', (0, 2), (10, 2)),
                ('SPAN', (0, 3), (10, 3)),
                ('SPAN', (0, 4), (10, 4)),
                ('FONTNAME', (0, 0), (11, -1), 'Arial-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]

            table.setStyle(TableStyle(table_style))
            table_summary.setStyle(TableStyle(summary_style))
            elements.append(table)
            elements.append(Spacer(1, 10 * mm))
            elements.append(table_summary)

            # Генерация PDF
            doc.build(elements)
            QMessageBox.information(self, "Успешно", f"PDF успешно сохранен:\n{file_path}")

            webbrowser.open_new_tab(f"file://{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении PDF:\n{str(e)}")
