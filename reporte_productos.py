import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QTabWidget, QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from datetime import datetime
import subprocess

class ReporteProductos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Productos")
        self.resize(1000, 600)
        self.db_path = "pruebas.db"

        main_layout = QVBoxLayout(self)

        # Barra superior: Título y botones
        top_layout = QHBoxLayout()
        lbl_titulo = QLabel("Reporte de Productos")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold;")
        top_layout.addWidget(lbl_titulo)
        top_layout.addStretch()

        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_volver.clicked.connect(self.volver)
        top_layout.addWidget(btn_volver)

        btn_exportar = QPushButton("Exportar")
        btn_exportar.setIcon(QIcon.fromTheme("document-save"))
        btn_exportar.clicked.connect(self.exportar)
        top_layout.addWidget(btn_exportar)

        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setIcon(QIcon.fromTheme("document-print"))
        btn_imprimir.clicked.connect(self.imprimir)
        top_layout.addWidget(btn_imprimir)

        main_layout.addLayout(top_layout)

        # Buscador y controles
        controls_layout = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o código...")
        self.input_busqueda.returnPressed.connect(self.buscar)
        btn_buscar = QPushButton("Buscar")
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
        self.tabla_disp.setColumnCount(7)
        self.tabla_disp.setHorizontalHeaderLabels(["Cód.", "Imagen", "Nombre", "Precio", "Stock", "Estado", "Historial"])
        self.tabla_disp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_disp.setAlternatingRowColors(True)
        self.tabla_disp.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_disp.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_disp.horizontalHeader().sectionClicked.connect(self.ordenar_disponibles)
        layout_disp = QVBoxLayout()
        layout_disp.addWidget(self.tabla_disp)
        self.tab_disponibles.setLayout(layout_disp)

        # Tabla de Eliminados
        self.tabla_eli = QTableWidget()
        self.tabla_eli.setColumnCount(7)
        self.tabla_eli.setHorizontalHeaderLabels(["Cód.", "Imagen", "Nombre", "Precio", "Stock", "Estado", "Historial"])
        self.tabla_eli.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_eli.setAlternatingRowColors(True)
        self.tabla_eli.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_eli.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_eli.horizontalHeader().sectionClicked.connect(self.ordenar_eliminados)
        layout_eli = QVBoxLayout()
        layout_eli.addWidget(self.tabla_eli)
        self.tab_eliminados.setLayout(layout_eli)

        # Cambiar pestaña
        self.tabs.currentChanged.connect(self.buscar)

        # Orden actual (columna, asc/desc)
        self.orden_col = 0
        self.orden_asc = True

        self.buscar()

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        main_layout.addWidget(btn_menu, alignment=Qt.AlignLeft)

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
        query = """
            SELECT codigo, imagen, nombre, precio, stock
            FROM productos
            WHERE 1=1
        """
        params = []
        if filtro:
            query += " AND (nombre LIKE ? OR codigo LIKE ?)"
            params += [f"%{filtro}%", f"%{filtro}%"]
        query += " ORDER BY nombre ASC"
        cursor.execute(query, params)
        productos = cursor.fetchall()
        conn.close()
        for row_num, (codigo, imagen, nombre, precio, stock) in enumerate(productos):
            self.tabla_disp.insertRow(row_num)
            self.tabla_disp.setItem(row_num, 0, QTableWidgetItem(str(codigo)))
            # Imagen
            img_item = QTableWidgetItem()
            if imagen and os.path.exists(imagen):
                pixmap = QPixmap(imagen).scaled(40, 40, Qt.KeepAspectRatio)
                img_item.setData(Qt.DecorationRole, pixmap)
            else:
                img_item.setText("[img]")
            self.tabla_disp.setItem(row_num, 1, img_item)
            self.tabla_disp.setItem(row_num, 2, QTableWidgetItem(nombre))
            self.tabla_disp.setItem(row_num, 3, QTableWidgetItem(f"{precio:.2f}"))
            self.tabla_disp.setItem(row_num, 4, QTableWidgetItem(str(stock)))
            # Estado
            if stock > 0:
                estado_item = QTableWidgetItem("🟢 Activo")
                estado_item.setForeground(Qt.green)
            else:
                estado_item = QTableWidgetItem("🔴 Baja")
                estado_item.setForeground(Qt.red)
            self.tabla_disp.setItem(row_num, 5, estado_item)
            # Botón historial
            btn_hist = QPushButton("Ver")
            btn_hist.clicked.connect(lambda _, cod=codigo: self.ver_historial(cod))
            self.tabla_disp.setCellWidget(row_num, 6, btn_hist)

    def cargar_eliminados(self, filtro=""):
        self.tabla_eli.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = """
            SELECT codigo, imagen, nombre, precio, stock
            FROM productos_eliminados
            WHERE 1=1
        """
        params = []
        if filtro:
            query += " AND (nombre LIKE ? OR codigo LIKE ?)"
            params += [f"%{filtro}%", f"%{filtro}%"]
        query += " ORDER BY nombre ASC"
        cursor.execute(query, params)
        productos = cursor.fetchall()
        conn.close()
        for row_num, (codigo, imagen, nombre, precio, stock) in enumerate(productos):
            self.tabla_eli.insertRow(row_num)
            self.tabla_eli.setItem(row_num, 0, QTableWidgetItem(str(codigo)))
            # Imagen
            img_item = QTableWidgetItem()
            if imagen and os.path.exists(imagen):
                pixmap = QPixmap(imagen).scaled(40, 40, Qt.KeepAspectRatio)
                img_item.setData(Qt.DecorationRole, pixmap)
            else:
                img_item.setText("[img]")
            self.tabla_eli.setItem(row_num, 1, img_item)
            self.tabla_eli.setItem(row_num, 2, QTableWidgetItem(nombre))
            self.tabla_eli.setItem(row_num, 3, QTableWidgetItem(f"{precio:.2f}"))
            self.tabla_eli.setItem(row_num, 4, QTableWidgetItem(str(stock)))
            estado_item = QTableWidgetItem("🔴 Baja")
            estado_item.setForeground(Qt.red)
            self.tabla_eli.setItem(row_num, 5, estado_item)
            # Botón historial
            btn_hist = QPushButton("Ver")
            btn_hist.clicked.connect(lambda _, cod=codigo: self.ver_historial(cod, eliminado=True))
            self.tabla_eli.setCellWidget(row_num, 6, btn_hist)

    def exportar(self):
        QMessageBox.information(self, "Exportar", "Funcionalidad de exportar a PDF/Excel pendiente de implementar.")

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