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

def crear_tablas_necesarias():
    """Crea las tablas productos, lotes y proveedores si no existen."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Estructura de la tabla 'productos' (según la información que proporcionaste)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id_producto INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                imagen TEXT NOT NULL,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                "fecha_venc" INTEGER NOT NULL,
                id_empleado INTEGER,
                FOREIGN KEY(id_empleado) REFERENCES empleado(CI)
            );
        """)

        # Estructura de la tabla 'proveedores'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id_proveedor INTEGER PRIMARY KEY,
                nombre_proveedor TEXT NOT NULL UNIQUE,
                "nit ruc" TEXT UNIQUE,
                "nombre contacto" TEXT,
                telefono TEXT NOT NULL,
                correo TEXT NOT NULL,
                direccion TEXT,
                estado TEXT DEFAULT 'activo' CHECK(estado IN ('activo', 'inactivo')),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Estructura de la tabla 'lotes'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lotes (
                id_lote INTEGER PRIMARY KEY,
                id_producto INTEGER NOT NULL,
                codigo_lote TEXT NOT NULL UNIQUE,
                cantidad INTEGER NOT NULL,
                "fecha_entrada" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "fecha_vencimiento" INTEGER NOT NULL,
                precio_costo REAL,
                id_proveedor INTEGER,
                FOREIGN KEY(id_producto) REFERENCES productos(id_producto),
                FOREIGN KEY(id_proveedor) REFERENCES proveedores(id_proveedor)
            );
        """)
        
        conn.commit()
        print("Tablas verificadas/creadas correctamente.")
        
    except sqlite3.Error as e:
        print(f"Error al crear tablas: {e}")
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

class VerLotesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ver Lotes")
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
        self.main_layout = QVBoxLayout()
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)

        title = QLabel("Inventario por Lotes")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title)

        # Botones
        buttons_layout = QHBoxLayout()
        btn_nuevo_lote = QPushButton("Añadir Nuevo Lote")
        btn_nuevo_lote.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_nuevo_lote.clicked.connect(self.abrir_insertar_lote)
        buttons_layout.addWidget(btn_nuevo_lote)

        btn_refrescar = QPushButton("Actualizar")
        btn_refrescar.setStyleSheet("background-color: #388e3c; color: white;")
        btn_refrescar.clicked.connect(self.cargar_lotes)
        buttons_layout.addWidget(btn_refrescar)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        buttons_layout.addWidget(btn_menu)

        self.main_layout.addLayout(buttons_layout)

        # Tabla de datos
        self.tabla_lotes = QTableWidget()
        self.tabla_lotes.setColumnCount(8)
        self.tabla_lotes.setHorizontalHeaderLabels([
            "ID Lote", "ID Producto", "Código Lote", "Cantidad", "Fecha Entrada", "Fecha Vencimiento", "Precio Costo", "ID Proveedor"
        ])
        self.tabla_lotes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_lotes.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_lotes.setSortingEnabled(True)

        self.main_layout.addWidget(self.tabla_lotes)

        self.cargar_lotes()

    def abrir_insertar_lote(self):
        try:
            from insertar_lotes import InsertarLoteWindow
        except ImportError:
            QMessageBox.critical(self, "Error", "No se pudo importar la ventana para insertar lotes.")
            return
        self.insertar_lote_window = InsertarLoteWindow()
        self.insertar_lote_window.show()
        self.close()

    def cargar_lotes(self):
        """Carga los datos de los lotes desde la base de datos."""
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_lote, id_producto, codigo_lote, cantidad, fecha_entrada, fecha_vencimiento, precio_costo, id_proveedor
                FROM lotes
                ORDER BY fecha_vencimiento ASC;
            """)
            lotes = cursor.fetchall()
            self.tabla_lotes.setRowCount(len(lotes))
            for fila_index, lote in enumerate(lotes):
                for col_index, valor in enumerate(lote):
                    # Formatear fechas para mejor visualización
                    if col_index == 4:  # Fecha de Entrada
                        try:
                            valor_formateado = datetime.strptime(str(valor), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                        except Exception:
                            valor_formateado = str(valor)
                    elif col_index == 5:  # Fecha de Vencimiento
                        try:
                            valor_formateado = datetime.fromtimestamp(int(valor)).strftime('%d/%m/%Y')
                        except Exception:
                            valor_formateado = str(valor)
                        # Resaltar lotes que están cerca de vencer (90 días)
                        try:
                            if (datetime.fromtimestamp(int(valor)).date() - datetime.now().date()).days < 90:
                                item = QTableWidgetItem(valor_formateado)
                                item.setBackground(Qt.yellow)
                                self.tabla_lotes.setItem(fila_index, col_index, item)
                                continue
                        except Exception:
                            pass
                    else:
                        valor_formateado = str(valor) if valor is not None else ""
                    self.tabla_lotes.setItem(fila_index, col_index, QTableWidgetItem(valor_formateado))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo cargar la información de lotes: {e}")
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
    crear_tablas_necesarias()
    app = QApplication(sys.argv)
    window = VerLotesWindow()
    window.showMaximized()
    sys.exit(app.exec_())