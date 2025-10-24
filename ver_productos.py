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
    QMessageBox, QLabel, QFrame, QFileDialog, QGraphicsDropShadowEffect, QGraphicsBlurEffect
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
        # Fondo por defecto transparente (sobre el cual se colocará image4.jpg)
        self.setStyleSheet("""
            QMainWindow { background: transparent; }
        """)

        # Cargar fondo decorativo (image4.jpg) si existe
        fondo = os.path.abspath(os.path.join(os.path.dirname(__file__), 'image4.jpg'))
        if os.path.exists(fondo):
            self._bg_pixmap = QPixmap(fondo)
            self.bg_label = QLabel(self)
            self.bg_label.setScaledContents(True)
            blur = QGraphicsBlurEffect(self.bg_label)
            blur.setBlurRadius(12)
            self.bg_label.setGraphicsEffect(blur)
            self.bg_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.bg_label.lower()
        self._setup_ui()
        self._load_products()
        self.table.setMouseTracking(True)  # Permite detectar el puntero sobre la celda
        self.table.cellEntered.connect(self._show_cell_tooltip)

    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        # Márgenes y espaciado más amplios para un aspecto moderno
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(12)
        # Hacer el widget principal transparente para que se vea el fondo
        main_widget.setAttribute(Qt.WA_TranslucentBackground)
        # Top bar: búsqueda a la izquierda, botones a la derecha
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, código, línea o presentación...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(0,0,0,0.35);
                border: none;
                border-radius: 22px;
                padding: 10px 18px;
                font-size: 15px; color: #ffffff;
            }
            QLineEdit::placeholder { color: rgba(255,255,255,0.75); }
        """)
        btn_search = QPushButton("Buscar")
        btn_search.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6); color:#22223b; border-radius:14px; padding:8px 16px; font-weight:700;")
        btn_search.clicked.connect(self._search_products)
        btn_clear = QPushButton("Limpiar")
        btn_clear.setStyleSheet("background: rgba(255,255,255,0.08); color:#ffffff; border-radius:14px; padding:8px 16px; border:1px solid rgba(255,255,255,0.06);")
        btn_clear.clicked.connect(self._clear_search)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(btn_search)
        top_layout.addWidget(btn_clear)
        top_layout.addStretch(1)

        # Botones principales (alineados a la derecha en la top bar)
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
        btn_menu.setStyleSheet("background: rgba(255,255,255,0.06); color:#ffffff; border-radius:12px; padding:8px 18px; border:1px solid rgba(255,255,255,0.06);")
        btn_menu.clicked.connect(self.ir_menu_principal)
        btn_layout.addWidget(btn_menu)

        btn_layout.addWidget(btn_insert)
        btn_layout.addWidget(btn_deleted)
        btn_layout.addWidget(btn_sell)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_export)
        # Insertar top_layout antes de la botonera principal para un topbar organizado
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
        # Hacer la tabla transparente y con encabezados legibles sobre el fondo
        self.table.setStyleSheet("""
            QTableWidget { background: transparent; color: #ffffff; border: none; }
            QTableWidget::item { background: transparent; }
            QTableWidget::item:selected { background: rgba(255,255,255,0.08); }
            QHeaderView::section { background: rgba(0,0,0,0.45); color: #ffffff; border: none; padding: 6px; }
        """)
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
            item3 = QTableWidgetItem(f"{precio:.2f}")
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

        btn_opciones = QPushButton("Opciones")
        btn_opciones.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ef;
                color: #22223b;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c9d6e3;
            }
        """)

        def mostrar_menu():
            dialog = QDialog(self)
            dialog.setWindowTitle("Menú de opciones")
            layout = QVBoxLayout(dialog)
            label = QLabel(f"¿Qué acción desea realizar para el producto {product_id}?")
            layout.addWidget(label)
            # Botones de acción
            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")
            btn_ajustar = QPushButton("Ajustar cantidad")
            btn_precio = QPushButton("Reasignar precio")
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