import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime
import subprocess

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

def crear_tabla_proveedores():
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id_proveedor INTEGER PRIMARY KEY,
                nombre_proveedor TEXT NOT NULL UNIQUE,
                nit_ruc TEXT UNIQUE,
                nombre_contacto TEXT,
                telefono TEXT NOT NULL,
                correo TEXT NOT NULL,
                direccion TEXT,
                estado TEXT DEFAULT 'activo',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("Tabla 'proveedores' verificada/creada correctamente.")
        
    except sqlite3.Error as e:
        print(f"Error al crear la tabla 'proveedores': {e}")
    finally:
        if conn:
            conn.close()

def abrir_aplicacion(nombre_py):
    rutas = []
    if hasattr(sys, '_MEIPASS'):
        rutas.append(sys._MEIPASS)
    rutas.append(os.path.dirname(sys.executable))

    exe_name = nombre_py.replace('.py', '.exe')

    for base_path in rutas:
        exe_path = os.path.join(base_path, exe_name)
        py_path = os.path.join(base_path, nombre_py)
        if os.path.exists(exe_path):
            try:
                cmd = [exe_path]
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen(cmd, startupinfo=startupinfo)
                else:
                    subprocess.Popen(cmd)
                return
            except Exception as e:
                QMessageBox.critical(None, "❌ Error", f"No se pudo abrir el ejecutable:\n{e}")
                return
        elif os.path.exists(py_path):
            try:
                cmd = [sys.executable, py_path]
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen(cmd, startupinfo=startupinfo)
                else:
                    subprocess.Popen(cmd)
                return
            except Exception as e:
                QMessageBox.critical(None, "❌ Error", f"No se pudo abrir el script:\n{e}")
                return

    QMessageBox.warning(None, "⚠️ Archivo no encontrado",
                        f"No se encontró el archivo:\n{exe_name} ni {nombre_py}")

class VerProveedoresWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ver Proveedores")
        self.setGeometry(100, 100, 1200, 600)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 13px;
            }
            #title {
                font-size: 20px;
                font-weight: bold;
                background-color: #e0e0e0;
                padding: 10px;
                text-align: center;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                min-width: 80px;
            }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        title = QLabel("Lista de Proveedores")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Botones
        buttons_layout = QHBoxLayout()
        btn_nuevo_proveedor = QPushButton("Añadir Nuevo Proveedor")
        btn_nuevo_proveedor.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_nuevo_proveedor.clicked.connect(lambda: abrir_aplicacion("insertar_proveedor.py")) 
        buttons_layout.addWidget(btn_nuevo_proveedor)

        btn_refrescar = QPushButton("Actualizar")
        btn_refrescar.setStyleSheet("background-color: #388e3c; color: white;")
        btn_refrescar.clicked.connect(self.cargar_proveedores)
        buttons_layout.addWidget(btn_refrescar)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        buttons_layout.addWidget(btn_menu)

        main_layout.addLayout(buttons_layout)

        # Tabla de datos
        self.tabla_proveedores = QTableWidget()
        self.tabla_proveedores.setColumnCount(8)
        self.tabla_proveedores.setHorizontalHeaderLabels([
            "ID", "Nombre Proveedor", "NIT/RUC", "Nombre Contacto", 
            "Teléfono", "Correo", "Dirección", "Fecha de Registro"
        ])
        self.tabla_proveedores.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_proveedores.setEditTriggers(QTableWidget.NoEditTriggers) # No se puede editar la tabla
        self.tabla_proveedores.setSortingEnabled(True) # Habilitar ordenamiento

        main_layout.addWidget(self.tabla_proveedores)

        self.cargar_proveedores()

    def cargar_proveedores(self):
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Consulta para obtener todos los proveedores
            cursor.execute("""
                SELECT 
                    id_proveedor,
                    nombre_proveedor,
                    nit_ruc,
                    nombre_contacto,
                    telefono,
                    correo,
                    direccion,
                    fecha_registro
                FROM proveedores
                ORDER BY nombre_proveedor ASC;
            """)
            
            proveedores = cursor.fetchall()
            
            self.tabla_proveedores.setRowCount(len(proveedores))
            
            for fila_index, proveedor in enumerate(proveedores):
                for col_index, valor in enumerate(proveedor):
                    valor_formateado = str(valor) if valor is not None else ""
                    
                    # Formatear la fecha de registro
                    if col_index == 7: # Columna 'fecha_registro'
                        valor_formateado = datetime.strptime(str(valor), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

                    self.tabla_proveedores.setItem(fila_index, col_index, QTableWidgetItem(valor_formateado))
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo cargar la información de proveedores: {e}")
        finally:
            if conn:
                conn.close()
                
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
    crear_tabla_proveedores()
    app = QApplication(sys.argv)
    window = VerProveedoresWindow()
    window.showMaximized()
    sys.exit(app.exec_())