import sys
import sqlite3
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QSpinBox, QHeaderView, QComboBox
)
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta

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

class VentasWindow(QMainWindow):
    def __init__(self):
        """Inicializa la ventana principal del sistema de ventas y configura la interfaz."""
        super().__init__()
        self.setWindowTitle("Sistema de Ventas")
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        self.carrito = []

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Título
        title_label = QLabel("Sistema de Ventas")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Barra de navegación
        nav_layout = QHBoxLayout()
        btn_productos = QPushButton("Ver Productos")
        btn_productos.clicked.connect(lambda: self.abrir_script("ver_productos.py"))
        nav_layout.addWidget(btn_productos)
        btn_nuevo_producto = QPushButton("Nuevo Producto")
        btn_nuevo_producto.clicked.connect(lambda: self.abrir_script("insertar_producto.py"))
        nav_layout.addWidget(btn_nuevo_producto)
        btn_empleados = QPushButton("Empleados")
        btn_empleados.clicked.connect(lambda: self.abrir_script(os.path.join("empleados", "ver_empleado.py")))
        nav_layout.addWidget(btn_empleados)
        btn_nuevo_empleado = QPushButton("Nuevo Empleado")
        btn_nuevo_empleado.clicked.connect(lambda: self.abrir_script(os.path.join("empleados", "insertar_empleado.py")))
        nav_layout.addWidget(btn_nuevo_empleado)
        btn_ventas = QPushButton("Ventas")
        btn_ventas.clicked.connect(lambda: self.abrir_script("venta_registro.py"))
        nav_layout.addWidget(btn_ventas)
        main_layout.addLayout(nav_layout)

        # Buscador de productos
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_layout.addWidget(search_label)
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Nombre o código...")
        self.input_busqueda.returnPressed.connect(self.buscar_producto)
        search_layout.addWidget(self.input_busqueda)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar_producto)
        search_layout.addWidget(btn_buscar)
        main_layout.addLayout(search_layout)

        # Tabla de productos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Imagen", "Precio", "Cajas", "Paquetes",
            "Paquetes Totales", "Unidades por Paquete", "Unidades Totales",
            "Fecha Venc.", "Empleado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.tabla)

        # Panel de agregar al carrito
        add_layout = QHBoxLayout()
        qty_label = QLabel("Cantidad:")
        add_layout.addWidget(qty_label)
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(1)
        add_layout.addWidget(self.spin_cantidad)
        self.combo_tipo_venta = QComboBox()
        self.combo_tipo_venta.addItems(["Por unidad", "Por caja"])
        add_layout.addWidget(self.combo_tipo_venta)
        btn_agregar = QPushButton("Agregar al Carrito")
        btn_agregar.clicked.connect(self.agregar_al_carrito)
        add_layout.addWidget(btn_agregar)
        main_layout.addLayout(add_layout)

        # Tabla del carrito
        cart_label = QLabel("Carrito de Venta")
        cart_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(cart_label)
        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(4)
        self.tabla_carrito.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad", "Subtotal"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_carrito.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.tabla_carrito)

        # Panel de total y botones
        total_layout = QHBoxLayout()
        self.label_total = QLabel("Total: $0.00")
        self.label_total.setStyleSheet("font-size: 18px; font-weight: bold;")
        total_layout.addWidget(self.label_total)
        btn_cancelar = QPushButton("Cancelar Venta")
        btn_cancelar.clicked.connect(self.cancelar_venta)
        total_layout.addWidget(btn_cancelar)
        btn_vender = QPushButton("Procesar Venta")
        btn_vender.clicked.connect(self.vender_todo)
        total_layout.addWidget(btn_vender)
        main_layout.addLayout(total_layout)

        # Panel de pago y cambio
        pago_layout = QHBoxLayout()
        pago_label = QLabel("Pago del cliente (Bs.):")
        pago_layout.addWidget(pago_label)
        self.input_pago = QLineEdit()
        self.input_pago.setPlaceholderText("Ejemplo: 50")
        pago_layout.addWidget(self.input_pago)
        btn_calcular_cambio = QPushButton("Calcular Cambio")
        btn_calcular_cambio.clicked.connect(self.calcular_cambio)
        pago_layout.addWidget(btn_calcular_cambio)
        self.label_cambio = QLabel("Cambio: 0.00 Bs.")
        self.label_cambio.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3436;")
        pago_layout.addWidget(self.label_cambio)
        main_layout.addLayout(pago_layout)

        # Panel de descuento
        descuento_layout = QHBoxLayout()
        descuento_label = QLabel("Descuento (%):")
        descuento_layout.addWidget(descuento_label)
        self.input_descuento = QLineEdit()
        self.input_descuento.setPlaceholderText("Ejemplo: 10")
        descuento_layout.addWidget(self.input_descuento)
        btn_aplicar_descuento = QPushButton("Aplicar Descuento")
        btn_aplicar_descuento.clicked.connect(self.aplicar_descuento)
        descuento_layout.addWidget(btn_aplicar_descuento)
        self.label_descuento = QLabel("Descuento aplicado: 0.00 Bs.")
        self.label_descuento.setStyleSheet("font-size: 16px; color: #0984e3;")
        descuento_layout.addWidget(self.label_descuento)
        main_layout.addLayout(descuento_layout)

        self.descuento_porcentaje = 0.0  # Variable para guardar el descuento aplicado

        # Botón de menú principal
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        main_layout.addWidget(btn_menu, alignment=Qt.AlignLeft)

        self.tabla.selectionModel().selectionChanged.connect(self.actualizar_spinbox)
        self.cargar_todos_productos()

    def cargar_todos_productos(self):
        """Carga productos mostrando todas las columnas relevantes excepto acciones y código."""
        self.cursor.execute("""
            SELECT p.nombre, p.imagen, p.precio, p.cajas, p.paquetes,
                   (p.cajas * p.paquetes_por_caja + p.paquetes) as paquetes_totales,
                   p.unidades_por_paquete,
                   (p.cajas * p.paquetes_por_caja * p.unidades_por_paquete + p.paquetes * p.unidades_por_paquete + p.unidades) as unidades_totales,
                   p.fecha_venc, p.id_empleado
            FROM productos p
            ORDER BY p.nombre ASC
        """)
        resultados = self.cursor.fetchall()
        self.mostrar_productos(resultados)
        self.spin_cantidad.setMaximum(1)

    def buscar_producto(self):
        """Busca productos por nombre o código y muestra columnas cajas y paquetes correctamente."""
        texto = self.input_busqueda.text().strip()
        if not texto:
            self.cargar_todos_productos()
            return
        like = f"%{texto}%"
        # Buscar en productos
        self.cursor.execute("""
            SELECT nombre, codigo, precio, cajas, 0 as paquetes
            FROM productos
            WHERE (nombre LIKE ? OR codigo LIKE ?)
        """, (like, like))
        productos = self.cursor.fetchall()
        # Buscar en productos_paquetes
        self.cursor.execute("""
            SELECT nombre, codigo, precio_paquete, 0 as cajas, paquetes_disponibles
            FROM productos_paquetes
            WHERE (nombre LIKE ? OR codigo LIKE ?)
        """, (like, like))
        paquetes = self.cursor.fetchall()
        resultados = productos + paquetes
        self.mostrar_productos(resultados)

    def mostrar_productos(self, resultados):
        """Muestra los productos en la tabla principal sin la columna código."""
        self.tabla.setRowCount(0)
        for row_num, row_data in enumerate(resultados):
            (nombre, imagen, precio, cajas, paquetes, paquetes_totales,
             unidades_por_paquete, unidades_totales, fecha_venc, id_empleado) = row_data
            self.tabla.insertRow(row_num)
            self.tabla.setItem(row_num, 0, QTableWidgetItem(str(nombre)))
            # Imagen
            img_item = QTableWidgetItem()
            if imagen and os.path.exists(imagen):
                from PyQt5.QtGui import QPixmap
                pixmap = QPixmap(imagen).scaled(40, 40, Qt.KeepAspectRatio)
                img_item.setData(Qt.DecorationRole, pixmap)
            else:
                img_item.setText("[img]")
            self.tabla.setItem(row_num, 1, img_item)
            self.tabla.setItem(row_num, 2, QTableWidgetItem(f"{precio:.2f} Bs."))
            self.tabla.setItem(row_num, 3, QTableWidgetItem(str(cajas)))
            self.tabla.setItem(row_num, 4, QTableWidgetItem(str(paquetes)))
            self.tabla.setItem(row_num, 5, QTableWidgetItem(str(paquetes_totales)))
            self.tabla.setItem(row_num, 6, QTableWidgetItem(str(unidades_por_paquete)))
            self.tabla.setItem(row_num, 7, QTableWidgetItem(str(unidades_totales)))
            # Fecha vencimiento
            if fecha_venc:
                try:
                    fecha = datetime.fromtimestamp(int(fecha_venc)).strftime("%Y-%m-%d")
                except Exception:
                    fecha = str(fecha_venc)
                self.tabla.setItem(row_num, 8, QTableWidgetItem(fecha))
            else:
                self.tabla.setItem(row_num, 8, QTableWidgetItem(""))
            self.tabla.setItem(row_num, 9, QTableWidgetItem(str(id_empleado)))
        self.tabla.resizeColumnsToContents()
        self.spin_cantidad.setMaximum(1)

    def actualizar_spinbox(self):
        """Actualiza el máximo del spinbox de cantidad según el stock del producto seleccionado."""
        selected = self.tabla.currentRow()
        if selected == -1:
            self.spin_cantidad.setMaximum(1)
            return
        try:
            stock = int(self.tabla.item(selected, 5).text())
        except Exception:
            stock = 1
        self.spin_cantidad.setMaximum(max(1, stock))

    def agregar_al_carrito(self):
        """Agrega el producto seleccionado y la cantidad indicada al carrito de ventas."""
        selected = self.tabla.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Advertencia", "Seleccione un producto para agregar al carrito.")
            return
        try:
            nombre = self.tabla.item(selected, 0).text()
            codigo = self.tabla.item(selected, 1).text()
            precio = float(self.tabla.item(selected, 2).text().replace(" Bs.", ""))
            cajas = int(self.tabla.item(selected, 3).text()) if self.tabla.item(selected, 3).text() else 0
            unidades = int(self.tabla.item(selected, 4).text()) if self.tabla.item(selected, 4).text() else 0
            stock = int(self.tabla.item(selected, 5).text())
            # Buscar el id_producto en la base de datos usando código
            self.cursor.execute("SELECT id_producto FROM productos WHERE codigo = ?", (codigo,))
            result = self.cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "No se encontró el producto en la base de datos.")
                return
            producto_id = result[0]
        except Exception:
            QMessageBox.warning(self, "Error", "Error al leer los datos del producto seleccionado.")
            return

        cantidad = self.spin_cantidad.value()
        tipo_venta = self.combo_tipo_venta.currentText()

        if tipo_venta == "Por caja":
            if cajas == 0 or unidades == 0:
                QMessageBox.warning(self, "No disponible", "Este producto no tiene cajas configuradas.")
                return
            if cantidad > cajas:
                QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficientes cajas de '{nombre}'.")
                return
            cantidad_unidades = cantidad * unidades
            descripcion = f"{cantidad} caja(s) ({cantidad_unidades} unidades)"
        else:
            if cantidad > stock:
                QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficiente stock de '{nombre}'.")
                return
            cantidad_unidades = cantidad
            descripcion = f"{cantidad_unidades} unidad(es)"

        # Verifica si ya está en el carrito
        for item in self.carrito:
            if item["id"] == producto_id and item["tipo"] == tipo_venta:
                if item["cantidad"] + cantidad > (cajas if tipo_venta == "Por caja" else stock):
                    QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficiente stock de '{nombre}'.")
                    return
                item["cantidad"] += cantidad
                item["cantidad_unidades"] += cantidad_unidades
                item["descripcion"] = f"{item['cantidad']} caja(s) ({item['cantidad_unidades']} unidades)" if tipo_venta == "Por caja" else f"{item['cantidad_unidades']} unidad(es)"
                self.actualizar_tabla_carrito()
                self.spin_cantidad.setValue(1)
                return

        self.carrito.append({
            "id": producto_id,
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "cantidad_unidades": cantidad_unidades,
            "stock": stock,
            "codigo": codigo,
            "tipo": tipo_venta,
            "descripcion": descripcion
        })
        self.actualizar_tabla_carrito()
        self.spin_cantidad.setValue(1)

    def actualizar_tabla_carrito(self):
        """Actualiza la tabla del carrito de ventas y el total."""
        self.tabla_carrito.setRowCount(0)
        for row_num, item in enumerate(self.carrito):
            self.tabla_carrito.insertRow(row_num)
            self.tabla_carrito.setItem(row_num, 0, QTableWidgetItem(str(item["id"])))
            self.tabla_carrito.setItem(row_num, 1, QTableWidgetItem(item["nombre"]))
            self.tabla_carrito.setItem(row_num, 2, QTableWidgetItem(item["descripcion"]))
            subtotal = item["cantidad_unidades"] * item["precio"]
            subtotal_item = QTableWidgetItem(f"{subtotal:.2f} Bs.")
            self.tabla_carrito.setItem(row_num, 3, subtotal_item)
        total = sum(item["cantidad_unidades"] * item["precio"] for item in self.carrito)
        self.label_total.setText(f"Total: {total:.2f} Bs.")

    def cancelar_venta(self):
        """Cancela la venta actual, vacía el carrito y muestra un mensaje."""
        self.carrito = []
        self.tabla_carrito.setRowCount(0)
        self.label_total.setText("Total: 0.00 Bs.")
        QMessageBox.information(self, "Venta Cancelada", "La venta ha sido cancelada y el carrito vaciado.")

    def aplicar_descuento(self):
        """Aplica un descuento porcentual al total de la venta."""
        try:
            porcentaje = float(self.input_descuento.text())
            if porcentaje < 0 or porcentaje > 100:
                QMessageBox.warning(self, "Descuento inválido", "Ingrese un porcentaje entre 0 y 100.")
                return
            self.descuento_porcentaje = porcentaje
            total = sum(item["cantidad_unidades"] * item["precio"] for item in self.carrito)
            descuento = total * (porcentaje / 100)
            total_con_descuento = total - descuento
            self.label_descuento.setText(f"Descuento aplicado: {descuento:.2f} Bs.")
            self.label_total.setText(f"Total: {total_con_descuento:.2f} Bs.")
        except Exception:
            QMessageBox.warning(self, "Error", "Ingrese un porcentaje válido.")

    def vender_todo(self):
        """Procesa la venta de todos los productos en el carrito, actualiza stock y registra el movimiento."""
        if not self.carrito:
            QMessageBox.warning(self, "Carrito Vacío", "Agregue productos al carrito antes de procesar la venta.")
            return
        fecha_mov = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = sum(item["cantidad_unidades"] * item["precio"] for item in self.carrito)
        descuento = total * (self.descuento_porcentaje / 100)
        total_con_descuento = total - descuento
        for item in self.carrito:
            # Obtener datos actuales del producto
            self.cursor.execute("SELECT cajas, unidades, stock FROM productos WHERE id_producto = ?", (item["id"],))
            result = self.cursor.fetchone()
            if not result:
                continue
            cajas_actual, unidades_por_caja, stock_actual = result

            if item["tipo"] == "Por caja":
                # Descontar cajas y stock
                nuevas_cajas = cajas_actual - item["cantidad"]
                nuevas_unidades = unidades_por_caja
                nuevas_stock = nuevas_cajas * nuevas_unidades
                self.cursor.execute(
                    "UPDATE productos SET cajas = ?, stock = ? WHERE id_producto = ?",
                    (nuevas_cajas, nuevas_stock, item["id"])
                )
            else:  # Por unidad
                # Descontar unidades y ajustar cajas si corresponde
                unidades_vendidas = item["cantidad"]
                total_unidades = cajas_actual * unidades_por_caja if cajas_actual and unidades_por_caja else stock_actual
                nuevas_total_unidades = total_unidades - unidades_vendidas

                if cajas_actual and unidades_por_caja:
                    nuevas_cajas = nuevas_total_unidades // unidades_por_caja
                    nuevas_unidades = nuevas_total_unidades % unidades_por_caja
                    # Si hay unidades sueltas, se guardan en stock y cajas
                    self.cursor.execute(
                        "UPDATE productos SET cajas = ?, unidades = ?, stock = ? WHERE id_producto = ?",
                        (nuevas_cajas, nuevas_unidades, nuevas_total_unidades, item["id"])
                    )
                else:
                    # Solo descontar del stock si no hay cajas configuradas
                    self.cursor.execute(
                        "UPDATE productos SET stock = ? WHERE id_producto = ?",
                        (nuevas_total_unidades, item["id"])
                    )

            # Registrar movimiento
            self.cursor.execute(
                "INSERT INTO movimientos_inventario (codigo_producto, tipo_movimiento, cantidad, fecha_movimiento, observaciones, usuario) VALUES (?, ?, ?, ?, ?, ?)",
                (item["codigo"], "venta", item["cantidad"], fecha_mov, "Venta realizada desde sistema admin", "admin")
            )
        self.conexion.commit()
        self.carrito = []
        self.tabla_carrito.setRowCount(0)
        self.label_total.setText("Total: 0.00 Bs.")
        self.label_descuento.setText("Descuento aplicado: 0.00 Bs.")
        QMessageBox.information(self, "Venta procesada", f"Venta realizada correctamente.\nTotal con descuento: {total_con_descuento:.2f} Bs.")
        self.cargar_todos_productos()

    def calcular_cambio(self):
        """Calcula el cambio y muestra la cantidad y billetes sugeridos."""
        try:
            pago = float(self.input_pago.text())
        except Exception:
            QMessageBox.warning(self, "Pago inválido", "Ingrese un monto válido.")
            return
        total = 0.0
        try:
            total = float(self.label_total.text().replace("Total: ", "").replace("Bs.", "").replace("$", "").strip())
        except Exception:
            pass
        if pago < total:
            QMessageBox.warning(self, "Pago insuficiente", "El pago es menor al total de la venta.")
            return
        cambio = round(pago - total, 2)
        billetes = [200, 100, 50, 20, 10]
        desglose = []
        restante = cambio
        for b in billetes:
            cantidad = int(restante // b)
            if cantidad > 0:
                desglose.append(f"{cantidad} x {b} Bs.")
                restante -= cantidad * b
        restante = round(restante, 2)
        mensaje = f"Cambio: {cambio:.2f} Bs."
        if desglose:
            mensaje += " | Billetes: " + ", ".join(desglose)
        if restante > 0:
            mensaje += f" | Resto: {restante:.2f} Bs. (entregar en monedas)"
        self.label_cambio.setText(mensaje)

    def abrir_script(self, script):
        try:
            if self.conexion:
                self.conexion.close()
        except Exception:
            pass
        subprocess.Popen([sys.executable, script])
        QApplication.quit()

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
    app = QApplication(sys.argv)
    ventana = VentasWindow()
    ventana.showMaximized()
    sys.exit(app.exec_())