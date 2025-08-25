import subprocess
import sys
import sqlite3
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QMessageBox, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from datetime import datetime

def obtener_db_path():
    if getattr(sys, 'frozen', False):
        # Carpeta donde está el ejecutable
        exe_dir = os.path.dirname(sys.executable)
        db_path = os.path.join(exe_dir, "pruebas.db")  # Cambiado a pruebas.db
        if os.path.exists(db_path):
            return db_path
        # Si no está, busca en la carpeta temporal de PyInstaller
        base_path = sys._MEIPASS
        return os.path.join(base_path, "pruebas.db")
    else:
        # En desarrollo, busca en la carpeta original
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "pruebas.db"))  # Cambiado a pruebas.db

db_path = obtener_db_path()
print("Conexión exitosa a la base de datos:", db_path)
print("¿Existe?", os.path.exists(db_path))

class ProductosEliminadosWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Productos Eliminados")
        self.setGeometry(100, 100, 1200, 500)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        label = QLabel("Productos Eliminados")
        label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(label)

        btn_volver = QPushButton("Volver atrás")
        btn_volver.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold;")
        btn_volver.clicked.connect(self.volver_atras)
        main_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        main_layout.addWidget(btn_menu)

        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.clicked.connect(self.cargar_productos)
        main_layout.addWidget(btn_actualizar)

        # Buscador
        buscador_layout = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o código...")
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar_productos)
        buscador_layout.addWidget(self.input_busqueda)
        buscador_layout.addWidget(btn_buscar)
        main_layout.addLayout(buscador_layout)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Código", "Imagen", "Nombre", "Precio", "Stock", "Fecha Venc.", "ID Empleado", "Acciones"
        ])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.tabla)

        self.cargar_productos()

        self.input_busqueda.returnPressed.connect(self.buscar_productos)

    def cargar_productos(self, filtro=""):
        self.tabla.setRowCount(0)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if filtro:
                cursor.execute("""
                    SELECT id_producto, codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado
                    FROM productos_borrados
                    WHERE nombre LIKE ? OR codigo LIKE ?
                    ORDER BY id_producto DESC
                """, (f"%{filtro}%", f"%{filtro}%"))
            else:
                cursor.execute("""
                    SELECT id_producto, codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado
                    FROM productos_borrados
                    ORDER BY id_producto DESC
                """)
            productos = cursor.fetchall()
            conn.close()

            for row_num, row_data in enumerate(productos):
                self.tabla.insertRow(row_num)
                for col_num, data in enumerate(row_data):
                    # Formatear fecha_venc si es timestamp
                    if col_num == 6 and data:
                        try:
                            fecha = datetime.fromtimestamp(int(data)).strftime("%Y-%m-%d")
                        except Exception:
                            fecha = str(data)
                        item = QTableWidgetItem(fecha)
                    else:
                        item = QTableWidgetItem(str(data) if data is not None else "")
                    self.tabla.setItem(row_num, col_num, item)

                # Columna de acciones
                acciones_widget = QWidget()
                acciones_layout = QHBoxLayout()
                acciones_layout.setContentsMargins(0, 0, 0, 0)

                btn_restaurar = QPushButton("Restaurar")
                btn_restaurar.setStyleSheet("background-color: #4CAF50; color: white;")
                btn_restaurar.clicked.connect(lambda _, rid=row_data[0]: self.restaurar_producto(rid))
                acciones_layout.addWidget(btn_restaurar)

                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setStyleSheet("background-color: #e53935; color: white;")
                btn_eliminar.clicked.connect(lambda _, rid=row_data[0]: self.eliminar_producto(rid))
                acciones_layout.addWidget(btn_eliminar)

                acciones_widget.setLayout(acciones_layout)
                self.tabla.setCellWidget(row_num, 8, acciones_widget)
        except Exception as e:
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(1)
            self.tabla.setHorizontalHeaderLabels(["Error"])
            self.tabla.insertRow(0)
            self.tabla.setItem(0, 0, QTableWidgetItem(f"Error al cargar productos: {e}"))

    def buscar_productos(self):
        texto = self.input_busqueda.text().strip()
        self.cargar_productos(filtro=texto)

    def restaurar_producto(self, producto_id):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Recuperar datos del producto eliminado
            cursor.execute("""
                SELECT codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado
                FROM productos_borrados WHERE id_producto = ?
            """, (producto_id,))
            producto = cursor.fetchone()
            if producto:
                codigo_actual, imagen, nombre, precio, stock, fecha_venc, id_empleado = producto

                while True:
                    # Pedir al usuario el nuevo código (o dejar el mismo)
                    nuevo_codigo, ok = QInputDialog.getText(
                        self,
                        "Reasignar Código",
                        f"Ingrese el nuevo código para el producto '{nombre}':",
                        text=str(codigo_actual)
                    )
                    if not ok or not nuevo_codigo.strip():
                        QMessageBox.information(self, "Cancelado", "Restauración cancelada.")
                        conn.close()
                        return

                    # Verificar si ya existe un producto con el nuevo código
                    cursor.execute("SELECT id_producto FROM productos WHERE codigo = ?", (nuevo_codigo,))
                    existente = cursor.fetchone()
                    if existente:
                        QMessageBox.warning(
                            self,
                            "Código existente",
                            f"Ya existe un producto con el código '{nuevo_codigo}'.\nPor favor, ingresa un código diferente."
                        )
                        # Vuelve a pedir el código
                        continue
                    else:
                        # Código único, proceder a restaurar
                        cursor.execute("""
                            INSERT INTO productos (codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (nuevo_codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado))
                        # Eliminar de productos_borrados
                        cursor.execute("DELETE FROM productos_borrados WHERE id_producto = ?", (producto_id,))
                        conn.commit()
                        QMessageBox.information(self, "Restaurado", f"Producto restaurado correctamente con código '{nuevo_codigo}'.")
                        break
            else:
                QMessageBox.warning(self, "No encontrado", "No se encontró el producto para restaurar.")
            conn.close()
            self.cargar_productos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo restaurar el producto: {e}")

    def eliminar_producto(self, producto_id):
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Seguro que quiere retirar este producto permanentemente?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM productos_borrados WHERE id_producto = ?", (producto_id,))
                conn.commit()
                QMessageBox.information(self, "Eliminado", "Producto eliminado permanentemente de eliminados.")
                self.cargar_productos()
                conn.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar producto: {e}")

    def volver_atras(self):
        import subprocess
        import sys
        import os
        ruta = os.path.join(os.path.dirname(__file__), "ver_productos.py")
        subprocess.Popen([sys.executable, ruta])
        self.close()

    def volver_a_lista(self):
        """Cierra la ventana y vuelve a la lista de productos"""
        abrir_aplicacion("ver_productos.py")
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

def abrir_aplicacion(nombre_py):
    """
    Abre el archivo .exe si existe, si no, ejecuta el .py en un nuevo proceso.
    Busca primero en la carpeta temporal (_MEIPASS), luego en la carpeta del ejecutable.
    """
    rutas = []
    # Carpeta temporal de PyInstaller
    if hasattr(sys, '_MEIPASS'):
        rutas.append(sys._MEIPASS)
    # Carpeta donde está el ejecutable principal
    rutas.append(os.path.dirname(sys.executable))

    exe_name = nombre_py.replace('.py', '.exe')

    for base_path in rutas:
        exe_path = os.path.join(base_path, exe_name)
        py_path = os.path.join(base_path, nombre_py)
        if os.path.exists(exe_path):
            try:
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen([exe_path], startupinfo=startupinfo)
                else:
                    subprocess.Popen([exe_path])
                return
            except Exception as e:
                QMessageBox.critical(None, "❌ Error", f"No se pudo abrir el ejecutable:\n{e}")
                return
        elif os.path.exists(py_path):
            try:
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen([sys.executable, py_path], startupinfo=startupinfo)
                else:
                    subprocess.Popen([sys.executable, py_path])
                return
            except Exception as e:
                QMessageBox.critical(None, "❌ Error", f"No se pudo abrir el script:\n{e}")
                return

    QMessageBox.warning(None, "⚠️ Archivo no encontrado",
                        f"No se encontró el archivo:\n{exe_name} ni {nombre_py}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProductosEliminadosWindow()
    window.showMaximized()
    sys.exit(app.exec_())