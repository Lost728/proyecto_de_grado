import sys
import sqlite3
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QSpinBox, QHeaderView, QComboBox, QListWidget, QListWidgetItem
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
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Código", "Precio", "Cajas", "Unidades/Caja", "Stock Total"
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

        # Botón de menú principal
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; font-size: 14px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        main_layout.addWidget(btn_menu, alignment=Qt.AlignLeft)

        # Botón y formulario de devoluciones
        devol_layout = QHBoxLayout()
        btn_devolucion = QPushButton("Registrar Devolución")
        btn_devolucion.setStyleSheet("background-color: #e0e7ef; font-weight: bold;")
        btn_devolucion.clicked.connect(self.mostrar_formulario_devolucion)
        devol_layout.addWidget(btn_devolucion)
        main_layout.addLayout(devol_layout)

        self.tabla.selectionModel().selectionChanged.connect(self.actualizar_spinbox)
        self.cargar_todos_productos()

    def cargar_todos_productos(self):
        """Carga todos los productos con stock disponible en la tabla principal."""
        self.cursor.execute("SELECT id_producto, nombre, codigo, precio, cajas, unidades, stock FROM productos WHERE stock > 0")
        resultados = self.cursor.fetchall()
        self.mostrar_productos(resultados)
        self.spin_cantidad.setMaximum(1)

    def buscar_producto(self):
        """Busca productos por nombre o código según el texto ingresado en el buscador."""
        texto = self.input_busqueda.text().strip()
        if not texto:
            self.cargar_todos_productos()
            return
        sql = """
            SELECT id_producto, nombre, codigo, precio, stock
            FROM productos
            WHERE stock > 0 AND (
                nombre LIKE ? OR codigo LIKE ?
            )
        """
        like = f"%{texto}%"
        self.cursor.execute(sql, (like, like))
        resultados = self.cursor.fetchall()
        self.mostrar_productos(resultados)

    def mostrar_productos(self, resultados):
        """Muestra los productos en la tabla principal con cajas, unidades y stock total."""
        self.tabla.setRowCount(0)
        for row_num, row_data in enumerate(resultados):
            self.tabla.insertRow(row_num)
            id_producto, nombre, codigo, precio, cajas, unidades, stock = row_data
            # Calcula el stock total: si hay cajas y unidades, stock = cajas * unidades; si no, usa stock
            if cajas and unidades and cajas > 0 and unidades > 0:
                stock_total = cajas * unidades
            else:
                stock_total = stock
            self.tabla.setItem(row_num, 0, QTableWidgetItem(str(nombre)))
            self.tabla.setItem(row_num, 1, QTableWidgetItem(str(codigo)))
            self.tabla.setItem(row_num, 2, QTableWidgetItem(f"{precio:.2f} Bs."))
            self.tabla.setItem(row_num, 3, QTableWidgetItem(str(cajas if cajas else "")))
            self.tabla.setItem(row_num, 4, QTableWidgetItem(str(unidades if unidades else "")))
            self.tabla.setItem(row_num, 5, QTableWidgetItem(str(stock_total)))
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

    def vender_todo(self):
        """Procesa la venta de todos los productos en el carrito, actualiza stock y registra el movimiento."""
        if not self.carrito:
            QMessageBox.warning(self, "Carrito Vacío", "Agregue productos al carrito antes de procesar la venta.")
            return
        fecha_mov = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        QMessageBox.information(self, "Venta procesada", "Venta realizada correctamente.")
        self.cargar_todos_productos()

    def mostrar_formulario_devolucion(self):
        from PyQt5.QtWidgets import (
            QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QPushButton, QSpinBox, QListWidget, QListWidgetItem
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar Devolución")
        dialog.setMinimumWidth(400)
        form = QFormLayout(dialog)

        input_codigo = QLineEdit()
        input_codigo.setPlaceholderText("Código del producto")
        form.addRow("Código:", input_codigo)

        input_nombre = QLineEdit()
        input_nombre.setPlaceholderText("Nombre del producto")
        form.addRow("Nombre producto:", input_nombre)

        # Lista para autocompletar
        lista_productos = QListWidget()
        lista_productos.setMaximumHeight(80)
        form.addRow("Coincidencias:", lista_productos)

        def buscar_productos():
            codigo = input_codigo.text().strip()
            nombre = input_nombre.text().strip()
            query = "SELECT id_producto, nombre, codigo FROM productos WHERE 1=1"
            params = []
            if codigo:
                query += " AND codigo LIKE ?"
                params.append(f"%{codigo}%")
            if nombre:
                query += " AND nombre LIKE ?"
                params.append(f"%{nombre}%")
            self.cursor.execute(query, params)
            productos = self.cursor.fetchall()
            lista_productos.clear()
            for id_producto, nombre_p, codigo_p in productos:
                item = QListWidgetItem(f"{nombre_p} (Código: {codigo_p})")
                item.setData(Qt.UserRole, (id_producto, nombre_p, codigo_p))
                lista_productos.addItem(item)

        input_codigo.textChanged.connect(buscar_productos)
        input_nombre.textChanged.connect(buscar_productos)

        def autocompletar_producto(item):
            id_producto, nombre_p, codigo_p = item.data(Qt.UserRole)
            input_codigo.setText(codigo_p)
            input_nombre.setText(nombre_p)
            lista_productos.clear()

        lista_productos.itemClicked.connect(autocompletar_producto)

        spin_cantidad = QSpinBox()
        spin_cantidad.setMinimum(1)
        spin_cantidad.setMaximum(1000)
        form.addRow("Cantidad a devolver:", spin_cantidad)

        input_motivo = QTextEdit()
        input_motivo.setPlaceholderText("Motivo de la devolución")
        input_motivo.setFixedHeight(40)
        form.addRow("Motivo:", input_motivo)

        combo_tipo_devolucion = QComboBox()
        combo_tipo_devolucion.addItems(["Devolución simple", "Devolución por defecto"])
        form.addRow("Tipo de devolución:", combo_tipo_devolucion)

        combo_empleado = QComboBox()
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        for id_empleado, nombre in self.cursor.fetchall():
            combo_empleado.addItem(f"{nombre} (ID:{id_empleado})", id_empleado)
        form.addRow("Empleado:", combo_empleado)

        btn_registrar = QPushButton("Registrar")
        btn_registrar.setStyleSheet("background-color: #FFD700; font-weight: bold;")
        form.addRow(btn_registrar)

        def buscar_id_producto(codigo, nombre):
            if codigo:
                self.cursor.execute("SELECT id_producto FROM productos WHERE codigo = ?", (codigo,))
                result = self.cursor.fetchone()
                if result:
                    return result[0]
            if nombre:
                self.cursor.execute("SELECT id_producto FROM productos WHERE nombre LIKE ?", (f"%{nombre}%",))
                result = self.cursor.fetchone()
                if result:
                    return result[0]
            return None

        def registrar_devolucion():
            codigo = input_codigo.text().strip()
            nombre = input_nombre.text().strip()
            cantidad = spin_cantidad.value()
            motivo = input_motivo.toPlainText().strip()
            tipo_devolucion = combo_tipo_devolucion.currentText()
            id_empleado = combo_empleado.currentData()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not (codigo or nombre) or not motivo or not id_empleado:
                QMessageBox.warning(dialog, "Campos requeridos", "Complete código o nombre, motivo y empleado.")
                return

            id_producto = buscar_id_producto(codigo, nombre)
            if not id_producto:
                QMessageBox.warning(dialog, "Producto no encontrado", "No existe un producto con ese código o nombre.")
                return

            try:
                # Registrar la devolución en la tabla devoluciones
                self.cursor.execute(
                    "INSERT INTO devoluciones (id_producto, cantidad, motivo, fecha_devolucion, id_empleado) VALUES (?, ?, ?, ?, ?)",
                    (id_producto, cantidad, motivo, fecha, id_empleado)
                )
                self.conexion.commit()

                # Si es devolución simple, sumar la cantidad al stock del producto (y actualizar cajas/unidades si corresponde)
                if tipo_devolucion == "Devolución simple":
                    self.cursor.execute("SELECT cajas, unidades, stock FROM productos WHERE id_producto = ?", (id_producto,))
                    cajas_actual, unidades_actual, stock_actual = self.cursor.fetchone()
                    nuevo_stock = stock_actual + cantidad
                    if cajas_actual and unidades_actual and cajas_actual > 0 and unidades_actual > 0:
                        nuevas_cajas = nuevo_stock // unidades_actual
                        nuevas_unidades = nuevo_stock % unidades_actual
                        self.cursor.execute(
                            "UPDATE productos SET cajas = ?, unidades = ?, stock = ? WHERE id_producto = ?",
                            (nuevas_cajas, nuevas_unidades, nuevo_stock, id_producto)
                        )
                    else:
                        self.cursor.execute(
                            "UPDATE productos SET stock = ? WHERE id_producto = ?",
                            (nuevo_stock, id_producto)
                        )
                    self.conexion.commit()
                    QMessageBox.information(dialog, "Devolución registrada", f"La devolución se registró y se reincorporaron {cantidad} producto(s) al stock.")
                else:
                    QMessageBox.information(dialog, "Devolución registrada", "La devolución se registró como defectuosa y no se reincorporó al stock.")

                dialog.accept()
                self.cargar_todos_productos()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"No se pudo registrar la devolución:\n{e}")

        btn_registrar.clicked.connect(registrar_devolucion)
        dialog.exec_()

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