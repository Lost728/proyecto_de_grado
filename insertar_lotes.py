import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QDateEdit, QWidget, QComboBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator, QIntValidator
import sqlite3
from datetime import datetime
import subprocess

def obtener_db_path():
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

def crear_tablas():
    """Crea las tablas productos, lotes y proveedores si no existen."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabla 'productos' (ajustada a un formato consistente)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id_producto INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                imagen TEXT NOT NULL,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                "fecha venc" INTEGER NOT NULL, -- Uso el nombre original de tu código
                id_empleado INTEGER,
                FOREIGN KEY(id_empleado) REFERENCES empleado(CI)
            );
        """)

        # Tabla 'lotes'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lotes (
                id_lote INTEGER PRIMARY KEY,
                id_producto INTEGER NOT NULL,
                codigo_lote TEXT NOT NULL UNIQUE,
                cantidad INTEGER NOT NULL,
                fecha_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_vencimiento INTEGER NOT NULL,
                precio_costo REAL,
                id_proveedor INTEGER,
                FOREIGN KEY(id_producto) REFERENCES productos(id_producto),
                FOREIGN KEY(id_proveedor) REFERENCES proveedores(id_proveedor)
            );
        """)
        
        # Tabla 'proveedores'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id_proveedor INTEGER PRIMARY KEY,
                nombre_proveedor TEXT NOT NULL UNIQUE,
                "nit ruc" TEXT,
                "nombre contacto" TEXT,
                telefono TEXT NOT NULL,
                correo TEXT NOT NULL,
                direccion TEXT,
                estado TEXT DEFAULT 'activo'
            );
        """)
        
        conn.commit()
        print("Tablas verificadas/creadas correctamente.")
        
    except sqlite3.Error as e:
        print(f"Error al crear tablas: {e}")
    finally:
        if conn:
            conn.close()

def verificar_tablas():
    """Función de depuración para ver las tablas existentes."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        print("Tablas existentes:")
        for tabla in tablas:
            print(f"- {tabla[0]}")
    except sqlite3.Error as e:
        print(f"Error al verificar tablas: {e}")
    finally:
        if conn:
            conn.close()

def obtener_productos():
    """Obtiene todos los productos para llenar el QComboBox de productos."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id_producto, nombre, codigo FROM productos ORDER BY nombre")
        productos = cursor.fetchall()
        return productos
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Error de DB", f"No se pudieron cargar los productos: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_proveedores():
    """Obtiene todos los proveedores para llenar el QComboBox de proveedores."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id_proveedor, nombre_proveedor FROM proveedores ORDER BY nombre_proveedor")
        proveedores = cursor.fetchall()
        return proveedores
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Error de DB", f"No se pudieron cargar los proveedores: {e}")
        return []
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

class InsertarLoteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Insertar Nuevo Lote")
        self.setGeometry(100, 100, 600, 500)
        
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
            QLineEdit, QDateEdit, QComboBox {
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

        title = QLabel("Insertar Nuevo Lote")
        title.setObjectName("title")
        main_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(30, 20, 30, 20)

        self.campos = {}

        # Campo para seleccionar el producto
        combo_producto = QComboBox()
        self.cargar_productos(combo_producto)
        form_layout.addRow("Producto:", combo_producto)
        self.campos["id_producto"] = combo_producto
        
        # Campo para seleccionar el proveedor (CAMBIO A QComboBox)
        combo_proveedor = QComboBox()
        self.cargar_proveedores(combo_proveedor)
        form_layout.addRow("Proveedor:", combo_proveedor)
        self.campos["id_proveedor"] = combo_proveedor

        self.campos["codigo_lote"] = QLineEdit()
        self.campos["codigo_lote"].setPlaceholderText("Ej: Lote-XYZ-2023")
        form_layout.addRow("Código de Lote:", self.campos["codigo_lote"])

        self.campos["cantidad"] = QLineEdit()
        self.campos["cantidad"].setPlaceholderText("Ej: 100")
        self.campos["cantidad"].setValidator(QIntValidator(0, 999999))
        form_layout.addRow("Cantidad:", self.campos["cantidad"])

        self.campos["precio_costo"] = QLineEdit()
        self.campos["precio_costo"].setPlaceholderText("Ej: 12.50")
        self.campos["precio_costo"].setValidator(QDoubleValidator(0.00, 999999.99, 2))
        form_layout.addRow("Precio de Costo (Bs.):", self.campos["precio_costo"])

        self.campos["fecha_vencimiento"] = QDateEdit()
        self.campos["fecha_vencimiento"].setCalendarPopup(True)
        self.campos["fecha_vencimiento"].setDate(QDate.currentDate().addYears(1))
        self.campos["fecha_vencimiento"].setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Fecha de Vencimiento:", self.campos["fecha_vencimiento"])
        
        main_layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Lote")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_guardar.clicked.connect(self.guardar_lote)
        buttons_layout.addWidget(btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setStyleSheet("background-color: #f39c12; color: white;")
        btn_limpiar.clicked.connect(self.limpiar_formulario)
        buttons_layout.addWidget(btn_limpiar)

        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #95a5a6; color: white;")
        btn_volver.clicked.connect(self.volver_a_lista)
        buttons_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; padding: 8px 15px; border-radius: 5px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        buttons_layout.addWidget(btn_menu)

        main_layout.addLayout(buttons_layout)
    
    def cargar_productos(self, combo_box):
        productos = obtener_productos()
        if productos:
            for id_prod, nombre, codigo in productos:
                combo_box.addItem(f"{nombre} ({codigo})", id_prod)
        else:
            combo_box.addItem("No hay productos disponibles", -1)
            combo_box.setEnabled(False)

    def cargar_proveedores(self, combo_box):
        proveedores = obtener_proveedores()
        if proveedores:
            for id_prov, nombre_prov in proveedores:
                combo_box.addItem(nombre_prov, id_prov)
        else:
            combo_box.addItem("No hay proveedores disponibles", None)
            combo_box.setEnabled(False)

    def guardar_lote(self):
        # Obtener datos del formulario
        try:
            id_producto = self.campos["id_producto"].currentData()
            if id_producto is None or id_producto == -1:
                QMessageBox.warning(self, "Advertencia", "Debe seleccionar un producto válido.")
                return

            id_proveedor = self.campos["id_proveedor"].currentData()

            codigo_lote = self.campos["codigo_lote"].text().strip()
            cantidad_str = self.campos["cantidad"].text().strip()
            precio_costo_str = self.campos["precio_costo"].text().strip()
            fecha_venc = self.campos["fecha_vencimiento"].date().toPyDate()

            # Validaciones
            if not codigo_lote or not cantidad_str or not precio_costo_str:
                QMessageBox.warning(self, "Advertencia", "Los campos Código de Lote, Cantidad y Precio de Costo son obligatorios.")
                return

            cantidad = int(cantidad_str)
            precio_costo = float(precio_costo_str)

            hoy = datetime.now().date()
            if fecha_venc < hoy:
                QMessageBox.warning(self, "Advertencia", "La fecha de vencimiento no puede ser anterior a hoy.")
                return
                
            fecha_venc_timestamp = int(datetime.combine(fecha_venc, datetime.min.time()).timestamp())

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Error de formato", f"Verifique los valores numéricos ingresados: {e}")
            return

        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insertar en la tabla 'lotes'
            cursor.execute("""
                INSERT INTO lotes (
                    id_producto, codigo_lote, cantidad, fecha_vencimiento, precio_costo, id_proveedor
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                id_producto,
                codigo_lote,
                cantidad,
                fecha_venc_timestamp,
                precio_costo,
                id_proveedor
            ))
            conn.commit()

            # Actualizar el stock del producto en la tabla 'productos'
            cursor.execute("""
                UPDATE productos SET stock = stock + ? WHERE id_producto = ?
            """, (cantidad, id_producto))
            conn.commit()

            QMessageBox.information(self, "Éxito", "Lote guardado y stock actualizado correctamente")
            self.abrir_ver_lotes()

        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Advertencia", f"Error de integridad: {e}. El código de lote podría ya existir o el proveedor no es válido.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo guardar el lote: {e}")
        finally:
            if conn:
                conn.close()

    def limpiar_formulario(self):
        self.campos["id_producto"].setCurrentIndex(0)
        self.campos["id_proveedor"].setCurrentIndex(0)
        self.campos["codigo_lote"].clear()
        self.campos["cantidad"].clear()
        self.campos["precio_costo"].clear()
        self.campos["fecha_vencimiento"].setDate(QDate.currentDate().addYears(1))
        self.campos["codigo_lote"].setFocus()

    def volver_a_lista(self):
        self.abrir_ver_lotes()

    def abrir_ver_lotes(self):
        try:
            from ver_lotes import VerLotesWindow
        except ImportError:
            QMessageBox.critical(self, "Error", "No se pudo importar la ventana de lotes.")
            self.close()
            return
        self.ver_lotes_window = VerLotesWindow()
        self.ver_lotes_window.show()
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
    crear_tablas()
    verificar_tablas()
    app = QApplication(sys.argv)
    window = InsertarLoteWindow()
    window.show()
    sys.exit(app.exec_())