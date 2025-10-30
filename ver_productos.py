import sys
import os
import sqlite3
import subprocess
from functools import partial
from datetime import datetime
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, 
    QMessageBox, QLabel, QFrame, QFileDialog, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap
import glob
import locale

# Configuración de la base de datos
DB_NAME = "pruebas.db"

# Estilo global renovado: gradiente púrpura-azul, botones azul claro y detalles modernos
APP_STYLE = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6a11cb, stop:1 #2575fc);
}

/* Hacemos el área principal levemente translúcida para que el fondo destaque */
QWidget#main_widget {
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
}

/* Inputs de búsqueda y campos */
QLineEdit {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 10px 14px;
    color: #ffffff;
    font-size: 14px;
}
QLineEdit:focus {
    border: 1px solid rgba(173, 216, 255, 0.9);
}
QLineEdit::placeholder { color: rgba(255,255,255,0.65); }

/* Botones: azul claro moderno */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #d9f3ff, stop:1 #74c0fc);
    color: #042b4f;
    border: none;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #a7e0ff, stop:1 #4dabf7);
}
QPushButton:pressed {
    transform: translateY(1px);
}

/* Tabla */
QTableWidget {
    background: transparent;
    color: #ffffff;
    gridline-color: rgba(255,255,255,0.04);
}
QTableWidget::item:selected {
    background: rgba(173, 216, 255, 0.12);
}
QHeaderView::section {
    background: rgba(0,0,0,0.18);
    color: #ffffff;
    border: none;
    padding: 8px;
}

/* Tarjetas de estadística */
QFrame#stats_card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255,255,255,0.04), stop:1 rgba(255,255,255,0.02));
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.04);
}

/* Diálogos y mensajes */
QMessageBox {
    background: rgba(0,0,0,0.35);
    color: #ffffff;
}
"""

class DatabaseManager:
    """Clase para manejar operaciones de base de datos"""
    @staticmethod
    def get_db_path():
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            db_path = os.path.join(exe_dir, DB_NAME)
            if os.path.exists(db_path):
                return db_path
            base_path = sys._MEIPASS
            return os.path.join(base_path, DB_NAME)
        else:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), DB_NAME))

    @staticmethod
    def get_products():
        """Obtiene todos los productos de la base de datos, incluyendo todas las columnas necesarias"""
        try:
            conn = sqlite3.connect(DatabaseManager.get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_producto, p.codigo, p.imagen, p.nombre, p.precio, p.fecha_venc,
                       p.id_empleado, p.unidades
                FROM productos p
            """)
            products = cursor.fetchall()
            conn.close()
            return products
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Error", f"No se pudo obtener los datos: {e}")
            return []

    @staticmethod
    def delete_product(product_id):
        """Elimina un producto y lo mueve a la tabla de eliminados"""
        try:
            conn = sqlite3.connect(DatabaseManager.get_db_path())
            cursor = conn.cursor()
            
            # Obtener el producto a eliminar con todos los datos necesarios
            cursor.execute("""
                SELECT id_producto, codigo, imagen, nombre, precio, fecha_venc, id_empleado, unidades
                FROM productos WHERE id_producto = ?
            """, (product_id,))
            product = cursor.fetchone()
            
            if product:
                # Desempacar los valores
                id_producto, codigo, imagen, nombre, precio, fecha_venc, id_empleado, unidades = product
                
                # Insertar en la tabla productos_borrados con la estructura correcta
                cursor.execute("""
                    INSERT INTO productos_borrados (
                        id_producto, codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_producto, codigo, imagen, nombre, precio, unidades, fecha_venc, id_empleado))
                
                # Eliminar de la tabla principal
                cursor.execute("DELETE FROM productos WHERE id_producto = ?", (product_id,))
                conn.commit()
                return True
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Error", f"Error al eliminar el producto: {e}")
            return False
        finally:
            if conn:
                conn.close()

class ModernButton(QPushButton):
    """Botón personalizado con apariencia moderna (ligera envoltura; estilos globales aplican la apariencia)"""
    def __init__(self, text, icon_text=""):
        super().__init__()
        self.setText(f"{icon_text} {text}" if icon_text else text)
        self.setCursor(Qt.PointingHandCursor)
        # Dejamos que el stylesheet global maneje colores y estados
        self.setObjectName('modern_button')

class SearchBox(QLineEdit):
    """Campo de búsqueda personalizado (sin estilos inline, el stylesheet global aplica)"""
    def __init__(self, placeholder="Buscar..."):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setObjectName('search_box')

class StatsCard(QFrame):
    """Tarjeta de estadísticas con diseño moderno"""
    def __init__(self, title, value, icon="📊", color="#a7e0ff"):
        super().__init__()
        self.setObjectName('stats_card')
        self._setup_ui(title, value, icon, color)
        
    def _setup_ui(self, title, value, icon, color):
        self.setFrameStyle(QFrame.NoFrame)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 22px; color: {color};")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.85); font-weight: bold;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {color};")
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(layout)

class ProductManagementWindow(QMainWindow):
    """Ventana principal de gestión de productos con estilo renovado púrpura-azul"""
    def __init__(self, empleado_actual_id):
        super().__init__()
        self.empleado_actual_id = empleado_actual_id
        self.setWindowTitle("Gestión de Productos")
        self.setGeometry(100, 100, 1100, 650)

        # Intentamos cargar un fondo si existe (imagen desenfocada para profundidad)
        fondo = os.path.abspath(os.path.join(os.path.dirname(__file__), 'image4.jpg'))
        if os.path.exists(fondo):
            self._bg_pixmap = QPixmap(fondo)
            self.bg_label = QLabel(self)
            self.bg_label.setScaledContents(True)
            # Aplicamos efecto blur mediante CSS-like (mantener simple)
            self.bg_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.bg_label.lower()

        self._setup_ui()
        self._load_products()
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self._show_cell_tooltip)

        # Aplicar estilo global a la ventana
        self.setStyleSheet(APP_STYLE)

    def _setup_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName('main_widget')
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(12)
        main_widget.setAttribute(Qt.WA_TranslucentBackground)

        # Top bar con búsqueda y botones
        self.search_input = SearchBox("Buscar por nombre, código, línea o presentación...")
        btn_search = ModernButton("Buscar")
        btn_search.clicked.connect(self._search_products)
        btn_clear = ModernButton("Limpiar")
        btn_clear.clicked.connect(self._clear_search)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(btn_search)
        top_layout.addWidget(btn_clear)
        top_layout.addStretch(1)

        # Botones principales
        btn_layout = QHBoxLayout()
        btn_menu = ModernButton("Menú Principal")
        btn_menu.clicked.connect(self.ir_menu_principal)
        btn_insert = ModernButton("Insertar")
        btn_insert.clicked.connect(self._open_insert_product)
        btn_deleted = ModernButton("Eliminados")
        btn_deleted.clicked.connect(self._open_deleted_products)
        btn_sell = ModernButton("Vender")
        btn_sell.clicked.connect(self._open_sales_admin)
        btn_refresh = ModernButton("Actualizar")
        btn_refresh.clicked.connect(self._load_products)
        btn_export = ModernButton("Exportar")
        btn_export.clicked.connect(lambda: self._export_products("xlsx"))

        for b in (btn_menu, btn_insert, btn_deleted, btn_sell, btn_refresh, btn_export):
            btn_layout.addWidget(b)

        top_bar = QHBoxLayout()
        top_bar.addLayout(top_layout)
        top_bar.addLayout(btn_layout)
        main_layout.addLayout(top_bar)

        # Tabla de productos
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Imagen", "Precio", "Unidades",
            "Fecha Venc.", "Empleado", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)

        self.setCentralWidget(main_widget)

    def resizeEvent(self, event):
        try:
            if hasattr(self, '_bg_pixmap') and self._bg_pixmap and hasattr(self, 'bg_label'):
                scaled = self._bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.bg_label.setPixmap(scaled)
                self.bg_label.resize(self.size())
                self.bg_label.lower()
        except Exception:
            pass
        return super().resizeEvent(event)

    def _load_products(self):
        products = DatabaseManager.get_products()
        self.table.setRowCount(0)
        for row_num, product in enumerate(products):
            self.table.insertRow(row_num)
            (id_producto, codigo, imagen, nombre, precio, fecha_venc, id_empleado, unidades) = product

            item0 = QTableWidgetItem(str(codigo))
            item1 = QTableWidgetItem(str(nombre))
            item2 = QTableWidgetItem(str(imagen))
            try:
                item3 = QTableWidgetItem(f"{float(precio):.2f}")
            except Exception:
                item3 = QTableWidgetItem(str(precio))
            item4 = QTableWidgetItem(str(unidades))
            for it in (item0, item1, item2, item3, item4):
                it.setForeground(QColor('#ffffff'))
                it.setBackground(Qt.transparent)
            self.table.setItem(row_num, 0, item0)
            self.table.setItem(row_num, 1, item1)
            self.table.setItem(row_num, 2, item2)
            self.table.setItem(row_num, 3, item3)
            self.table.setItem(row_num, 4, item4)
            
            fecha_str = ""
            if fecha_venc:
                try:
                    if isinstance(fecha_venc, int) or (isinstance(fecha_venc, str) and fecha_venc.isdigit()):
                        fecha = datetime.fromtimestamp(int(fecha_venc))
                        fecha_str = fecha.strftime("%Y-%m-%d")
                    else:
                        fecha = datetime.strptime(str(fecha_venc), "%Y-%m-%d")
                        fecha_str = fecha.strftime("%Y-%m-%d")
                except Exception:
                    fecha_str = ""
            item5 = QTableWidgetItem(fecha_str)
            item6 = QTableWidgetItem(str(id_empleado))
            for it in (item5, item6):
                it.setForeground(QColor('#ffffff'))
                it.setBackground(Qt.transparent)
            self.table.setItem(row_num, 5, item5)
            self.table.setItem(row_num, 6, item6)

            self._add_action_dropdown(row_num, id_producto)

    def _add_action_dropdown(self, row_num, product_id):
        from PyQt5.QtWidgets import QPushButton, QDialog, QVBoxLayout, QLabel

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)

        btn_opciones = ModernButton("Opciones")

        def mostrar_menu():
            dialog = QDialog(self)
            dialog.setWindowTitle("Menú de opciones")
            layout = QVBoxLayout(dialog)
            label = QLabel(f"¿Qué acción desea realizar para el producto {product_id}?")
            layout.addWidget(label)
            # Botones de acción
            btn_editar = ModernButton("Editar")
            btn_eliminar = ModernButton("Eliminar")
            btn_ajustar = ModernButton("Ajustar cantidad")
            btn_precio = ModernButton("Reasignar precio")
            layout.addWidget(btn_editar)
            layout.addWidget(btn_eliminar)
            layout.addWidget(btn_ajustar)
            layout.addWidget(btn_precio)
            # Conexiones
            btn_editar.clicked.connect(lambda: (dialog.accept(), self._edit_product(product_id)))
            btn_eliminar.clicked.connect(lambda: (dialog.accept(), self._confirm_delete_product(product_id)))
            btn_ajustar.clicked.connect(lambda: (dialog.accept(), self._adjust_quantity(product_id)))
            btn_precio.clicked.connect(lambda: (dialog.accept(), self._reassign_price(product_id)))
            dialog.setLayout(layout)
            dialog.exec_()

        btn_opciones.clicked.connect(mostrar_menu)
        action_layout.addWidget(btn_opciones)
        self.table.setCellWidget(row_num, self.table.columnCount() - 1, action_widget)

    def _search_products(self):
        query = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                query in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in [0, 1, 3]  # Buscar en Código, Nombre, Precio
            )
            self.table.setRowHidden(row, not match)

    def _clear_search(self):
        self.search_input.clear()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def _confirm_delete_product(self, product_id):
        reply = QMessageBox.question(self, "Eliminar producto",
                                     f"¿Eliminar el producto con ID {product_id}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if DatabaseManager.delete_product(product_id):
                QMessageBox.information(self, "Éxito", "Producto eliminado.")
                self._load_products()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el producto.")

    def _edit_product(self, product_id):
        self.close()
        abrir_aplicacion("editar_producto.py", [str(product_id), str(self.empleado_actual_id)])

    def _open_insert_product(self):
        self.close()
        abrir_aplicacion("insertar_producto.py")

    def _open_deleted_products(self):
        self.close()
        abrir_aplicacion("productos_eliminados.py")

    def _open_sales_admin(self):
        self.close()
        abrir_aplicacion("ventas_admin.py")

    def _export_products(self, formato):
        from datetime import datetime
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar productos a Excel", f"productos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            "Excel (*.xlsx)"
        )
        if not file_path:
            return
        
        # Corregir la lista de headers para que no incluya la columna de acciones
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount() - 1)]
        
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount() - 1):  # Excluye columna de acciones
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        
        df = pd.DataFrame(data, columns=headers)
        try:
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Exportación exitosa", f"Productos exportados a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", f"No se pudo exportar a Excel:\n{e}")

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

    def _show_cell_tooltip(self, row, column):
        item = self.table.item(row, column)
        if item:
            self.table.setToolTip(item.text())
        else:
            self.table.setToolTip("")

    def _adjust_quantity(self, product_id):
        """Permite ajustar la cantidad de unidades de un producto."""
        from PyQt5.QtWidgets import QInputDialog

        conn = sqlite3.connect(DatabaseManager.get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT unidades FROM productos WHERE id_producto = ?", (product_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            QMessageBox.warning(self, "Error", "No se encontró el producto.")
            return

        unidades_actual = result[0]

        unidades, ok = QInputDialog.getInt(
            self, "Ajustar Cantidad",
            f"Unidades actuales: {unidades_actual}\nIngrese la nueva cantidad de unidades:",
            value=unidades_actual, min=0
        )

        if ok:
            try:
                cursor.execute(
                    "UPDATE productos SET unidades = ? WHERE id_producto = ?",
                    (unidades, product_id)
                )
                conn.commit()
                QMessageBox.information(self, "Éxito", "Cantidad actualizada correctamente.")
                self._load_products()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la cantidad: {e}")
            finally:
                conn.close()
        else:
            conn.close()

    def _reassign_price(self, product_id):
        """Permite reasignar el precio de un producto."""
        from PyQt5.QtWidgets import QInputDialog

        conn = sqlite3.connect(DatabaseManager.get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT precio FROM productos WHERE id_producto = ?", (product_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            QMessageBox.warning(self, "Error", "No se encontró el producto.")
            return

        precio_actual = result[0]

        precio_texto, ok = QInputDialog.getText(
            self, "Reasignar Precio",
            f"Precio actual: {precio_actual:.2f}\nIngrese el nuevo precio (use . o , para decimales):",
            text=str(precio_actual).replace('.', ',')
        )

        if ok and precio_texto:
            try:
                nuevo_precio = float(precio_texto.replace(',', '.'))
                cursor.execute(
                    "UPDATE productos SET precio = ? WHERE id_producto = ?",
                    (nuevo_precio, product_id)
                )
                conn.commit()
                QMessageBox.information(self, "Éxito", "Precio actualizado correctamente.")
                self._load_products()
            except ValueError:
                QMessageBox.warning(self, "Entrada inválida", "Por favor, ingrese un número válido para el precio.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el precio: {e}")
            finally:
                conn.close()
        else:
            conn.close()

# Configura el locale para fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        pass

def abrir_aplicacion(nombre_py, argumentos=None):
    """
    Abre un archivo .py o .exe, usando ruta absoluta o relativa.
    Si es .py, lo ejecuta con el intérprete de Python.
    Permite pasar argumentos.
    """
    if os.path.isabs(nombre_py) and os.path.exists(nombre_py):
        if nombre_py.endswith('.py'):
            cmd = [sys.executable, nombre_py]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return
        elif nombre_py.endswith('.exe'):
            cmd = [nombre_py]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return

    base_paths = [os.getcwd()]
    if hasattr(sys, '_MEIPASS'):
        base_paths.append(sys._MEIPASS)

    for base_path in base_paths:
        exe_path = os.path.join(base_path, nombre_py.replace('.py', '.exe'))
        py_path = os.path.join(base_path, nombre_py)
        
        if os.path.exists(exe_path):
            cmd = [exe_path]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return
        elif os.path.exists(py_path):
            cmd = [sys.executable, py_path]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return

    QMessageBox.warning(None, "⚠️ Archivo no encontrado",
                        f"No se encontró el archivo:\n{nombre_py}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    print("Iniciando ver_productos.py con estilo púrpura-azul")
    empleado_actual_id = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "None" else None
    app = QApplication(sys.argv)
    window = ProductManagementWindow(empleado_actual_id)
    window.showMaximized()
    sys.exit(app.exec_())
