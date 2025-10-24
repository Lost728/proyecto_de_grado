import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QTabWidget, QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt
from datetime import datetime
import subprocess
import pandas as pd
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument

class ReporteProductos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Productos")
        self.resize(1000, 600)
        self.db_path = "pruebas.db"

        # Background image label (image6.jpg)
        img_path = os.path.join(os.path.dirname(__file__), "image6.jpg")
        if os.path.exists(img_path):
            self._bg_pixmap = QPixmap(img_path)
            self.bg_label = QLabel(self)
            self.bg_label.setScaledContents(True)
            # Place behind other widgets
            self.bg_label.lower()
            try:
                scaled = self._bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.bg_label.setPixmap(scaled)
                self.bg_label.resize(self.size())
            except Exception:
                self.bg_label.setPixmap(self._bg_pixmap)

        main_layout = QVBoxLayout(self)

        # Light stylesheet using the image palette (purple, pink, cyan)
        self.setStyleSheet('''
            QWidget { background: transparent; color: #FFFFFF; }
            QLabel#title { font-size: 22px; font-weight: bold; color: #ffffff; }
            QLineEdit { background: rgba(0,0,0,0.18); border: 1px solid rgba(255,255,255,0.06); padding: 6px; color: #FFFFFF; border-radius:6px; }
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5b2c6f, stop:1 #2c3e50); color: #FFFFFF; border-radius: 8px; padding: 6px 10px; }
            QPushButton#accent { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5a2a63, stop:1 #2a3a4a); color: #FFFFFF; }
            QTabWidget::pane { background: rgba(0,0,0,0.30); border: none; }
            /* Tabs (Disponibles / Eliminados) */
            QTabBar::tab {
                background: rgba(0,0,0,0.12);
                color: rgba(255,255,255,0.95);
                padding: 8px 14px;
                border-radius: 6px;
                margin-right: 6px;
            }
            QTabBar::tab:hover {
                background: rgba(0,0,0,0.22);
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6f2b78, stop:1 #2f3b8f);
                color: #ffffff;
                font-weight: 600;
            }
            QHeaderView::section { background: rgba(0,0,0,0.75); color: white; padding: 6px; }
            QTableWidget { background: transparent; color: #FFFFFF; gridline-color: rgba(0,0,0,0.12); }
            QTableWidget::item { background: rgba(0,0,0,0.12); }
            QTableWidget::item:selected { background: rgba(155,89,182,0.45); color: #fff; }
        ''')

        # Barra superior: Título y botones
        top_layout = QHBoxLayout()

        # Left group: Volver + Menú Principal
        left_buttons = QHBoxLayout()
        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #6f2b78; color: #ffffff; font-size: 14px; border-radius:6px; padding:6px 10px;")
        btn_volver.clicked.connect(self.volver)
        left_buttons.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #6f2b78; color: #ffffff; font-size: 14px; border-radius:6px; padding:6px 10px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        left_buttons.addWidget(btn_menu)

        top_layout.addLayout(left_buttons)

        # Title
        lbl_titulo = QLabel("Reporte de Productos")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        top_layout.addWidget(lbl_titulo)
        top_layout.addStretch()

        # Right group: Exportar, Imprimir
        btn_exportar = QPushButton("Exportar")
        btn_exportar.setIcon(QIcon.fromTheme("document-save"))
        btn_exportar.setStyleSheet("background-color: rgba(0,0,0,0.45); color: #ffffff; border-radius:6px; padding:6px 10px;")
        btn_exportar.clicked.connect(self.exportar)
        top_layout.addWidget(btn_exportar)

        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setIcon(QIcon.fromTheme("document-print"))
        btn_imprimir.setStyleSheet("background-color: rgba(0,0,0,0.45); color: #ffffff; border-radius:6px; padding:6px 10px;")
        btn_imprimir.clicked.connect(self.imprimir)
        top_layout.addWidget(btn_imprimir)

        main_layout.addLayout(top_layout)

        # Buscador y controles
        controls_layout = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o código...")
        self.input_busqueda.returnPressed.connect(self.buscar)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("background-color: rgba(0,0,0,0.28); color: #ffffff; border-radius:6px; padding:6px 10px;")
        btn_buscar.clicked.connect(self.buscar)
        controls_layout.addWidget(QLabel("Buscar:"))
        controls_layout.addWidget(self.input_busqueda)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        # Tabs: Disponibles y Eliminados
        self.tabs = QTabWidget()
        self.tab_disponibles = QWidget()
        self.tab_eliminados = QWidget()
        self.tabs.addTab(self.tab_disponibles, "Disponibles")
        self.tabs.addTab(self.tab_eliminados, "Eliminados")
        main_layout.addWidget(self.tabs)

        # Tabla de Disponibles
        self.tabla_disp = QTableWidget()
        self.tabla_disp.setColumnCount(8)
        self.tabla_disp.setHorizontalHeaderLabels([
            "Cód.", "Imagen", "Nombre", "Tipo", "Precio", "Stock", "Estado", "Historial"
        ])
        self.tabla_disp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Disable default alternating white rows and use explicit darker item backgrounds
        self.tabla_disp.setAlternatingRowColors(False)
        self.tabla_disp.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_disp.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_disp.horizontalHeader().sectionClicked.connect(self.ordenar_disponibles)
        # Improve readability: bigger header and row height, stronger selection
        self.tabla_disp.horizontalHeader().setFixedHeight(38)
        self.tabla_disp.verticalHeader().setDefaultSectionSize(36)
        # stronger selection color
        self.tabla_disp.setStyleSheet('''
            QTableWidget { background: transparent; color: #FFFFFF; }
            QTableWidget::item:selected { background: rgba(155,89,182,0.45); color: #fff; }
            QHeaderView::section { background: rgba(0,0,0,0.7); color: #fff; }
        ''')
        layout_disp = QVBoxLayout()
        layout_disp.addWidget(self.tabla_disp)
        self.tab_disponibles.setLayout(layout_disp)

        # Tabla de Eliminados
        self.tabla_eli = QTableWidget()
        self.tabla_eli.setColumnCount(8)
        self.tabla_eli.setHorizontalHeaderLabels([
            "Cód.", "Imagen", "Nombre", "Tipo", "Precio", "Stock", "Estado", "Historial"
        ])
        self.tabla_eli.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_eli.setAlternatingRowColors(False)
        self.tabla_eli.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_eli.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_eli.horizontalHeader().sectionClicked.connect(self.ordenar_eliminados)
        self.tabla_eli.horizontalHeader().setFixedHeight(38)
        self.tabla_eli.verticalHeader().setDefaultSectionSize(36)
        layout_eli = QVBoxLayout()
        layout_eli.addWidget(self.tabla_eli)
        self.tab_eliminados.setLayout(layout_eli)

        # Cambiar pestaña
        self.tabs.currentChanged.connect(self.buscar)

        # Orden actual (columna, asc/desc)
        self.orden_col = 0
        self.orden_asc = True

        self.buscar()

    # (Se eliminó el botón 'Menú Principal' inferior; ahora está en la barra superior)

    def resizeEvent(self, event):
        """Reescalar el fondo al cambiar el tamaño de la ventana."""
        try:
            if hasattr(self, '_bg_pixmap') and self._bg_pixmap and hasattr(self, 'bg_label'):
                scaled = self._bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.bg_label.setPixmap(scaled)
                self.bg_label.resize(self.size())
                self.bg_label.lower()
        except Exception:
            pass
        return super().resizeEvent(event)

    def volver(self):
        script_path = os.path.join(os.path.dirname(__file__), "menu.py")
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
            return
        self.close()
        os.system(f'python "{script_path}"')

    def buscar(self):
        filtro = self.input_busqueda.text().strip()
        tab_idx = self.tabs.currentIndex()
        if tab_idx == 0:
            self.cargar_disponibles(filtro)
        else:
            self.cargar_eliminados(filtro)

    def cargar_disponibles(self, filtro=""):
        self.tabla_disp.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT codigo, imagen, nombre, precio, fecha_venc, id_empleado, unidades FROM productos WHERE unidades > 0"
        params = []
        if filtro:
            query += " AND (nombre LIKE ? OR codigo LIKE ?)"
            params += [f"%{filtro}%", f"%{filtro}%"]
        query += " ORDER BY nombre ASC"
        cursor.execute(query, params)
        productos = cursor.fetchall()
        conn.close()

        for row_num, (codigo, imagen, nombre, precio, fecha_venc, id_empleado, unidades) in enumerate(productos):
            self.tabla_disp.insertRow(row_num)
            # Código
            item_cod = QTableWidgetItem(str(codigo))
            item_cod.setForeground(Qt.white)
            self.tabla_disp.setItem(row_num, 0, item_cod)

            # Imagen (decoración)
            img_item = QTableWidgetItem()
            if imagen and os.path.exists(imagen):
                pixmap = QPixmap(imagen).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_item.setData(Qt.DecorationRole, pixmap)
            else:
                img_item.setText("[img]")
            img_item.setForeground(Qt.white)
            self.tabla_disp.setItem(row_num, 1, img_item)

            # Nombre
            item_name = QTableWidgetItem(nombre)
            item_name.setForeground(Qt.white)
            self.tabla_disp.setItem(row_num, 2, item_name)

            # Tipo (no en DB) -> vacío
            item_tipo = QTableWidgetItem("")
            item_tipo.setForeground(Qt.white)
            self.tabla_disp.setItem(row_num, 3, item_tipo)

            # Precio (col 4)
            try:
                precio_text = f"{precio:.2f}"
            except Exception:
                precio_text = str(precio)
            item_prec = QTableWidgetItem(precio_text)
            item_prec.setForeground(Qt.white)
            item_prec.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_disp.setItem(row_num, 4, item_prec)

            # Stock/Unidades (col 5)
            item_stock = QTableWidgetItem(str(unidades))
            item_stock.setForeground(Qt.white)
            item_stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_disp.setItem(row_num, 5, item_stock)

            # Estado (col 6)
            if unidades > 0:
                estado_item = QTableWidgetItem("🟢 Activo")
                estado_item.setForeground(Qt.green)
            else:
                estado_item = QTableWidgetItem("🔴 Baja")
                estado_item.setForeground(Qt.red)
            self.tabla_disp.setItem(row_num, 6, estado_item)

            # Botón historial (col 7)
            btn_hist = QPushButton("Ver")
            btn_hist.setStyleSheet('''
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #9b59b6, stop:1 #5dade2); color: #fff; border-radius:6px; padding:6px; }
                QPushButton:hover { opacity: 0.95; }
            ''')
            btn_hist.clicked.connect(lambda _, cod=codigo: self.ver_historial(cod))
            self.tabla_disp.setCellWidget(row_num, 7, btn_hist)

            # Row height for readability
            self.tabla_disp.setRowHeight(row_num, 36)

    def cargar_eliminados(self, filtro=""):
        self.tabla_eli.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Detect available tables for deleted products
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]

        mapped = []
        if 'productos_eliminados' in tables:
            query = "SELECT codigo, imagen, nombre, 'Caja/Paquete/Unidad' as tipo, precio, stock FROM productos_eliminados WHERE 1=1"
            params = []
            if filtro:
                query += " AND (nombre LIKE ? OR codigo LIKE ?)"
                params += [f"%{filtro}%", f"%{filtro}%"]
            query += " ORDER BY nombre ASC"
            cursor.execute(query, params)
            mapped = cursor.fetchall()

        elif 'productos_borrados' in tables:
            # Older schema: productos_borrados (id_producto, codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado)
            query = "SELECT codigo, imagen, nombre, precio, stock FROM productos_borrados WHERE 1=1"
            params = []
            if filtro:
                query += " AND (nombre LIKE ? OR codigo LIKE ?)"
                params += [f"%{filtro}%", f"%{filtro}%"]
            query += " ORDER BY nombre ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            # map to (codigo, imagen, nombre, tipo, precio, stock)
            for codigo, imagen, nombre, precio, stock in rows:
                mapped.append((codigo, imagen, nombre, '', precio, stock))

        else:
            conn.close()
            QMessageBox.information(self, "Sin eliminados", "No se encontró la tabla de productos eliminados en la base de datos.")
            return

        conn.close()

        for row_num, (codigo, imagen, nombre, tipo, precio, stock) in enumerate(mapped):
            self.tabla_eli.insertRow(row_num)
            item_cod = QTableWidgetItem(str(codigo))
            item_cod.setForeground(Qt.white)
            self.tabla_eli.setItem(row_num, 0, item_cod)

            img_item = QTableWidgetItem()
            if imagen and os.path.exists(imagen):
                pixmap = QPixmap(imagen).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_item.setData(Qt.DecorationRole, pixmap)
            else:
                img_item.setText("[img]")
            img_item.setForeground(Qt.white)
            self.tabla_eli.setItem(row_num, 1, img_item)

            item_name = QTableWidgetItem(nombre)
            item_name.setForeground(Qt.white)
            self.tabla_eli.setItem(row_num, 2, item_name)

            item_tipo = QTableWidgetItem(tipo)
            item_tipo.setForeground(Qt.white)
            self.tabla_eli.setItem(row_num, 3, item_tipo)

            try:
                precio_text = f"{precio:.2f}"
            except Exception:
                precio_text = str(precio)
            item_prec = QTableWidgetItem(precio_text)
            item_prec.setForeground(Qt.white)
            item_prec.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_eli.setItem(row_num, 4, item_prec)

            item_stock = QTableWidgetItem(str(stock))
            item_stock.setForeground(Qt.white)
            item_stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_eli.setItem(row_num, 5, item_stock)

            estado_item = QTableWidgetItem("🔴 Baja")
            estado_item.setForeground(Qt.red)
            self.tabla_eli.setItem(row_num, 6, estado_item)

            btn_hist = QPushButton("Ver")
            btn_hist.setStyleSheet('''
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #9b59b6, stop:1 #5dade2); color: #fff; border-radius:6px; padding:6px; }
                QPushButton:hover { opacity: 0.95; }
            ''')
            btn_hist.clicked.connect(lambda _, cod=codigo: self.ver_historial(cod, eliminado=True))
            self.tabla_eli.setCellWidget(row_num, 7, btn_hist)

            self.tabla_eli.setRowHeight(row_num, 36)

    def exportar(self):
            # Elegir ubicación y formato
            options = "Excel (*.xlsx);;PDF (*.pdf)"
            file_path, filtro = QFileDialog.getSaveFileName(self, "Exportar", "productos", options)
            if not file_path:
                return

            # Escoger la tabla activa
            tabla = self.tabla_disp if self.tabs.currentIndex() == 0 else self.tabla_eli

            # Recolectar datos
            headers = [tabla.horizontalHeaderItem(i).text() if tabla.horizontalHeaderItem(i) else f"Col{i}" for i in range(tabla.columnCount())]
            data = []
            for r in range(tabla.rowCount()):
                row = []
                for c in range(tabla.columnCount()):
                    item = tabla.item(r, c)
                    if item:
                        row.append(item.text())
                    else:
                        # si la celda tiene un widget (p.ej botón), dejar vacío o marcar
                        widget = tabla.cellWidget(r, c)
                        if widget and hasattr(widget, 'text'):
                            try:
                                row.append(widget.text())
                            except Exception:
                                row.append("")
                        else:
                            row.append("")
                data.append(row)

            try:
                if file_path.lower().endswith('.xlsx') or (filtro and 'Excel' in filtro):
                    # exportar a Excel
                    df = pd.DataFrame(data, columns=headers)
                    df.to_excel(file_path, index=False)
                    QMessageBox.information(self, "Exportación", f"Exportado a Excel:\n{file_path}")
                elif file_path.lower().endswith('.pdf') or (filtro and 'PDF' in filtro):
                    # exportar a PDF usando QTextDocument
                    # construir HTML simple
                    html = ['<html><head><meta charset="utf-8"></head><body>']
                    html.append('<h2>Reporte de Productos</h2>')
                    html.append('<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">')
                    # headers
                    html.append('<tr style="background:#2f1b3a; color:white;">')
                    for h in headers:
                        html.append(f'<th>{h}</th>')
                    html.append('</tr>')
                    # rows
                    for row in data:
                        html.append('<tr>')
                        for cell in row:
                            html.append(f'<td>{cell}</td>')
                        html.append('</tr>')
                    html.append('</table></body></html>')
                    html_str = ''.join(html)

                    doc = QTextDocument()
                    doc.setHtml(html_str)
                    printer = QPrinter(QPrinter.HighResolution)
                    printer.setOutputFormat(QPrinter.PdfFormat)
                    printer.setOutputFileName(file_path)
                    doc.print_(printer)
                    QMessageBox.information(self, "Exportación", f"Exportado a PDF:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Formato no soportado", "Por favor elija .xlsx o .pdf como extensión.")
            except Exception as e:
                QMessageBox.critical(self, "Error al exportar", f"No se pudo exportar:\n{e}")

    def imprimir(self):
        QMessageBox.information(self, "Imprimir", "Funcionalidad de impresión pendiente de implementar.")

    def ver_historial(self, codigo, eliminado=False):
        script_path = os.path.join(os.path.dirname(__file__), "historial_prod.py")
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
            return
        # Llama a historial_prod.py pasando el código del producto como argumento
        subprocess.Popen([sys.executable, script_path, str(codigo)])

    def ordenar_disponibles(self, col):
        self.orden_col = col
        self.orden_asc = not getattr(self, "orden_asc", True)
        self.ordenar_tabla(self.tabla_disp, col, self.orden_asc)

    def ordenar_eliminados(self, col):
        self.orden_col = col
        self.orden_asc = not getattr(self, "orden_asc", True)
        self.ordenar_tabla(self.tabla_eli, col, self.orden_asc)

    def ordenar_tabla(self, tabla, col, asc):
        tabla.sortItems(col, Qt.AscendingOrder if asc else Qt.DescendingOrder)

    def ir_menu_principal(self):
        """Ir a menu.py"""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "menu.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir menu.py: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = ReporteProductos()
    ventana.showMaximized()
    sys.exit(app.exec_())