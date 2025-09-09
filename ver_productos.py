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
        """Obtiene todos los productos de la base de datos, incluyendo todas las columnas necesarias"""
        try:
            conn = sqlite3.connect(DatabaseManager.get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_producto, p.codigo, p.imagen, p.nombre, p.precio, p.stock, p.fecha_venc,
                       p.id_empleado, p.cajas, p.unidades
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
        self.table.setMouseTracking(True)  # Permite detectar el puntero sobre la celda
        self.table.cellEntered.connect(self._show_cell_tooltip)

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
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Imagen", "Precio", "Cajas", "Paquetes", "Paquetes Totales",
            "Unidades por Paquete", "Unidades Totales", "Fecha Venc.", "Empleado", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)

        self.setCentralWidget(main_widget)

    def _load_products(self):
        selected_row = self.table.currentRow()
        selected_id = None
        if selected_row >= 0:
            item = self.table.item(selected_row, 0)
            if item:
                selected_id = item.text()

        products = []
        try:
            conn = sqlite3.connect(DatabaseManager.get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_producto, codigo, imagen, nombre, precio, fecha_venc, id_empleado,
                       cajas, paquetes, unidades_por_paquete, unidades, paquetes_por_caja
                FROM productos
            """)
            products = cursor.fetchall()
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener los datos: {e}")

        self.table.setRowCount(0)
        for row_num, product in enumerate(products):
            self.table.insertRow(row_num)
            (id_producto, codigo, imagen, nombre, precio, fecha_venc, id_empleado,
             cajas, paquetes, unidades_por_paquete, unidades_sueltas, paquetes_por_caja) = product

            # Consulta las unidades por paquete desde la tabla productos_unidades
            unidades_por_paquete_db = None
            try:
                conn = sqlite3.connect(DatabaseManager.get_db_path())
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT unidades FROM productos_unidades WHERE id_producto = ?", (id_producto,)
                )
                result = cursor.fetchone()
                if result:
                    unidades_por_paquete_db = result[0]
                conn.close()
            except Exception:
                unidades_por_paquete_db = unidades_por_paquete

            if unidades_por_paquete_db is None:
                unidades_por_paquete_db = unidades_por_paquete

            # Lógica mejorada para el conteo
            if cajas and cajas > 0:
                paquetes_totales = (paquetes if paquetes else 0) * cajas
                unidades_totales = paquetes_totales * (unidades_por_paquete_db if unidades_por_paquete_db else 0) + (unidades_sueltas if unidades_sueltas else 0)
            elif paquetes and paquetes > 0:
                paquetes_totales = paquetes
                unidades_totales = paquetes_totales * (unidades_por_paquete_db if unidades_por_paquete_db else 0) + (unidades_sueltas if unidades_sueltas else 0)
            else:
                paquetes_totales = 0
                unidades_totales = unidades_sueltas if unidades_sueltas else 0  # Solo productos sueltos

            # Código
            self.table.setItem(row_num, 0, QTableWidgetItem(str(codigo)))
            # Nombre
            self.table.setItem(row_num, 1, QTableWidgetItem(str(nombre)))
            # Imagen
            self.table.setItem(row_num, 2, QTableWidgetItem(str(imagen)))
            # Precio
            self.table.setItem(row_num, 3, QTableWidgetItem(f"{precio:.2f}"))
            # Cajas
            self.table.setItem(row_num, 4, QTableWidgetItem(str(cajas)))
            # Paquetes (sueltos)
            self.table.setItem(row_num, 5, QTableWidgetItem(str(paquetes)))
            # Paquetes totales
            self.table.setItem(row_num, 6, QTableWidgetItem(f"{paquetes_totales:,}".replace(",", ".")))
            # Unidades por paquete
            self.table.setItem(row_num, 7, QTableWidgetItem(f"{unidades_por_paquete_db:,}".replace(",", ".")))
            # Unidades totales
            self.table.setItem(row_num, 8, QTableWidgetItem(f"{unidades_totales:,}".replace(",", ".")))

            # Actualiza la columna unidades_totales en productos_unidades para este producto
            try:
                conn_update = sqlite3.connect(DatabaseManager.get_db_path())
                cursor_update = conn_update.cursor()
                cursor_update.execute(
                    "UPDATE productos_unidades SET unidades_totales = ? WHERE id_producto = ?",
                    (unidades_totales, id_producto)
                )
                conn_update.commit()
                conn_update.close()
            except Exception:
                pass
            # Fecha Venc.
            fecha_str = ""
            if fecha_venc:
                try:
                    fecha = datetime.strptime(str(fecha_venc), "%Y-%m-%d")
                    fecha_str = fecha.strftime("%Y-%m-%d")
                except Exception:
                    fecha_str = str(fecha_venc)
            self.table.setItem(row_num, 9, QTableWidgetItem(fecha_str))
            # Empleado
            self.table.setItem(row_num, 10, QTableWidgetItem(str(id_empleado)))
            # Acciones
            self._add_action_dropdown(row_num, id_producto)

        # Restaurar la selección si es posible
        if selected_id is not None:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item and item.text() == selected_id:
                    self.table.selectRow(row)
                    break

        total_paquetes = 0
        for product in products:
            cajas = product[7]
            paquetes_por_caja = product[11]
            paquetes_sueltos = product[8]
            # Suma los paquetes totales según la lógica mejorada
            if cajas and cajas > 0:
                paquetes_totales = (paquetes_sueltos if paquetes_sueltos else 0) * cajas
            elif paquetes_sueltos and paquetes_sueltos > 0:
                paquetes_totales = paquetes_sueltos
            else:
                paquetes_totales = 0
            total_paquetes += paquetes_totales

        # Puedes mostrarlo en una StatsCard arriba de la tabla:
        stats_card = StatsCard("Paquetes totales en inventario", total_paquetes, icon="📦", color="#4CAF50")
        # Si ya tienes una tarjeta, actualízala; si no, agrégala al layout principal:
        # main_layout.insertWidget(0, stats_card)

        # Agrega una fila resumen al final
        resumen_row = self.table.rowCount()
        self.table.insertRow(resumen_row)
        self.table.setSpan(resumen_row, 0, 1, 6)
        self.table.setItem(resumen_row, 0, QTableWidgetItem("TOTAL PAQUETES"))
        self.table.setItem(resumen_row, 6, QTableWidgetItem(str(total_paquetes)))

    def _add_action_dropdown(self, row_num, product_id):
        from PyQt5.QtWidgets import QComboBox

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)

        combo = QComboBox()
        combo.addItem("Seleccionar acción")
        combo.addItem("Editar")
        combo.addItem("Eliminar")
        combo.addItem("Ajustar cantidad")
        combo.addItem("Reasignar precio")
        combo.setStyleSheet("""
            QComboBox {
                background-color: #e0e7ef;
                color: #22223b;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        def on_action_selected(index):
            action = combo.currentText()
            if action == "Editar":
                self._edit_product(product_id)
            elif action == "Eliminar":
                self._confirm_delete_product(product_id)
            elif action == "Ajustar cantidad":
                self._adjust_quantity(product_id)
            elif action == "Reasignar precio":
                self._reassign_price(product_id)
            combo.setCurrentIndex(0)  # Reset after action

        combo.currentIndexChanged.connect(on_action_selected)
        action_layout.addWidget(combo)
        self.table.setCellWidget(row_num, self.table.columnCount() - 1, action_widget)

    def _search_products(self):
        query = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                query in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(1, 9)  # Buscar en todas las columnas excepto ID y acciones (incluye cajas)
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

    def _adjust_quantity(self, product_id):
        """Permite ajustar la cantidad y guarda el total de unidades correctamente en productos_unidades.unidades_totales."""
        from PyQt5.QtWidgets import QInputDialog

        conn = sqlite3.connect(DatabaseManager.get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT cajas, paquetes, unidades_por_paquete, unidades, paquetes_por_caja FROM productos WHERE id_producto = ?", (product_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            QMessageBox.warning(self, "Error", "No se encontró el producto.")
            return

        cajas_actual, paquetes_actual, unidades_por_paquete_actual, unidades_sueltas_actual, paquetes_por_caja_actual = result

        # Solicitar nueva cantidad de cajas
        cajas, ok_cajas = QInputDialog.getInt(
            self, "Ajustar cantidad de cajas",
            f"Cantidad actual de cajas: {cajas_actual}\nIngrese nueva cantidad de cajas:",
            value=cajas_actual, min=0
        )
        if not ok_cajas:
            conn.close()
            return

        # Solicitar nueva cantidad de paquetes
        paquetes, ok_paquetes = QInputDialog.getInt(
            self, "Ajustar cantidad de paquetes",
            f"Cantidad actual de paquetes: {paquetes_actual}\nIngrese nueva cantidad de paquetes:",
            value=paquetes_actual, min=0
        )
        if not ok_paquetes:
            conn.close()
            return

        # Solicitar nueva cantidad de unidades por paquete
        unidades_por_paquete, ok_unidades = QInputDialog.getInt(
            self, "Ajustar unidades por paquete",
            f"Unidades actuales por paquete: {unidades_por_paquete_actual}\nIngrese nueva cantidad de unidades por paquete:",
            value=unidades_por_paquete_actual, min=1
        )
        if not ok_unidades:
            conn.close()
            return

        # Solicitar nueva cantidad de unidades sueltas
        unidades_sueltas, ok_unidades_sueltas = QInputDialog.getInt(
            self, "Ajustar unidades sueltas",
            f"Unidades sueltas actuales: {unidades_sueltas_actual}\nIngrese nueva cantidad de unidades sueltas:",
            value=unidades_sueltas_actual, min=0
        )
        if not ok_unidades_sueltas:
            conn.close()
            return

        # Solicitar nueva cantidad de paquetes por caja
        paquetes_por_caja, ok_paquetes_por_caja = QInputDialog.getInt(
            self, "Ajustar paquetes por caja",
            f"Paquetes por caja actuales: {paquetes_por_caja_actual}\nIngrese nueva cantidad de paquetes por caja:",
            value=paquetes_por_caja_actual, min=0
        )
        if not ok_paquetes_por_caja:
            conn.close()
            return

        try:
            # Actualizar en la tabla productos
            cursor.execute(
                "UPDATE productos SET cajas = ?, paquetes = ?, unidades_por_paquete = ?, unidades = ?, paquetes_por_caja = ? WHERE id_producto = ?",
                (cajas, paquetes, unidades_por_paquete, unidades_sueltas, paquetes_por_caja, product_id)
            )

            # Registrar paquetes en productos_paquetes
            cursor.execute("SELECT nombre, codigo, precio, fecha_venc, id_empleado FROM productos WHERE id_producto = ?", (product_id,))
            prod_data = cursor.fetchone()
            if prod_data:
                nombre, codigo, precio, fecha_venc, id_empleado = prod_data
                cursor.execute("""
                    INSERT OR REPLACE INTO productos_paquetes (id_producto, codigo, nombre, precio_paquete, fecha_venc, id_empleado, paquetes_disponibles, unidades_por_paquete)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, codigo, nombre, precio, fecha_venc, id_empleado, paquetes, unidades_por_paquete
                ))

            # Calcular el total de unidades tal cual lo muestra la interfaz
            unidades_totales = (
                (cajas if cajas else 0) * (paquetes_por_caja if paquetes_por_caja else 0) * (unidades_por_paquete if unidades_por_paquete else 0)
                + (paquetes if paquetes else 0) * (unidades_por_paquete if unidades_por_paquete else 0)
                + (unidades_sueltas if unidades_sueltas else 0)
            )

            # Registrar unidades por paquete y unidades totales en productos_unidades
            cursor.execute("SELECT 1 FROM productos_unidades WHERE id_producto = ?", (product_id,))
            existe = cursor.fetchone()

            if existe:
                cursor.execute("""
                    UPDATE productos_unidades
                    SET unidades = ?, unidades_totales = ?
                    WHERE id_producto = ?
                """, (unidades_por_paquete, unidades_totales, product_id))
            else:
                cursor.execute("""
                    INSERT INTO productos_unidades (id_producto, codigo, nombre, precio_unitario, fecha_venc, id_empleado, unidades, unidades_totales)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, codigo, nombre, precio, fecha_venc, id_empleado, unidades_por_paquete, unidades_totales
                ))

            # Actualizar solo unidades_totales en productos_unidades
            cursor.execute("""
                UPDATE productos_unidades
                SET unidades_totales = ?
                WHERE id_producto = ?
            """, (unidades_totales, product_id))

            conn.commit()
            QMessageBox.information(self, "Cantidad ajustada", "Las cantidades fueron actualizadas correctamente y el total de unidades se guardó en la base de datos.")
            self._load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo ajustar la cantidad:\n{e}")
        finally:
            conn.close()

    def _reassign_price(self, product_id):
        """Permite reasignar el precio de un producto, acepta punto o coma como separador decimal"""
        from PyQt5.QtWidgets import QInputDialog

        # Obtener precio actual
        conn = sqlite3.connect(DatabaseManager.get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT precio FROM productos WHERE id_producto = ?", (product_id,))
        result = cursor.fetchone()
        conn.close()
        if not result:
            QMessageBox.warning(self, "Error", "No se encontró el producto.")
            return

        precio_actual = result[0]

        # Solicitar nuevo precio como texto para permitir punto o coma
        precio_texto, ok = QInputDialog.getText(
            self, "Reasignar precio",
            f"Precio actual: {precio_actual}\nIngrese nuevo precio (puede usar punto o coma):",
            text=str(precio_actual)
        )
        if not ok or not precio_texto.strip():
            return

        # Reemplaza coma por punto y convierte a float
        try:
            precio = float(precio_texto.replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un precio válido (ejemplo: 12.50 o 12,50).")
            return

        # Actualizar en la base de datos
        try:
            conn = sqlite3.connect(DatabaseManager.get_db_path())
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE productos SET precio = ? WHERE id_producto = ?",
                (precio, product_id)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Precio actualizado", "El precio fue actualizado correctamente.")
            self._load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo reasignar el precio:\n{e}")

    def _show_cell_tooltip(self, row, column):
        item = self.table.item(row, column)
        if item:
            self.table.setToolTip(item.text())
        else:
            self.table.setToolTip("")

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