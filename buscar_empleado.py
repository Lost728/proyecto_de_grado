import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QMessageBox,
    QMenu, QAction
)
from PyQt5.QtCore import Qt
import sqlite3
import os
import subprocess
from functools import partial

def obtener_db_path():
    """Retorna la ruta de la base de datos 'pruebas.db'."""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        db_path = os.path.join(exe_dir, "pruebas.db")
        if os.path.exists(db_path):
            return db_path
        base_path = sys._MEIPASS
        return os.path.join(base_path, "pruebas.db")
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "pruebas.db"))

db_path = obtener_db_path()

# Función para obtener empleados desde la base de datos
def obtener_empleados():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Se incluye apellidos en la consulta
        cursor.execute("SELECT id_empleado, CI, nombre, apellidos, celular, rol, fecha_creacion FROM empleado")
        empleados = cursor.fetchall()
        conn.close()
        return empleados
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Error", f"No se pudo obtener los datos: {e}")
        return []

# Función para eliminar un empleado
def eliminar_empleado(ci):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Recuperar datos del empleado
        cursor.execute("SELECT id_empleado, CI, nombre, apellidos, celular, rol, fecha_creacion FROM empleado WHERE CI = ?", (ci,))
        empleado = cursor.fetchone()

        if empleado:
            cursor.execute("""
                INSERT INTO empleados_eliminados 
                (id_empleado, ci, nombre, apellido, celular, rol, fecha_creacion, fecha_borrado)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (empleado[0], empleado[1], empleado[2], empleado[3], empleado[4], empleado[5], empleado[6]))
            
            # 3. Eliminar de tabla principal
            cursor.execute("DELETE FROM empleado WHERE CI = ?", (ci,))
            conn.commit()
            
            QMessageBox.information(
                None, "Éxito", 
                f"Empleado con CI {ci} eliminado y guardado en respaldo."
            )
        else:
            QMessageBox.warning(None, "Advertencia", "Empleado no encontrado.")
            
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Error", f"No se pudo completar la operación: {e}")
    finally:
        if conn:
            conn.close()

# Clase principal de la ventana
class VerEmpleados(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Administrar Empleados")
        self.setGeometry(100, 100, 1100, 600)
        import os
        fondo = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mar.jpg')).replace('\\', '/')
        self.setStyleSheet(f"""
            QWidget {{
                background-image: url('{fondo}');
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
                color: #ffffff;
            }}
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6);
                color: #22223b;
                border-radius: 10px;
                padding: 6px 10px;
                font-weight: bold;
            }}
            QLineEdit {{
                background: rgba(0,0,0,0.35);
                border: 1.8px solid rgba(126,214,250,0.6);
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }}
            QTableWidget {{
                background: rgba(0,0,0,0.45);
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.70);
                color: #ffffff; /* texto blanco para títulos */
                font-weight: bold;
                padding: 6px;
                border: none;
            }}
        """)

        # Layout principal
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)

        # Barra de navegación
        nav_layout = QHBoxLayout()
        btn_inicio = QPushButton("Ventas")
        btn_inicio.setStyleSheet("font-size: 14px;")
        btn_inicio.clicked.connect(self.ir_inicio)
        nav_layout.addWidget(btn_inicio)

        btn_insertar = QPushButton("Insertar Empleados")
        btn_insertar.setStyleSheet("font-size: 14px;")
        btn_insertar.clicked.connect(self.insertar_empleados)
        nav_layout.addWidget(btn_insertar)
        
        btn_emp_eliminados = QPushButton("Empleados Eliminados")
        btn_emp_eliminados.setStyleSheet("font-size: 14px;")
        btn_emp_eliminados.clicked.connect(self.emp_eliminados)
        nav_layout.addWidget(btn_emp_eliminados)

        btn_reportes = QPushButton("Menú de Reportes")
        btn_reportes.setStyleSheet("font-size: 14px;")
        btn_reportes.clicked.connect(self.menu_reportes)
        nav_layout.addWidget(btn_reportes)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("font-size: 14px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        nav_layout.addWidget(btn_menu)

        nav_layout.setAlignment(Qt.AlignLeft)
        main_layout.addLayout(nav_layout)

        # Título
        titulo = QLineEdit("Administrar Empleados")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        titulo.setReadOnly(True)
        main_layout.addWidget(titulo)

        # Campo de búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar empleado: Nombre, Apellidos o CI")
        self.search_input.setFixedWidth(400)
        search_layout.addWidget(self.search_input)

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("font-size: 14px;")
        btn_buscar.clicked.connect(self.buscar_empleados)
        search_layout.addWidget(btn_buscar)
        # Botón Actualizar
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setStyleSheet("font-size: 14px;")
        btn_actualizar.clicked.connect(self.cargar_empleados)
        search_layout.addWidget(btn_actualizar)
        main_layout.addLayout(search_layout)

        # Tabla de empleados (ahora con 7 columnas)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "CI", "Nombre", "Apellidos", "Celular", "Rol", "Estado", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)

        # Cargar datos iniciales
        self.cargar_empleados()

        # Establecer el widget principal
        self.setCentralWidget(main_container)

    def cargar_empleados(self):
        """Cargar empleados en la tabla."""
        empleados = obtener_empleados()
        self.table.setRowCount(0)

        import time
        for row_num, empleado in enumerate(empleados):
            self.table.insertRow(row_num)
            # id_empleado, CI, nombre, apellidos, celular, rol, fecha_creacion
            self.table.setItem(row_num, 0, QTableWidgetItem(str(empleado[0])))  # ID
            self.table.setItem(row_num, 1, QTableWidgetItem(str(empleado[1])))  # CI
            self.table.setItem(row_num, 2, QTableWidgetItem(str(empleado[2])))  # Nombre
            self.table.setItem(row_num, 3, QTableWidgetItem(str(empleado[3])))  # Apellidos
            self.table.setItem(row_num, 4, QTableWidgetItem(str(empleado[4])))  # Celular
            self.table.setItem(row_num, 5, QTableWidgetItem(str(empleado[5])))  # Rol
            # Estado: consulta historial_empleado para vacaciones
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tipo_evento, fecha_evento, observaciones FROM historial_empleado
                WHERE ci_empleado = ? ORDER BY fecha_evento DESC LIMIT 1
            """, (empleado[1],))
            evento = cursor.fetchone()
            conn.close()
            estado_item = None
            if evento and evento[0] == "vacaciones":
                # observaciones: "X días"
                try:
                    dias = int(evento[2].split()[0])
                except:
                    dias = 0
                inicio = int(evento[1])
                ahora = int(time.time())
                if dias > 0 and ahora < inicio + dias * 86400:
                    estado_item = QTableWidgetItem("🔴 Inactivo (Vacaciones)")
                    estado_item.setForeground(Qt.red)
            if not estado_item:
                estado_item = QTableWidgetItem("🟢 Activo")
                estado_item.setForeground(Qt.green)
            self.table.setItem(row_num, 6, estado_item)
            # Botón de acciones con estilo coherente
            btn_acciones = QPushButton("Opciones")
            btn_acciones.setStyleSheet("padding:6px 10px; border-radius:8px;")
            # Conectar acciones via menú (mantener funcionalidad)
            menu = QMenu()
            action_baja = QAction("Dar de baja", btn_acciones)
            action_baja.triggered.connect(partial(self.dar_de_baja, empleado[1])) # CI
            menu.addAction(action_baja)
            action_editar = QAction("Modificar", btn_acciones)
            action_editar.triggered.connect(partial(self.modificar_empleado, empleado[0])) # ID
            menu.addAction(action_editar)
            action_vacaciones = QAction("Dar vacaciones", btn_acciones)
            action_vacaciones.triggered.connect(partial(self.dar_vacaciones, empleado[1])) # CI
            menu.addAction(action_vacaciones)
            action_reincorporar = QAction("Reincorporar", btn_acciones)
            action_reincorporar.triggered.connect(partial(self.reincorporar_empleado, empleado[1])) # CI
            menu.addAction(action_reincorporar)
            btn_acciones.setMenu(menu)
            action_layout = QHBoxLayout()
            action_layout.addWidget(btn_acciones)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row_num, 7, action_widget)

    def reincorporar_empleado(self, ci):
        # Obtener nombre, apellidos y celular del empleado
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, apellidos, celular FROM empleado WHERE CI = ?", (ci,))
        datos = cursor.fetchone()
        nombre, apellidos, celular = datos if datos else ("", "", "")
        conn.close()
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout
        class ReincorporarDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Registrar reincorporación")
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"Motivo de reincorporación para CI: {ci}"))
                self.motivo_input = QLineEdit()
                self.motivo_input.setPlaceholderText("Motivo de reincorporación")
                layout.addWidget(self.motivo_input)
                self.obs_input = QTextEdit()
                self.obs_input.setPlaceholderText("Observaciones (opcional)")
                layout.addWidget(self.obs_input)
                btns = QHBoxLayout()
                btn_aceptar = QPushButton("Aceptar")
                btn_cancelar = QPushButton("Cancelar")
                btn_aceptar.clicked.connect(self.accept)
                btn_cancelar.clicked.connect(self.reject)
                btns.addWidget(btn_aceptar)
                btns.addWidget(btn_cancelar)
                layout.addLayout(btns)
            def get_data(self):
                return self.motivo_input.text(), self.obs_input.toPlainText()

        dialog = ReincorporarDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            motivo, observaciones = dialog.get_data()
            if not motivo.strip():
                QMessageBox.warning(self, "Advertencia", "Debes ingresar el motivo de reincorporación.")
                return
            import time
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historial_empleado (ci_empleado, nombre, apellido, celular, tipo_evento, motivo, fecha_evento, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ci, nombre, apellidos, celular, "reincorporacion", motivo, int(time.time()), observaciones))
            conn.commit()
            conn.close()
            self.cargar_empleados()
            QMessageBox.information(self, "Reincorporación registrada", "La reincorporación fue registrada correctamente.")
    def dar_de_baja(self, ci):
        # Obtener nombre, apellidos y celular del empleado
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, apellidos, celular FROM empleado WHERE CI = ?", (ci,))
        datos = cursor.fetchone()
        nombre, apellidos, celular = datos if datos else ("", "", "")
        conn.close()
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout
        class BajaDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Registrar baja de empleado")
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"Motivo de la baja para CI: {ci}"))
                self.motivo_input = QLineEdit()
                self.motivo_input.setPlaceholderText("Motivo de la baja")
                layout.addWidget(self.motivo_input)
                layout.addWidget(QLabel("Observaciones (opcional):"))
                self.obs_input = QTextEdit()
                layout.addWidget(self.obs_input)
                btns = QHBoxLayout()
                btn_aceptar = QPushButton("Aceptar")
                btn_cancelar = QPushButton("Cancelar")
                btn_aceptar.clicked.connect(self.accept)
                btn_cancelar.clicked.connect(self.reject)
                btns.addWidget(btn_aceptar)
                btns.addWidget(btn_cancelar)
                layout.addLayout(btns)
            def get_data(self):
                return self.motivo_input.text(), self.obs_input.toPlainText()

        dialog = BajaDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            motivo, observaciones = dialog.get_data()
            if not motivo.strip():
                QMessageBox.warning(self, "Advertencia", "Debes ingresar el motivo de la baja.")
                return
            # Registrar en historial_empleado
            import time
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historial_empleado (ci_empleado, nombre, apellido, celular, tipo_evento, motivo, fecha_evento, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ci, nombre, apellidos, celular, "baja", motivo, int(time.time()), observaciones))
            conn.commit()
            conn.close()
            # Eliminar de la tabla principal y cargar empleados
            eliminar_empleado(ci)
            self.cargar_empleados()
            QMessageBox.information(self, "Baja registrada", "La baja fue registrada correctamente en el historial.")

    def dar_vacaciones(self, ci):
        # Obtener nombre, apellidos y celular del empleado
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, apellidos, celular FROM empleado WHERE CI = ?", (ci,))
        datos = cursor.fetchone()
        nombre, apellidos, celular = datos if datos else ("", "", "")
        conn.close()
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        class VacacionesDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Registrar vacaciones")
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"Cantidad de días de vacaciones para CI: {ci}"))
                self.dias_input = QLineEdit()
                self.dias_input.setPlaceholderText("Cantidad de días")
                layout.addWidget(self.dias_input)
                btns = QHBoxLayout()
                btn_aceptar = QPushButton("Aceptar")
                btn_cancelar = QPushButton("Cancelar")
                btn_aceptar.clicked.connect(self.accept)
                btn_cancelar.clicked.connect(self.reject)
                btns.addWidget(btn_aceptar)
                btns.addWidget(btn_cancelar)
                layout.addLayout(btns)
            def get_dias(self):
                return self.dias_input.text()

        dialog = VacacionesDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            dias = dialog.get_dias()
            if not dias.isdigit() or int(dias) <= 0:
                QMessageBox.warning(self, "Advertencia", "Debes ingresar una cantidad válida de días.")
                return
            # Registrar en historial_empleado
            import time
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historial_empleado (ci_empleado, nombre, apellido, celular, tipo_evento, motivo, fecha_evento, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ci, nombre, apellidos, celular, "vacaciones", "Vacaciones/Retiro", int(time.time()), f"{dias} días"))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Vacaciones registradas", f"Se registraron {dias} días de vacaciones para el empleado.")

    def buscar_empleados(self):
        """Buscar empleados en la tabla."""
        query = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            # Buscar en las columnas ID, CI, Nombre, Apellidos
            for col in range(4):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
            self.table.setRowHidden(row, not match)

    def eliminar_empleado(self, ci):
        confirmar = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar al empleado con CI {ci}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            eliminar_empleado(ci)
            self.cargar_empleados()
            
    def modificar_empleado(self, id_empleado):
        """Abre la ventana de modificación del empleado con el ID proporcionado."""
        if not id_empleado:
            QMessageBox.warning(self, "Advertencia", "No se proporcionó ID de empleado")
            return
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), "editar_empleado.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el script de modificación: {script_path}")
                return

            # Cierra la ventana actual y abre la de modificación
            self.close()
            subprocess.Popen([sys.executable, script_path, str(id_empleado)])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de modificación: {e}")

    def ir_inicio(self):
        """Ir a ventas_admin.py"""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "ventas_admin.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir ventas_admin.py: {e}")

    def insertar_empleados(self):
        # Abre el programa de insertar empleados
        abrir_aplicacion("insertar_empleado.py")
        self.close()

    def emp_eliminados(self):
        abrir_aplicacion("emp_eliminados.py")
        self.close()
    
    def menu_reportes(self):
        """Abrir el menú de reportes de empleados."""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "reporte_emp.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el menú de reportes: {e}")

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

def abrir_aplicacion(nombre_py):
    # Lógica para abrir otras aplicaciones, no la del mismo archivo
    try:
        script_path = os.path.join(os.path.dirname(__file__), nombre_py)
        subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        QMessageBox.critical(None, "Error", f"No se pudo abrir el archivo {nombre_py}: {e}")

# Ejecutar la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VerEmpleados()
    ventana.showMaximized()
    sys.exit(app.exec_())