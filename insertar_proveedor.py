import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QWidget, QFormLayout
)
from PyQt5.QtCore import Qt
import subprocess

# ----------------- Funciones de Utilidad -----------------

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
    """Crea la tabla 'proveedores' si no existe, con la estructura proporcionada."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Estructura de la tabla 'proveedores' con nombres de columna corregidos
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
    """
    Abre el archivo .exe si existe, si no, ejecuta el .py en un nuevo proceso.
    """
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


# ----------------- Ventana Principal -----------------

class InsertarProveedorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Insertar Nuevo Proveedor")
        self.setGeometry(100, 100, 500, 400)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 13px;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 3px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #aaa;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                min-width: 80px;
            }
            #title {
                font-size: 18px;
                font-weight: bold;
                background-color: #e0e0e0;
                padding: 10px;
                text-align: center;
            }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        title = QLabel("Insertar Nuevo Proveedor")
        title.setObjectName("title")
        main_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(30, 20, 30, 20)

        self.campos = {}

        self.campos["nombre_proveedor"] = QLineEdit()
        self.campos["nombre_proveedor"].setPlaceholderText("Ej: Laboratorios Unidos S.A.")
        form_layout.addRow("Nombre del Proveedor:", self.campos["nombre_proveedor"])

        self.campos["nit_ruc"] = QLineEdit()
        self.campos["nit_ruc"].setPlaceholderText("Ej: 123456789-0")
        form_layout.addRow("NIT/RUC:", self.campos["nit_ruc"])

        self.campos["nombre_contacto"] = QLineEdit()
        self.campos["nombre_contacto"].setPlaceholderText("Ej: Juan Pérez")
        form_layout.addRow("Nombre del Contacto:", self.campos["nombre_contacto"])

        self.campos["telefono"] = QLineEdit()
        self.campos["telefono"].setPlaceholderText("Ej: +591 71234567")
        form_layout.addRow("Teléfono:", self.campos["telefono"])

        self.campos["correo"] = QLineEdit()
        self.campos["correo"].setPlaceholderText("Ej: contacto@proveedor.com")
        form_layout.addRow("Correo Electrónico:", self.campos["correo"])
        
        self.campos["direccion"] = QLineEdit()
        self.campos["direccion"].setPlaceholderText("Ej: Av. Principal 123, La Paz")
        form_layout.addRow("Dirección:", self.campos["direccion"])

        main_layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Proveedor")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_guardar.clicked.connect(self.guardar_proveedor)
        buttons_layout.addWidget(btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setStyleSheet("background-color: #f39c12; color: white;")
        btn_limpiar.clicked.connect(self.limpiar_formulario)
        buttons_layout.addWidget(btn_limpiar)

        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #95a5a6; color: white;")
        # Aquí puedes conectar el botón a la ventana principal de tu aplicación
        # btn_volver.clicked.connect(self.volver_a_principal)
        buttons_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; padding: 8px 15px; border-radius: 5px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        buttons_layout.addWidget(btn_menu)

        main_layout.addLayout(buttons_layout)

    def guardar_proveedor(self):
        # Obtener datos del formulario
        nombre_proveedor = self.campos["nombre_proveedor"].text().strip()
        nit_ruc = self.campos["nit_ruc"].text().strip()
        nombre_contacto = self.campos["nombre_contacto"].text().strip()
        telefono = self.campos["telefono"].text().strip()
        correo = self.campos["correo"].text().strip()
        direccion = self.campos["direccion"].text().strip()

        # Validaciones
        if not nombre_proveedor or not telefono or not correo:
            QMessageBox.warning(self, "Advertencia", "Los campos Nombre del Proveedor, Teléfono y Correo Electrónico son obligatorios.")
            return

        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insertar en la tabla 'proveedores' con los nombres de columna corregidos
            cursor.execute("""
                INSERT INTO proveedores (
                    nombre_proveedor, nit_ruc, nombre_contacto, telefono, correo, direccion
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                nombre_proveedor,
                nit_ruc,
                nombre_contacto,
                telefono,
                correo,
                direccion
            ))
            conn.commit()

            QMessageBox.information(self, "Éxito", "Proveedor guardado correctamente")
            self.limpiar_formulario()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Advertencia", "El proveedor, NIT/RUC o correo electrónico ya existe. Ingrese datos diferentes.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo guardar el proveedor: {e}")
        finally:
            if conn:
                conn.close()

    def limpiar_formulario(self):
        for campo in self.campos.values():
            campo.clear()
        self.campos["nombre_proveedor"].setFocus()
    
    def volver_a_principal(self):
        self.close()

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
    crear_tabla_proveedores() # Llama a esta función para asegurar que la tabla exista
    app = QApplication(sys.argv)
    window = InsertarProveedorWindow()
    window.show()
    sys.exit(app.exec_())