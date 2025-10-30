import subprocess
import sys
import sqlite3
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QMessageBox, QInputDialog, QLineEdit, QGraphicsBlurEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
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

# Estilos generales reutilizables jondo
ESTILOS_APP = {
    "ventana_fondo": "background: #6a1b9a;",
    "tabla": """
        QTableWidget {
            background: transparent;
            color: #E3F6FF;
            border: none;
        }
        QTableWidget::item {
            background: transparent;
            color: #E3F6FF;
        }
        QTableWidget::item:selected {
            background: rgba(74,208,255,0.12);
        }
        QHeaderView::section {
            background: rgba(106,27,154,0.45);
            color: #AEEFFF;
            border: none;
            padding: 6px;
        }
    """,
    "boton_principal": """
        QPushButton {
            background-color: #4AD0FF;
            color: #311b92;
            font-weight: bold;
            padding: 8px 15px;
            border-radius: 10px;
            font-size: 15px;
        }
        QPushButton:hover {
            background-color: #6DE0FF;
        }
    """,
    "boton_peligro": "background-color: #e53935; color: white; border-radius: 8px; font-weight: bold;",
    "boton_exito": "background-color: #4CAF50; color: white; border-radius: 8px; font-weight: bold;"
}
class ProductosEliminadosWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Productos Eliminados")
            # Fondo gradiente púrpura-azul
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #6a1b9a, stop:0.5 #1976d2, stop:1 #00bcd4);
                }
            """)

            main_widget = QWidget()
            main_layout = QVBoxLayout()
            main_widget.setLayout(main_layout)
            main_widget.setStyleSheet("background: rgba(255,255,255,0.18); border-radius: 18px;")
            self.setCentralWidget(main_widget)

            # Título moderno
            label = QLabel("Productos Eliminados")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                "font-size: 38px; font-weight: bold; padding: 18px 0; margin-bottom: 18px; "
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6a1b9a, stop:0.5 #1976d2, stop:1 #00bcd4); "
                "color: white; border-radius: 18px; "
            )
            main_layout.addWidget(label)

            # Botones principales
            btn_layout = QHBoxLayout()
            btn_style = (
                "QPushButton {background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4AD0FF, stop:1 #AEEFFF); "
                "color: #311b92; font-weight: bold; border-radius: 12px; padding: 8px 0; font-size: 16px;} "
                "QPushButton:hover {background: #81d4fa;} "
                "QPushButton:pressed {background: #039be5;}"
            )
            btn_volver = QPushButton("Volver atrás")
            btn_volver.setFixedWidth(160)
            btn_volver.setStyleSheet(btn_style)
            btn_volver.clicked.connect(self.volver_atras)
            btn_layout.addWidget(btn_volver)

            btn_menu = QPushButton("Menú Principal")
            btn_menu.setFixedWidth(160)
            btn_menu.setStyleSheet(btn_style)
            btn_menu.clicked.connect(self.ir_menu_principal)
            btn_layout.addWidget(btn_menu)

            btn_actualizar = QPushButton("Actualizar")
            btn_actualizar.setFixedWidth(160)
            btn_actualizar.setStyleSheet(btn_style)
            btn_actualizar.clicked.connect(self.cargar_productos)
            btn_layout.addWidget(btn_actualizar)

            main_layout.addLayout(btn_layout)

            # Buscador
            buscador_layout = QHBoxLayout()
            self.input_busqueda = QLineEdit()
            self.input_busqueda.setPlaceholderText("Buscar por nombre o código...")
            self.input_busqueda.setStyleSheet(
                "QLineEdit {font-size: 16px; border-radius: 8px; padding: 6px 12px; border: 2px solid #6a1b9a;}"
            )
            btn_buscar = QPushButton("Buscar")
            btn_buscar.setFixedWidth(120)
            btn_buscar.setStyleSheet(btn_style)
            btn_buscar.clicked.connect(self.buscar_productos)
            buscador_layout.addWidget(self.input_busqueda)
            buscador_layout.addWidget(btn_buscar)
            main_layout.addLayout(buscador_layout)

            # Tabla moderna y transparente
            self.tabla = QTableWidget()
            self.tabla.setColumnCount(9)
            self.tabla.setHorizontalHeaderLabels([
                "ID Borrado", "ID Producto", "Código", "Nombre", "Precio", "Stock",
                "Fecha Venc.", "Fecha Eliminación", "Acciones"
            ])
            self.tabla.horizontalHeader().setStretchLastSection(True)
            self.tabla.setStyleSheet(
                "QTableWidget { background: transparent; color: #311b92; border: none; } "
                "QTableWidget::item { background: transparent; color: #311b92; } "
                "QTableWidget::item:selected { background: rgba(74,208,255,0.12); } "
                "QHeaderView::section { background: rgba(106,27,154,0.45); color: #AEEFFF; border: none; padding: 6px; } "
            )
            main_layout.addWidget(self.tabla)

            self.input_busqueda.returnPressed.connect(self.buscar_productos)
            self.cargar_productos()
    
        def cargar_productos(self, filtro=""):
            self.tabla.setRowCount(0)
            try:
                db_path = obtener_db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                if filtro:
                    cursor.execute("""
                        SELECT id_borrado, id_producto, codigo, nombre, precio, stock, fecha_venc, fecha_eliminacion
                        FROM productos_borrados
                        WHERE nombre LIKE ? OR codigo LIKE ?
                        ORDER BY fecha_eliminacion DESC
                    """, (f"%{filtro}%", f"%{filtro}%"))
                else:
                    cursor.execute("""
                        SELECT id_borrado, id_producto, codigo, nombre, precio, stock, fecha_venc, fecha_eliminacion
                        FROM productos_borrados
                        ORDER BY fecha_eliminacion DESC
                    """)
                productos = cursor.fetchall()
                conn.close()
    
                for row_num, row_data in enumerate(productos):
                    self.tabla.insertRow(row_num)
                    (id_borrado, id_producto, codigo, nombre, precio, stock, fecha_venc, fecha_eliminacion) = row_data
    
                    self.tabla.setItem(row_num, 0, QTableWidgetItem(str(id_borrado)))
                    self.tabla.setItem(row_num, 1, QTableWidgetItem(str(id_producto)))
                    self.tabla.setItem(row_num, 2, QTableWidgetItem(str(codigo)))
                    self.tabla.setItem(row_num, 3, QTableWidgetItem(str(nombre)))
                    self.tabla.setItem(row_num, 4, QTableWidgetItem(f"{precio:.2f}"))
                    self.tabla.setItem(row_num, 5, QTableWidgetItem(str(stock)))
    
                    if fecha_venc:
                        try:
                            fecha = datetime.fromtimestamp(int(fecha_venc)).strftime("%Y-%m-%d")
                        except Exception:
                            fecha = str(fecha_venc)
                        self.tabla.setItem(row_num, 6, QTableWidgetItem(fecha))
                    else:
                        self.tabla.setItem(row_num, 6, QTableWidgetItem(""))
                    
                    if fecha_eliminacion:
                        try:
                            self.tabla.setItem(row_num, 7, QTableWidgetItem(str(fecha_eliminacion)))
                        except Exception:
                            self.tabla.setItem(row_num, 7, QTableWidgetItem(str(fecha_eliminacion)))
                    else:
                        self.tabla.setItem(row_num, 7, QTableWidgetItem(""))
    
                    # Columna de acciones: solo un botón 'Funciones'
                    acciones_widget = QWidget()
                    acciones_layout = QHBoxLayout()
                    acciones_layout.setContentsMargins(0, 0, 0, 0)

                    btn_funciones = QPushButton("Funciones")
                    btn_funciones.setStyleSheet(
                        "QPushButton {background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4AD0FF, stop:1 #AEEFFF); "
                        "color: #311b92; font-weight: bold; border-radius: 12px; padding: 8px 0; font-size: 16px;} "
                        "QPushButton:hover {background: #81d4fa;} "
                        "QPushButton:pressed {background: #039be5;}"
                    )
                    def mostrar_funciones():
                        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
                        dialog = QDialog(self)
                        dialog.setWindowTitle("Funciones")
                        dialog.setFixedSize(300, 180)
                        layout = QVBoxLayout()
                        label = QLabel(f"Acciones para el producto: {nombre}")
                        label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 12px;")
                        layout.addWidget(label)

                        btn_restaurar = QPushButton("Restaurar")
                        btn_restaurar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; border-radius: 8px; font-size: 15px;")
                        btn_restaurar.clicked.connect(lambda: (self.restaurar_producto(id_borrado, id_producto), dialog.accept()))
                        layout.addWidget(btn_restaurar)

                        btn_eliminar = QPushButton("Eliminar")
                        btn_eliminar.setStyleSheet("background-color: #e53935; color: white; font-weight: bold; border-radius: 8px; font-size: 15px;")
                        btn_eliminar.clicked.connect(lambda: (self.eliminar_producto(id_borrado), dialog.accept()))
                        layout.addWidget(btn_eliminar)

                        dialog.setLayout(layout)
                        dialog.exec_()

                    btn_funciones.clicked.connect(mostrar_funciones)
                    acciones_layout.addWidget(btn_funciones)
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
    
        def restaurar_producto(self, borrado_id, producto_id):
            try:
                db_path = obtener_db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Recuperar datos del producto eliminado
                cursor.execute("""
                    SELECT codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado
                    FROM productos_borrados WHERE id_borrado = ?
                """, (borrado_id,))
                producto = cursor.fetchone()
                if producto:
                    (codigo_actual, imagen, nombre, precio, stock, fecha_venc, id_empleado) = producto
    
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
                                INSERT INTO productos (
                                    codigo, imagen, nombre, precio, fecha_venc, id_empleado, unidades
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                nuevo_codigo, imagen, nombre, precio, fecha_venc, id_empleado, stock
                            ))
                            # Eliminar de productos_borrados
                            cursor.execute("DELETE FROM productos_borrados WHERE id_borrado = ?", (borrado_id,))
                            conn.commit()
                            QMessageBox.information(self, "Restaurado", f"Producto restaurado correctamente con código '{nuevo_codigo}'.")
                            break
                else:
                    QMessageBox.warning(self, "No encontrado", "No se encontró el producto para restaurar.")
                conn.close()
                self.cargar_productos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al restaurar producto: {e}")
    
        def eliminar_producto(self, borrado_id):
            reply = QMessageBox.question(
                self,
                "Confirmar eliminación",
                "¿Seguro que quiere retirar este producto permanentemente?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    db_path = obtener_db_path()
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM productos_borrados WHERE id_borrado = ?", (borrado_id,))
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