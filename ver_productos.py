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
from PyQt5.QtGui import QColor, QPixmap, QIcon
import glob
import locale

# Configuración de la base de datos
DB_NAME = "pruebas.db"

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
        """Obtiene todos los productos de la base de datos, incluyendo el nombre del empleado que lo modificó"""
        try:
            conn = sqlite3.connect(DatabaseManager.get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_producto, p.codigo, p.imagen, p.nombre, p.precio, p.stock, p.fecha_venc,
                       IFNULL(e.nombre, 'Sin asignar') as empleado
                FROM productos p
                LEFT JOIN empleado e ON p.id_empleado = e.id_empleado
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
            
            cursor.execute("""
                SELECT id_producto, codigo, imagen, nombre, precio, stock, fecha_venc
            FROM productos WHERE id_producto = ?
            """, (product_id,))
            product = cursor.fetchone()
            
            if product:
                # El tuple 'product' ya contiene los 10 valores,
                # ahora insertamos en la tabla de eliminados con la fecha de borrado
                cursor.execute("""
                INSERT INTO productos_borrados (
                    id_producto, codigo, imagen, nombre, precio, stock, fecha_venc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, product) # Añadir el valor de fecha_borrado
                
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
    """Botón personalizado con efectos modernos"""
    def __init__(self, text, icon_text="", color="#4CAF50", hover_color="#45a049"):
        super().__init__()
        self.setText(f"{icon_text} {text}" if icon_text else text)
        self.color = color
        self.hover_color = hover_color
        self.setStyleSheet(self._get_style())
        self.setCursor(Qt.PointingHandCursor)
        
    def _get_style(self):
        """Genera el estilo CSS para el botón"""
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.color}, stop:1 {self._darken_color(self.color)});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.hover_color}, stop:1 {self._darken_color(self.hover_color)});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self._darken_color(self.color)}, stop:1 {self.color});
            }}
        """
    
    def _darken_color(self, color):
        """Oscurece un color hexadecimal"""
        color = color.replace('#', '')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
        return f"#{r:02x}{g:02x}{b:02x}"

class SearchBox(QLineEdit):
    """Campo de búsqueda personalizado"""
    def __init__(self, placeholder="Buscar..."):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                padding: 12px 20px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: #f9f9f9;
            }
            QLineEdit::placeholder {
                color: #999;
            }
        """)

class StatsCard(QFrame):
    """Tarjeta de estadísticas con diseño moderno"""
    def __init__(self, title, value, icon="📊", color="#4CAF50"):
        super().__init__()
        self._setup_ui(title, value, icon, color)
        
    def _setup_ui(self, title, value, icon, color):
        """Configura la interfaz de la tarjeta"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 white, stop:1 #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)

class ProductManagementWindow(QMainWindow):
    """Ventana principal de gestión de productos con colores suaves"""
    def __init__(self, empleado_actual_id):
        super().__init__()
        self.empleado_actual_id = empleado_actual_id
        self.setWindowTitle("Gestión de Productos")
        self.setGeometry(100, 100, 1100, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f6fb;
            }
        """)
        self._setup_ui()
        self._load_products()

    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, código, línea o presentación...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #dbe2ef;
                border-radius: 18px;
                padding: 10px 18px;
                font-size: 15px;
                color: #22223b;
            }
            QLineEdit:focus {
                border-color: #a3cef1;
                background-color: #f0f4fa;
            }
        """)
        btn_search = QPushButton("Buscar")
        btn_search.setStyleSheet("""
            QPushButton {
                background-color: #a3cef1;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b6e0fe;
            }
        """)
        btn_search.clicked.connect(self._search_products)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #f9fafc;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #dbe2ef;
            }
            QPushButton:hover {
                background-color: #e0e7ef;
            }
        """)
        btn_clear.clicked.connect(self._clear_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)
        search_layout.addWidget(btn_clear)
        main_layout.addLayout(search_layout)

        # Botones principales
        btn_layout = QHBoxLayout()
        btn_insert = QPushButton("Insertar")
        btn_insert.setStyleSheet("""
            QPushButton {
                background-color: #b7e4c7;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d8f3dc;
            }
        """)
        btn_insert.clicked.connect(self._open_insert_product)

        btn_deleted = QPushButton("Eliminados")
        btn_deleted.setStyleSheet("""
            QPushButton {
                background-color: #ffe5d9;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffd7ba;
            }
        """)
        btn_deleted.clicked.connect(self._open_deleted_products)

        btn_sell = QPushButton("Vender")
        btn_sell.setStyleSheet("""
            QPushButton {
                background-color: #f9c6c9;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f7cad0;
            }
        """)
        btn_sell.clicked.connect(self._open_sales_admin)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ef;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c9d6e3;
            }
        """)
        btn_refresh.clicked.connect(self._load_products)

        btn_export = QPushButton("Exportar")
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #f7f7fa;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #dbe2ef;
            }
            QPushButton:hover {
                background-color: #e0e7ef;
            }
        """)
        btn_export.clicked.connect(lambda: self._export_products("xlsx"))

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: #22223b;
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffe066;
            }
        """)
        btn_menu.clicked.connect(self.ir_menu_principal)
        btn_layout.addWidget(btn_menu)

        btn_layout.addWidget(btn_insert)
        btn_layout.addWidget(btn_deleted)
        btn_layout.addWidget(btn_sell)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_export)
        main_layout.addLayout(btn_layout)

        # Tabla de productos
        self.table = QTableWidget()
        self.table.setColumnCount(9) # 8 columnas de datos + 1 de acciones
        self.table.setHorizontalHeaderLabels([
            "ID", "CÓDIGO", "IMAGEN", "NOMBRE", "PRECIO", "STOCK", "VENCIMIENTO", "EMPLEADO", "ACCIONES"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border-radius: 14px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #e0e7ef;
                color: #22223b;
                font-weight: bold;
                border-radius: 8px;
                padding: 6px;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        main_layout.addWidget(self.table)

        self.setCentralWidget(main_widget)

    def _load_products(self):
        # Guardar la fila seleccionada antes de recargar
        selected_row = self.table.currentRow()
        selected_id = None
        if selected_row >= 0:
            item = self.table.item(selected_row, 0)
            if item:
                selected_id = item.text()

        products = DatabaseManager.get_products()
        self.table.setRowCount(0)
        for row_num, product in enumerate(products):
            self.table.insertRow(row_num)
            for col_num, data in enumerate(product):
                # Formatear la fecha de vencimiento (columna 6)
                if col_num == 6 and data is not None:
                    try:
                        fecha = datetime.fromtimestamp(int(data))
                        data_str = fecha.strftime("%d/%b/%Y")  # Ahora el mes será en español si el locale lo permite
                    except Exception:
                        data_str = str(data)
                    item = QTableWidgetItem(data_str)
                # Mostrar miniatura de imagen (columna 2)
                elif col_num == 2 and data:
                    item = QTableWidgetItem()
                    # Si la ruta es relativa, hazla absoluta
                    ruta_img = data
                    if not os.path.isabs(ruta_img):
                        ruta_img = os.path.join(os.path.dirname(__file__), ruta_img)
                    if os.path.exists(ruta_img):
                        pixmap = QPixmap(ruta_img)
                        if not pixmap.isNull():
                            # Cambia aquí el tamaño de la miniatura
                            icon = QIcon(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            item.setIcon(icon)
                            item.setText("")  # Opcional: no mostrar texto
                        else:
                            item.setText("Imagen inválida")
                    else:
                        item.setText("No encontrada")
                # Mostrar nombre del empleado (columna 7)
                elif col_num == 7:
                    item = QTableWidgetItem(str(data) if data is not None else "Sin asignar")
                else:
                    item = QTableWidgetItem(str(data) if data is not None else "")
                self.table.setItem(row_num, col_num, item)
            self._add_action_buttons(row_num, product[0]) # product[0] es el ID

        # Restaurar la selección si es posible
        if selected_id is not None:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item and item.text() == selected_id:
                    self.table.selectRow(row)
                    break

    def _add_action_buttons(self, row_num, product_id):
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_edit = QPushButton("Editar")
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #b7e4c7;
                color: #22223b;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d8f3dc;
            }
        """)
        btn_edit.clicked.connect(partial(self._edit_product, product_id))
        
        btn_delete = QPushButton("Eliminar")
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ffe5d9;
                color: #22223b;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #ffd7ba;
            }
        """)
        btn_delete.clicked.connect(partial(self._confirm_delete_product, product_id))
        
        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_delete)
        self.table.setCellWidget(row_num, self.table.columnCount() - 1, action_widget)

    def _search_products(self):
        query = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                query in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(1, 8)  # Buscar en todas las columnas excepto ID y acciones
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
        abrir_aplicacion("Modificar_producto.py", [str(product_id), str(self.empleado_actual_id)])

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

# Configura el locale para fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    # Si no está disponible en Windows, intenta con otra variante o ignora
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        pass  # Si no se puede, seguirá en inglés

def abrir_aplicacion(nombre_py, argumentos=None):
    """
    Abre un archivo .py o .exe, usando ruta absoluta o relativa.
    Si es .py, lo ejecuta con el intérprete de Python.
    Permite pasar argumentos.
    """
    # Si es ruta absoluta y existe, úsala directamente
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

    # Si es solo nombre, busca en cwd y en _MEIPASS
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
    print("Iniciando ver_productos.py")
    empleado_actual_id = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "None" else None
    app = QApplication(sys.argv)
    window = ProductManagementWindow(empleado_actual_id)
    window.showMaximized()
    sys.exit(app.exec_())