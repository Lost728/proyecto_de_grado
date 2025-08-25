import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QMessageBox
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
        cursor.execute("SELECT id_empleado, CI, nombre, celular, rol, fecha_creacion FROM empleado WHERE CI = ?", (ci,))
        empleado = cursor.fetchone()
        
        if empleado:
            cursor.execute("""
                INSERT INTO empleados_eliminados 
                (id_empleado, ci, nombre, celular, rol, fecha_creacion, fecha_borrado)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (empleado[0], empleado[1], empleado[2], empleado[3], empleado[4], empleado[5]))
            
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
        self.setGeometry(100, 100, 1100, 600)  # Más ancho para la columna extra

        # Layout principal
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)

        # Barra de navegación
        nav_layout = QHBoxLayout()
        btn_inicio = QPushButton("Ventas")
        btn_inicio.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_inicio.clicked.connect(self.ir_inicio)
        nav_layout.addWidget(btn_inicio)

        btn_insertar = QPushButton("Insertar Empleados")
        btn_insertar.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_insertar.clicked.connect(self.insertar_empleados)
        nav_layout.addWidget(btn_insertar)
        
        btn_emp_eliminados = QPushButton("Empleados Eliminados")
        btn_emp_eliminados.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_emp_eliminados.clicked.connect(self.emp_eliminados)
        nav_layout.addWidget(btn_emp_eliminados)

        btn_reportes = QPushButton("Menú de Reportes")
        btn_reportes.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_reportes.clicked.connect(self.menu_reportes)
        nav_layout.addWidget(btn_reportes)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; font-size: 14px;")
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
        btn_buscar.setStyleSheet("background-color: #32CD32; font-size: 14px;")
        btn_buscar.clicked.connect(self.buscar_empleados)
        search_layout.addWidget(btn_buscar)
        main_layout.addLayout(search_layout)

        # Tabla de empleados (ahora con 7 columnas)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "CI", "Nombre", "Apellidos", "Celular", "Rol", "Acciones"])
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

        for row_num, empleado in enumerate(empleados):
            self.table.insertRow(row_num)
            # id_empleado, CI, nombre, apellidos, celular, rol, fecha_creacion
            self.table.setItem(row_num, 0, QTableWidgetItem(str(empleado[0])))  # ID
            self.table.setItem(row_num, 1, QTableWidgetItem(str(empleado[1])))  # CI
            self.table.setItem(row_num, 2, QTableWidgetItem(str(empleado[2])))  # Nombre
            self.table.setItem(row_num, 3, QTableWidgetItem(str(empleado[3])))  # Apellidos
            self.table.setItem(row_num, 4, QTableWidgetItem(str(empleado[4])))  # Celular
            self.table.setItem(row_num, 5, QTableWidgetItem(str(empleado[5])))  # Rol

            # Botones de acciones
            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setStyleSheet("background-color: #FF6347; color: white;")
            btn_eliminar.clicked.connect(partial(self.eliminar_empleado, empleado[1])) # Usa el CI para eliminar

            btn_modificar = QPushButton("Modificar")
            btn_modificar.setStyleSheet("background-color: #1E90FF; color: white;")
            btn_modificar.clicked.connect(partial(self.modificar_empleado, empleado[0])) # Usa el ID para modificar

            action_layout = QHBoxLayout()
            action_layout.addWidget(btn_eliminar)
            action_layout.addWidget(btn_modificar)

            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row_num, 6, action_widget)

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
            script_path = os.path.join(os.path.dirname(__file__), "modificar_empleado.py")
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