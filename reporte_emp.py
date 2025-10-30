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

        # Fondo gradiente púrpura-azul y estilos modernos
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6a1b9a, stop:1 #1976d2);
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 15px;
                color: #ffffff;
            }
            QLabel#titulo {
                font-size: 28px;
                font-weight: bold;
                color: #fff;
                padding: 18px 0 10px 0;
                letter-spacing: 1px;
                text-align: center;
            }
            QLabel {
                font-weight: 600;
                color: #e3e3e3;
            }
            QLineEdit {
                padding: 10px;
                border-radius: 10px;
                background: rgba(0,0,0,0.25);
                color: #ffffff;
                border: 1.5px solid #8bd3ff;
                margin-bottom: 8px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 12px;
                color: #22223b;
                font-weight: 700;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #8bd3ff);
                border: none;
                margin: 4px;
                transition: background 0.2s;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8bd3ff, stop:1 #7ed6fa);
                color: #22223b;
            }
            QTabWidget::pane {
                border: 2px solid #8bd3ff;
                border-radius: 10px;
                background: rgba(255,255,255,0.08);
            }
            QTabBar::tab {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #8bd3ff);
                color: #22223b;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px 18px;
                margin: 4px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8bd3ff, stop:1 #7ed6fa);
                color: #22223b;
            }
            QTableWidget {
                background: rgba(255,255,255,0.08);
                border-radius: 10px;
                border: 1.5px solid #8bd3ff;
                font-size: 14px;
                color: #22223b;
                gridline-color: #8bd3ff;
            }
            QTableWidget::item {
                background: rgba(255,255,255,0.18);
                color: #22223b;
                border-radius: 6px;
            }
            QTableWidget::item:selected {
                background-color: #7ed6fa;
                color: #22223b;
            }
            QHeaderView::section {
                background-color: #6a1b9a;
                color: #fff;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(18)
        self.setLayout(main_layout)

        # Botón Regresar y Menú Principal en una sola fila
        top_buttons_layout = QHBoxLayout()
        btn_regresar = QPushButton("Regresar")
        btn_regresar.clicked.connect(self.regresar_a_buscar_empleado)
        top_buttons_layout.addWidget(btn_regresar)
        btn_menu = QPushButton("Menú Principal")
        btn_menu.clicked.connect(self.ir_menu_principal)
        top_buttons_layout.addWidget(btn_menu)
        top_buttons_layout.addStretch()
        main_layout.addLayout(top_buttons_layout)

        # Título
        titulo = QLabel("Reporte de Empleados")
        titulo.setObjectName("titulo")
        main_layout.addWidget(titulo, alignment=Qt.AlignHCenter)

        # Buscador y controles
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o CI...")
        self.input_busqueda.returnPressed.connect(self.buscar)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar)
        controls_layout.addWidget(QLabel("Buscar:"))
        controls_layout.addWidget(self.input_busqueda, stretch=2)
        controls_layout.addWidget(btn_buscar)
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
        self.tabla_activos.setColumnCount(8)
        self.tabla_activos.setHorizontalHeaderLabels(["CI", "Nombre", "Celular", "Rol", "Estado", "Fecha", "Historial", "Registrar evento"])
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
            # Botón Historial
            btn_historial = QPushButton("Historial")
            btn_historial.clicked.connect(lambda _, ci=ci: self.ver_historial_empleado(ci))
            self.tabla_activos.setCellWidget(row_num, 6, btn_historial)
            # Botón Registrar evento
            btn_evento = QPushButton("Registrar evento")
            btn_evento.clicked.connect(lambda _, ci=ci: self.registrar_evento_empleado(ci))
            self.tabla_activos.setCellWidget(row_num, 7, btn_evento)
    def ver_historial_empleado(self, ci_empleado):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Historial de bajas - CI: {ci_empleado}")
        dialog.setFixedSize(600, 350)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Consulta solo bajas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT motivo, fecha_evento FROM historial_empleado WHERE ci_empleado = ? AND tipo_evento = 'baja' ORDER BY fecha_evento DESC
        """, (ci_empleado,))
        bajas = cursor.fetchall()
        conn.close()

        label = QLabel(f"El usuario {ci_empleado} tuvo bajas por:")
        label.setStyleSheet("font-size: 16px; font-weight: bold; color: #6a1b9a;")
        layout.addWidget(label)

        tabla = QTableWidget()
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["Motivo", "Fecha"])
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabla.setRowCount(len(bajas))
        for row, (motivo, fecha) in enumerate(bajas):
            fecha_str = datetime.fromtimestamp(int(fecha)).strftime("%Y-%m-%d") if str(fecha).isdigit() else str(fecha)
            tabla.setItem(row, 0, QTableWidgetItem(motivo))
            tabla.setItem(row, 1, QTableWidgetItem(fecha_str))
        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #8bd3ff); color: #22223b; font-weight: bold; border-radius: 10px; padding: 8px 15px; font-size: 15px;")
        btn_cerrar.clicked.connect(dialog.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec_()

    def registrar_evento_empleado(self, ci_empleado):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QTextEdit, QDateEdit, QPushButton
        from PyQt5.QtCore import QDate
        import time
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Registrar evento para CI: {ci_empleado}")
        dialog.setFixedSize(420, 420)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        label = QLabel(f"Registrar evento para empleado CI: {ci_empleado}")
        label.setStyleSheet("font-size: 16px; font-weight: bold; color: #6a1b9a;")
        layout.addWidget(label)

        # Tipo de evento
        tipo_evento = QComboBox()
        tipo_evento.addItems(["vacaciones", "baja", "despido", "observación"])
        layout.addWidget(QLabel("Tipo de evento:"))
        layout.addWidget(tipo_evento)

        # Motivo
        motivo = QLineEdit()
        motivo.setPlaceholderText("Motivo del evento (opcional)")
        layout.addWidget(QLabel("Motivo:"))
        layout.addWidget(motivo)

        # Fecha del evento
        fecha_evento = QDateEdit()
        fecha_evento.setCalendarPopup(True)
        fecha_evento.setDate(QDate.currentDate())
        fecha_evento.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(QLabel("Fecha del evento:"))
        layout.addWidget(fecha_evento)

        # Observaciones
        observaciones = QTextEdit()
        observaciones.setPlaceholderText("Observaciones adicionales")
        layout.addWidget(QLabel("Observaciones:"))
        layout.addWidget(observaciones)

        # Botón guardar
        btn_guardar = QPushButton("Guardar evento")
        btn_guardar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #8bd3ff); color: #22223b; font-weight: bold; border-radius: 10px; padding: 8px 15px; font-size: 15px;")
        def guardar():
            tipo = tipo_evento.currentText()
            mot = motivo.text().strip()
            fecha = int(time.mktime(fecha_evento.date().toPyDate().timetuple()))
            obs = observaciones.toPlainText().strip()
            # Obtener nombre, apellido, celular del empleado
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, apellido, celular FROM empleado WHERE ci = ?", (ci_empleado,))
            datos = cursor.fetchone()
            nombre, apellido, celular = datos if datos else ("", "", "")
            cursor.execute("""
                INSERT INTO historial_empleado (ci_empleado, tipo_evento, motivo, fecha_evento, observaciones, nombre, apellido, celular)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ci_empleado, tipo, mot, fecha, obs, nombre, apellido, celular))
            conn.commit()
            conn.close()
            QMessageBox.information(dialog, "Evento registrado", "El evento ha sido guardado correctamente.")
            dialog.accept()
            self.buscar()  # Refrescar tablas
        btn_guardar.clicked.connect(guardar)
        layout.addWidget(btn_guardar, alignment=Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec_()

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