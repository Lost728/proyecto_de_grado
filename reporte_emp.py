import sys
import os
import subprocess
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QTabWidget, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime

class ReporteEmpleados(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Empleados")
        self.resize(800, 500)
        self.db_path = "pruebas.db"

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Botón Regresar
        btn_regresar = QPushButton("Regresar")
        btn_regresar.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_regresar.clicked.connect(self.regresar_a_buscar_empleado)
        main_layout.addWidget(btn_regresar, alignment=Qt.AlignLeft)

        # Botón Menú Principal
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        main_layout.addWidget(btn_menu, alignment=Qt.AlignLeft)

        # Título
        titulo = QLabel("Reporte de Empleados")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(titulo)

        # Buscador y controles
        controls_layout = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o CI...")
        self.input_busqueda.returnPressed.connect(self.buscar)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar)
        controls_layout.addWidget(QLabel("Buscar:"))
        controls_layout.addWidget(self.input_busqueda)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        # Tabs: Activos y Eliminados, cada uno con su propia tabla
        self.tabs = QTabWidget()
        self.tab_activos = QWidget()
        self.tab_eliminados = QWidget()
        self.tabs.addTab(self.tab_activos, "Activos")
        self.tabs.addTab(self.tab_eliminados, "Eliminados")
        main_layout.addWidget(self.tabs)

        # Tabla de Activos
        self.tabla_activos = QTableWidget()
        self.tabla_activos.setColumnCount(6)
        self.tabla_activos.setHorizontalHeaderLabels(["CI", "Nombre", "Celular", "Rol", "Estado", "Fecha"])
        self.tabla_activos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_activos.setAlternatingRowColors(True)
        layout_activos = QVBoxLayout()
        layout_activos.addWidget(self.tabla_activos)
        self.tab_activos.setLayout(layout_activos)

        # Tabla de Eliminados
        self.tabla_eliminados = QTableWidget()
        self.tabla_eliminados.setColumnCount(6)
        self.tabla_eliminados.setHorizontalHeaderLabels(["CI", "Nombre", "Celular", "Rol", "Estado", "Fecha"])
        self.tabla_eliminados.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_eliminados.setAlternatingRowColors(True)
        layout_eliminados = QVBoxLayout()
        layout_eliminados.addWidget(self.tabla_eliminados)
        self.tab_eliminados.setLayout(layout_eliminados)

        # Cambiar pestaña
        self.tabs.currentChanged.connect(self.buscar)

        self.buscar()

    def buscar(self):
        filtro = self.input_busqueda.text().strip()
        tab_idx = self.tabs.currentIndex()
        if tab_idx == 0:
            self.cargar_empleados_activos(filtro)
        else:
            self.cargar_empleados_eliminados(filtro)

    def cargar_empleados_activos(self, filtro=""):
        self.tabla_activos.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if filtro:
            cursor.execute("""
                SELECT ci, nombre, celular, rol, fecha_creacion
                FROM empleado
                WHERE (nombre LIKE ? OR ci LIKE ?)
                ORDER BY fecha_creacion DESC
            """, (f"%{filtro}%", f"%{filtro}%"))
        else:
            cursor.execute("""
                SELECT ci, nombre, celular, rol, fecha_creacion
                FROM empleado
                ORDER BY fecha_creacion DESC
            """)
        empleados = cursor.fetchall()
        conn.close()
        for row_num, (ci, nombre, celular, rol, fecha) in enumerate(empleados):
            self.tabla_activos.insertRow(row_num)
            self.tabla_activos.setItem(row_num, 0, QTableWidgetItem(str(ci)))
            self.tabla_activos.setItem(row_num, 1, QTableWidgetItem(nombre))
            self.tabla_activos.setItem(row_num, 2, QTableWidgetItem(celular if celular else ""))
            self.tabla_activos.setItem(row_num, 3, QTableWidgetItem(rol))
            estado_item = QTableWidgetItem("🟢 Activo")
            estado_item.setForeground(Qt.green)
            self.tabla_activos.setItem(row_num, 4, estado_item)
            self.tabla_activos.setItem(row_num, 5, QTableWidgetItem(self.formatear_fecha(fecha)))

    def cargar_empleados_eliminados(self, filtro=""):
        self.tabla_eliminados.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if filtro:
            cursor.execute("""
                SELECT ci, nombre, celular, rol, fecha_borrado
                FROM empleados_eliminados
                WHERE (nombre LIKE ? OR ci LIKE ?)
                ORDER BY fecha_borrado DESC
            """, (f"%{filtro}%", f"%{filtro}%"))
        else:
            cursor.execute("""
                SELECT ci, nombre, celular, rol, fecha_borrado
                FROM empleados_eliminados
                ORDER BY fecha_borrado DESC
            """)
        empleados = cursor.fetchall()
        conn.close()
        for row_num, (ci, nombre, celular, rol, fecha) in enumerate(empleados):
            self.tabla_eliminados.insertRow(row_num)
            self.tabla_eliminados.setItem(row_num, 0, QTableWidgetItem(str(ci)))
            self.tabla_eliminados.setItem(row_num, 1, QTableWidgetItem(nombre))
            self.tabla_eliminados.setItem(row_num, 2, QTableWidgetItem(celular if celular else ""))
            self.tabla_eliminados.setItem(row_num, 3, QTableWidgetItem(rol))
            estado_item = QTableWidgetItem("🔴 Baja")
            estado_item.setForeground(Qt.red)
            self.tabla_eliminados.setItem(row_num, 4, estado_item)
            self.tabla_eliminados.setItem(row_num, 5, QTableWidgetItem(self.formatear_fecha(fecha)))

    def formatear_fecha(self, fecha):
        # Si la fecha es timestamp, conviértela, si no, muéstrala como está
        try:
            if isinstance(fecha, int) or (isinstance(fecha, str) and fecha.isdigit()):
                return datetime.fromtimestamp(int(fecha)).strftime("%Y-%m-%d")
            return str(fecha)[:10]
        except Exception:
            return str(fecha)

    def regresar_a_buscar_empleado(self):
        script_path = os.path.join(os.path.dirname(__file__), "buscar_empleado.py")
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
            return
        self.close()
        subprocess.Popen([sys.executable, script_path])

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
    ventana = ReporteEmpleados()
    ventana.showMaximized()
    sys.exit(app.exec_())