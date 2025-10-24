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
        self.cliente_actual = None
        self.descuento_cliente = 0.0
        self.id_empleado = None
        
        # La tabla ventas ya existe, no necesitamos crearla
        # Solo verificamos si existe la tabla clientes
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                CI TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                celular TEXT,
                puntos_acumulados INTEGER DEFAULT 0,
                descuento REAL DEFAULT 0.0,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conexion.commit()

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        # Aplicar tema visual consistente (púrpura/rosa/cian)
        try:
            self.aplicar_tema()
        except Exception:
            pass

        # Título
        title_label = QLabel("Sistema de Ventas")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Sección de Cliente
        cliente_layout = QHBoxLayout()
        
        # Tipo de búsqueda
        cliente_layout.addWidget(QLabel("Buscar por:"))
        self.combo_tipo_busqueda = QComboBox()
        self.combo_tipo_busqueda.addItems(["CI", "Nombre", "Celular"])
        self.combo_tipo_busqueda.currentIndexChanged.connect(self.cambiar_tipo_busqueda)
        cliente_layout.addWidget(self.combo_tipo_busqueda)
        
        # Campo de búsqueda
        self.input_busqueda_cliente = QLineEdit()
        self.input_busqueda_cliente.setPlaceholderText("Ingrese CI del cliente")
        cliente_layout.addWidget(self.input_busqueda_cliente)
        
        # Botones
        btn_buscar_cliente = QPushButton("Buscar Cliente")
        btn_buscar_cliente.clicked.connect(self.buscar_cliente)
        cliente_layout.addWidget(btn_buscar_cliente)
        
        btn_registrar_cliente = QPushButton("Registrar Nuevo Cliente")
        btn_registrar_cliente.clicked.connect(self.abrir_registro_cliente)
        cliente_layout.addWidget(btn_registrar_cliente)
        
        # Información del cliente
        cliente_info_layout = QHBoxLayout()
        self.label_info_cliente = QLabel("Cliente: No registrado")
        cliente_info_layout.addWidget(self.label_info_cliente)
        
        self.label_puntos_cliente = QLabel("Puntos: 0")
        cliente_info_layout.addWidget(self.label_puntos_cliente)
        
        self.label_descuento_cliente = QLabel("Descuento: 0%")
        cliente_info_layout.addWidget(self.label_descuento_cliente)
        
        btn_historial_puntos = QPushButton("Ver Historial de Puntos")
        btn_historial_puntos.setStyleSheet("background-color: #00b894; color: white; font-size: 14px;")
        btn_historial_puntos.clicked.connect(lambda: self.mostrar_historial_puntos(self.cliente_actual['ci']) if self.cliente_actual else QMessageBox.information(self, "Sin cliente", "Primero seleccione un cliente."))
        cliente_info_layout.addWidget(btn_historial_puntos)
        
        btn_ver_devoluciones = QPushButton("Ver Devoluciones")
        btn_ver_devoluciones.setStyleSheet("background-color: #d35400; color: white; font-size: 14px;")
        btn_ver_devoluciones.clicked.connect(self.abrir_devoluciones_py)
        cliente_info_layout.addWidget(btn_ver_devoluciones)
        
        btn_reintegrar_devolucion = QPushButton("Reintegrar Devolución")
        btn_reintegrar_devolucion.setStyleSheet("background-color: #0984e3; color: white; font-size: 14px;")
        btn_reintegrar_devolucion.clicked.connect(self.reintegrar_devolucion)
        cliente_info_layout.addWidget(btn_reintegrar_devolucion)
        
        # Agregar los layouts al layout principal
        main_layout.addLayout(cliente_layout)
        main_layout.addLayout(cliente_info_layout)

        # Barra de navegación (reorganizada)
        nav_layout = QHBoxLayout()
        # Botones de navegación a la izquierda
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

        nav_layout.addStretch()  # empuja las siguientes acciones a la derecha

        # Acciones importantes a la derecha
        btn_ventas = QPushButton("Ventas")
        btn_ventas.clicked.connect(lambda: self.abrir_script("venta_registro.py"))
        nav_layout.addWidget(btn_ventas)

        btn_devoluciones = QPushButton("Registrar Devolución")
        btn_devoluciones.setStyleSheet("background-color: #e17055; color: white; font-size: 14px;")
        btn_devoluciones.clicked.connect(self.abrir_miniventana_devolucion)
        nav_layout.addWidget(btn_devoluciones)

        # Botón Cerrar Día ahora en la barra superior a la derecha
        btn_cerrar_dia = QPushButton("Cerrar Día")
        btn_cerrar_dia.setStyleSheet("background-color: #636e72; color: white; font-size: 14px;")
        btn_cerrar_dia.clicked.connect(self.cerrar_dia)
        nav_layout.addWidget(btn_cerrar_dia)

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
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Código", "Precio", "Unidades Disponibles", "ID Producto"
        ])
        self.tabla.setColumnWidth(0, 200)  # Nombre
        self.tabla.setColumnWidth(1, 100)  # Código
        self.tabla.setColumnWidth(2, 90)   # Precio
        self.tabla.setColumnWidth(3, 110)  # Unidades Disponibles
        self.tabla.setColumnWidth(4, 80)   # ID Producto (oculto para uso interno)
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
        self.combo_tipo_venta.addItems(["Por unidad"])
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

        # (Botones inferiores eliminados por petición: "Menú Principal" y el duplicado "Registrar Devolución")

        self.tabla.selectionModel().selectionChanged.connect(self.actualizar_spinbox)
        self.cargar_todos_productos()
        self.seleccionar_empleado()

    def cargar_todos_productos(self):
        """Carga todos los productos de la tabla productos."""
        sql = """
            SELECT id_producto, nombre, codigo, precio, unidades 
            FROM productos 
            WHERE unidades > 0
            ORDER BY nombre
        """
        self.cursor.execute(sql)
        resultados = self.cursor.fetchall()
        self.mostrar_productos(resultados)
        self.spin_cantidad.setMaximum(1)

    def buscar_producto(self):
        """Busca productos por nombre o código en la tabla productos."""
        texto = self.input_busqueda.text().strip()
        if not texto:
            self.cargar_todos_productos()
            return
        like = f"%{texto}%"
        sql = """
            SELECT id_producto, nombre, codigo, precio, unidades
            FROM productos
            WHERE (nombre LIKE ? OR codigo LIKE ?) AND unidades > 0
            ORDER BY nombre
        """
        self.cursor.execute(sql, (like, like))
        resultados = self.cursor.fetchall()
        self.mostrar_productos(resultados)

    def mostrar_productos(self, resultados):
        """Muestra los productos en la tabla principal."""
        self.tabla.setRowCount(0)
        for row_num, row_data in enumerate(resultados):
            id_producto, nombre, codigo, precio, unidades = row_data
            
            self.tabla.insertRow(row_num)
            self.tabla.setItem(row_num, 0, QTableWidgetItem(str(nombre)))
            self.tabla.setItem(row_num, 1, QTableWidgetItem(str(codigo)))
            self.tabla.setItem(row_num, 2, QTableWidgetItem(f"{precio:.2f} Bs."))
            self.tabla.setItem(row_num, 3, QTableWidgetItem(str(unidades)))
            self.tabla.setItem(row_num, 4, QTableWidgetItem(str(id_producto)))
            
        self.tabla.resizeColumnsToContents()
        # Ocultar la columna de ID Producto (es solo para uso interno)
        self.tabla.setColumnHidden(4, True)
        self.spin_cantidad.setMaximum(1)

    def actualizar_spinbox(self):
        """Actualiza el máximo del spinbox de cantidad según el stock del producto seleccionado."""
        selected = self.tabla.currentRow()
        if selected == -1:
            self.spin_cantidad.setMaximum(1)
            return
        try:
            stock = int(self.tabla.item(selected, 3).text())
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
            unidades_disponibles = int(self.tabla.item(selected, 3).text())
            producto_id = int(self.tabla.item(selected, 4).text())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al leer los datos del producto seleccionado: {str(e)}")
            return

        cantidad = self.spin_cantidad.value()
        tipo_venta = self.combo_tipo_venta.currentText()

        # Ahora solo tenemos venta por unidades
        if cantidad > unidades_disponibles:
            QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficientes unidades de '{nombre}'.")
            return
        
        cantidad_unidades = cantidad
        descripcion = f"{cantidad_unidades} unidad(es)"

        # Verifica si ya está en el carrito
        for item in self.carrito:
            if item["id"] == producto_id:
                if item["cantidad"] + cantidad > item["stock"]:
                    QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficiente stock de '{nombre}'.")
                    return
                item["cantidad"] += cantidad
                item["cantidad_unidades"] += cantidad_unidades
                item["descripcion"] = f"{item['cantidad_unidades']} unidad(es)"
                self.actualizar_tabla_carrito()
                self.spin_cantidad.setValue(1)
                return

        self.carrito.append({
            "id": producto_id,
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "cantidad_unidades": cantidad_unidades,
            "stock": unidades_disponibles,
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
            # Si hay un descuento de cliente registrado, usar ese valor como predeterminado
            if self.cliente_actual and self.descuento_cliente > 0:
                porcentaje = self.descuento_cliente
                self.input_descuento.setText(str(porcentaje))
            else:
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
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Ingrese un porcentaje válido. Error: {str(e)}")
            
    def cambiar_tipo_busqueda(self):
        """Cambia el placeholder del campo de búsqueda según el tipo seleccionado."""
        tipo_busqueda = self.combo_tipo_busqueda.currentText()
        if tipo_busqueda == "CI":
            self.input_busqueda_cliente.setPlaceholderText("Ingrese CI del cliente")
        elif tipo_busqueda == "Nombre":
            self.input_busqueda_cliente.setPlaceholderText("Ingrese nombre o apellido del cliente")
        elif tipo_busqueda == "Celular":
            self.input_busqueda_cliente.setPlaceholderText("Ingrese número de celular del cliente")
    
    def buscar_cliente(self):
        """Busca un cliente según el criterio seleccionado y muestra su información."""
        tipo_busqueda = self.combo_tipo_busqueda.currentText()
        valor_busqueda = self.input_busqueda_cliente.text().strip()
        
        if not valor_busqueda:
            QMessageBox.warning(self, "Campo vacío", f"Ingrese un {tipo_busqueda} válido para buscar.")
            return
        
        # Preparar la consulta según el tipo de búsqueda
        if tipo_busqueda == "CI":
            sql = "SELECT CI, nombre, apellidos, puntos_acumulados, descuento FROM clientes WHERE CI = ?"
            params = (valor_busqueda,)
        elif tipo_busqueda == "Nombre":
            sql = "SELECT CI, nombre, apellidos, puntos_acumulados, descuento FROM clientes WHERE nombre LIKE ? OR apellidos LIKE ?"
            valor_like = f"%{valor_busqueda}%"
            params = (valor_like, valor_like)
        elif tipo_busqueda == "Celular":
            sql = "SELECT CI, nombre, apellidos, puntos_acumulados, descuento FROM clientes WHERE celular = ?"
            params = (valor_busqueda,)
        
        # Ejecutar la consulta
        self.cursor.execute(sql, params)
        resultados = self.cursor.fetchall()
        
        # Si no hay resultados
        if not resultados:
            QMessageBox.information(self, "Cliente no encontrado", 
                                  "No se encontró ningún cliente con ese criterio. Las ventas se realizarán sin descuento.")
            self.cliente_actual = None
            self.descuento_cliente = 0.0
            self.label_info_cliente.setText("Cliente: No registrado")
            self.label_puntos_cliente.setText("Puntos: 0")
            self.label_descuento_cliente.setText("Descuento: 0%")
            return
        
        # Si hay múltiples resultados (para búsqueda por nombre)
        if len(resultados) > 1:
            self.mostrar_seleccion_cliente(resultados)
            return
            
        # Si hay un solo resultado
        ci, nombre, apellidos, puntos, descuento = resultados[0]
        self.seleccionar_cliente(ci, nombre, apellidos, puntos, descuento)
    
    def mostrar_seleccion_cliente(self, resultados):
        """Muestra un diálogo para seleccionar un cliente cuando hay múltiples resultados."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
        
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Seleccionar Cliente")
        dialogo.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Instrucciones
        layout.addWidget(QLabel("Se encontraron varios clientes. Por favor, seleccione uno:"))
        
        # Lista de clientes
        lista_clientes = QListWidget()
        for ci, nombre, apellidos, puntos, descuento in resultados:
            item = QListWidgetItem(f"{nombre} {apellidos} - CI: {ci} - Puntos: {puntos} - Descuento: {descuento}%")
            item.setData(Qt.UserRole, (ci, nombre, apellidos, puntos, descuento))
            lista_clientes.addItem(item)
        
        layout.addWidget(lista_clientes)
        
        # Botón de seleccionar
        btn_seleccionar = QPushButton("Seleccionar Cliente")
        
        def seleccionar():
            item_seleccionado = lista_clientes.currentItem()
            if item_seleccionado:
                datos = item_seleccionado.data(Qt.UserRole)
                ci, nombre, apellidos, puntos, descuento = datos
                self.seleccionar_cliente(ci, nombre, apellidos, puntos, descuento)
                dialogo.accept()
            else:
                QMessageBox.warning(dialogo, "Selección requerida", "Por favor, seleccione un cliente de la lista.")
        
        btn_seleccionar.clicked.connect(seleccionar)
        layout.addWidget(btn_seleccionar)
        
        dialogo.setLayout(layout)
        dialogo.exec_()
        
    def seleccionar_cliente(self, ci, nombre, apellidos, puntos, descuento):
        self.cliente_actual = {
            'ci': ci,
            'nombre': nombre,
            'apellidos': apellidos,
            'puntos': puntos,
            'descuento': descuento
        }
        nivel, porcentaje = self.calcular_nivel_puntaje(puntos)
        self.descuento_cliente = porcentaje
        self.label_info_cliente.setText(f"Cliente: {nombre} {apellidos}")
        self.label_puntos_cliente.setText(f"Puntos: {puntos} | Nivel: {nivel}")
        self.label_descuento_cliente.setText(f"Descuento: {porcentaje}%")
        self.input_descuento.setText(str(porcentaje))
        self.descuento_porcentaje = porcentaje
        self.mostrar_barra_progreso(puntos)
        
        # Aplicar descuento automáticamente si hay uno disponible
        if descuento > 0:
            self.input_descuento.setText(str(descuento))
            self.aplicar_descuento()
        
        QMessageBox.information(self, "Cliente Seleccionado", 
                              f"Cliente: {nombre} {apellidos}\nCI: {ci}\nPuntos: {puntos}\nDescuento: {descuento}%")
    
    def calcular_nivel_puntaje(self, puntos):
        """Devuelve el nivel y porcentaje de descuento según los puntos acumulados."""
        if puntos >= 1501:
            return "Oro", 10
        elif puntos >= 501:
            return "Plata", 5
        else:
            return "Bronce", 2

    def mostrar_barra_progreso(self, puntos):
        """Muestra una barra de progreso y mensaje motivacional en la interfaz."""
        from PyQt5.QtWidgets import QProgressBar
        if not hasattr(self, 'barra_puntaje'):
            self.barra_puntaje = QProgressBar()
            self.centralWidget().layout().addWidget(self.barra_puntaje)
        nivel, _ = self.calcular_nivel_puntaje(puntos)
        if nivel == "Bronce":
            max_puntos = 500
        elif nivel == "Plata":
            max_puntos = 1500
        else:
            max_puntos = 2000
        self.barra_puntaje.setMaximum(max_puntos)
        self.barra_puntaje.setValue(puntos)
        self.barra_puntaje.setFormat(f"Nivel: {nivel} | Puntos: {puntos} / {max_puntos}")

    def mostrar_historial_puntos(self, ci):
        """Muestra el historial de acumulación y canje de puntos del cliente."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle("Historial de puntos y canjes")
        layout = QVBoxLayout()
        self.cursor.execute("SELECT fecha_venta, total_venta FROM ventas WHERE id_cliente = ? ORDER BY fecha_venta DESC", (ci,))
        ventas = self.cursor.fetchall()
        self.cursor.execute("SELECT premios_canjeados FROM clientes WHERE CI = ?", (ci,))
        row = self.cursor.fetchone()
        premios = row[0] if row else 0
        layout.addWidget(QLabel(f"Premios canjeados: {premios}"))
        for fecha, total in ventas:
            layout.addWidget(QLabel(f"Venta: {fecha} | Monto: {total} Bs."))
        dialog.setLayout(layout)
        dialog.exec_()

    def actualizar_puntos_cliente(self, total_compra):
        if not self.cliente_actual:
            return
        ci = self.cliente_actual['ci']
        # Sistema escalable: 2 puntos si la compra supera 500 Bs, 1 punto si no
        puntos_extra = 2 if total_compra >= 500 else 1
        self.cursor.execute("SELECT puntos_acumulados, premios_canjeados FROM clientes WHERE CI = ?", (ci,))
        row = self.cursor.fetchone()
        puntos_actuales = row[0] if row else 0
        premios_canjeados = row[1] if row else 0
        total_puntos = puntos_actuales + puntos_extra
        self.cursor.execute(
            "UPDATE clientes SET puntos_acumulados = ? WHERE CI = ?",
            (total_puntos, ci)
        )
        self.conexion.commit()
        self.cliente_actual['puntos'] = total_puntos
        nivel, porcentaje = self.calcular_nivel_puntaje(total_puntos)
        self.label_puntos_cliente.setText(f"Puntos: {total_puntos} | Nivel: {nivel}")
        self.label_descuento_cliente.setText(f"Descuento: {porcentaje}%")
        self.input_descuento.setText(str(porcentaje))
        self.descuento_porcentaje = porcentaje
        self.mostrar_barra_progreso(total_puntos)
        QMessageBox.information(self, "Puntos Acumulados", f"El cliente ha ganado {puntos_extra} punto(s).\nTotal de puntos: {total_puntos}\nNivel: {nivel}\nDescuento: {porcentaje}%")

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
            self.cursor.execute("SELECT unidades FROM productos WHERE id_producto = ?", (item["id"],))
            result = self.cursor.fetchone()
            if not result:
                continue
                
            unidades_actual = result[0]
            
            # Descontar unidades
            unidades_vendidas = item["cantidad"]
            nuevas_unidades = unidades_actual - unidades_vendidas
            
            # Actualizar inventario
            self.cursor.execute(
                "UPDATE productos SET unidades = ? WHERE id_producto = ?",
                (nuevas_unidades, item["id"])
            )

            # Registrar movimiento
            self.cursor.execute(
                "INSERT INTO movimientos_inventario (codigo_producto, tipo_movimiento, cantidad, fecha_movimiento, observaciones, usuario) VALUES (?, ?, ?, ?, ?, ?)",
                (item["codigo"], "venta", item["cantidad"], fecha_mov, "Venta realizada desde sistema admin", "admin")
            )
        # Registrar la venta y actualizar los puntos del cliente si está registrado
        try:
            # Registrar la venta con información básica (ahora con id_empleado)
            self.cursor.execute(
                "INSERT INTO ventas (fecha_venta, total_venta, id_empleado) VALUES (?, ?, ?)",
                (fecha_mov, total_con_descuento, self.id_empleado)
            )
            
            # Si hay un cliente registrado, actualizar sus puntos
            if self.cliente_actual:
                self.actualizar_puntos_cliente(total_con_descuento)
            
            # Nota: No estamos usando id_cliente en la tabla ventas por ahora
            # debido a la incompatibilidad entre el tipo de dato CI (TEXT) y id_cliente (INTEGER)
            
        except Exception as e:
            # Si hay un error al registrar la venta, mostrar mensaje y continuar
            print(f"Error al registrar la venta: {e}")
            QMessageBox.warning(self, "Advertencia", 
                             f"La venta se ha procesado pero hubo un error al guardar en el historial: {e}")
            
        self.conexion.commit()
        self.carrito = []
        self.tabla_carrito.setRowCount(0)
        self.label_total.setText("Total: 0.00 Bs.")
        self.label_descuento.setText("Descuento aplicado: 0.00 Bs.")
        
        mensaje = f"Venta realizada correctamente.\nTotal con descuento: {total_con_descuento:.2f} Bs."
        if self.cliente_actual:
            mensaje += f"\nCliente: {self.cliente_actual['nombre']} {self.cliente_actual['apellidos']}"
        
        QMessageBox.information(self, "Venta procesada", mensaje)
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
        
    def abrir_registro_cliente(self):
        """Abre la ventana de registro de nuevo cliente."""
        # Usamos una implementación diferente para que no cierre la ventana actual
        try:
            script_path = os.path.join(os.path.dirname(__file__), "registrar_cliente.py")
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el registro de clientes: {str(e)}")

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

    def abrir_miniventana_devolucion(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QSpinBox, QTextEdit, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QLabel, QHBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar Devolución")
        dialog.setMinimumSize(400, 400)
        layout = QVBoxLayout()
        form = QFormLayout()

        # Buscador de productos
        buscador_layout = QHBoxLayout()
        buscador_label = QLabel("Buscar producto:")
        buscador_layout.addWidget(buscador_label)
        input_busqueda_producto = QLineEdit()
        input_busqueda_producto.setPlaceholderText("Nombre o código...")
        buscador_layout.addWidget(input_busqueda_producto)
        btn_buscar_producto = QPushButton("Buscar")
        buscador_layout.addWidget(btn_buscar_producto)
        layout.addLayout(buscador_layout)

        lista_productos = QListWidget()
        layout.addWidget(lista_productos)

        def buscar_producto():
            texto = input_busqueda_producto.text().strip()
            lista_productos.clear()
            if not texto:
                self.cursor.execute("SELECT id_producto, nombre, codigo FROM productos")
                resultados = self.cursor.fetchall()
            else:
                like = f"%{texto}%"
                self.cursor.execute("SELECT id_producto, nombre, codigo FROM productos WHERE nombre LIKE ? OR codigo LIKE ?", (like, like))
                resultados = self.cursor.fetchall()
            for id_prod, nombre, codigo in resultados:
                item = QListWidgetItem(f"{nombre} [Código: {codigo}] [ID: {id_prod}]")
                item.setData(Qt.UserRole, id_prod)
                lista_productos.addItem(item)

        btn_buscar_producto.clicked.connect(buscar_producto)
        input_busqueda_producto.returnPressed.connect(buscar_producto)
        buscar_producto()  # Mostrar todos al abrir

        # Cantidad
        spin_cantidad = QSpinBox()
        spin_cantidad.setMinimum(1)
        form.addRow("Cantidad:", spin_cantidad)
        # Motivo
        input_motivo = QTextEdit()
        input_motivo.setPlaceholderText("Motivo de la devolución")
        form.addRow("Motivo:", input_motivo)
        # Empleado
        combo_empleado = QComboBox()
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        for id_emp, nombre in self.cursor.fetchall():
            combo_empleado.addItem(f"{nombre} [ID: {id_emp}]", id_emp)
        form.addRow("Empleado:", combo_empleado)
        # Botón registrar
        btn_registrar = QPushButton("Registrar devolución")
        def registrar():
            item_seleccionado = lista_productos.currentItem()
            if not item_seleccionado:
                QMessageBox.warning(dialog, "Error", "Debe seleccionar un producto de la lista.")
                return
            id_producto = item_seleccionado.data(Qt.UserRole)
            cantidad = spin_cantidad.value()
            motivo = input_motivo.toPlainText().strip()
            fecha_devolucion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            id_empleado = combo_empleado.currentData()
            if not motivo:
                QMessageBox.warning(dialog, "Error", "Debe ingresar el motivo de la devolución.")
                return
            try:
                self.cursor.execute(
                    "INSERT INTO devoluciones (id_producto, cantidad, motivo, fecha_devolucion, id_empleado) VALUES (?, ?, ?, ?, ?)",
                    (id_producto, cantidad, motivo, fecha_devolucion, id_empleado)
                )
                self.conexion.commit()
                QMessageBox.information(dialog, "Registro exitoso", "La devolución ha sido registrada correctamente.")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"No se pudo registrar la devolución: {str(e)}")
        btn_registrar.clicked.connect(registrar)
        form.addRow(btn_registrar)
        layout.addLayout(form)
        dialog.setLayout(layout)
        dialog.exec_()

    def seleccionar_empleado(self):
        """Selecciona el empleado activo al iniciar la ventana."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Empleado")
        layout = QVBoxLayout()
        label = QLabel("Seleccione el empleado que realizará las ventas hoy:")
        layout.addWidget(label)
        combo = QComboBox()
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        empleados = self.cursor.fetchall()
        for id_emp, nombre in empleados:
            combo.addItem(f"{nombre} [ID: {id_emp}]", id_emp)
        layout.addWidget(combo)
        btn = QPushButton("Confirmar")
        layout.addWidget(btn)
        def confirmar():
            self.id_empleado = combo.currentData()
            dialog.accept()
        btn.clicked.connect(confirmar)
        dialog.setLayout(layout)
        dialog.exec_()

    def cerrar_dia(self):
        """Cierra el día y limpia el empleado activo."""
        self.id_empleado = None
        QMessageBox.information(self, "Día cerrado", "El empleado activo ha sido desregistrado. Puedes seleccionar uno nuevo al iniciar ventas.")

    def crear_botones_extra(self):
        """Agrega el botón para cerrar día en la interfaz principal."""
        btn_cerrar_dia = QPushButton("Cerrar Día")
        btn_cerrar_dia.setStyleSheet("background-color: #636e72; color: white; font-size: 14px;")
        btn_cerrar_dia.clicked.connect(self.cerrar_dia)
        self.centralWidget().layout().addWidget(btn_cerrar_dia)

    def mostrar_devoluciones_cliente(self):
        """Muestra las devoluciones realizadas por el cliente seleccionado."""
        if not self.cliente_actual:
            QMessageBox.information(self, "Sin cliente", "Primero seleccione un cliente.")
            return
        ci = self.cliente_actual['ci']
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle("Devoluciones del cliente")
        layout = QVBoxLayout()
        self.cursor.execute("SELECT fecha_devolucion, motivo, cantidad FROM devoluciones WHERE CI_cliente = ? ORDER BY fecha_devolucion DESC", (ci,))
        devoluciones = self.cursor.fetchall()
        if not devoluciones:
            layout.addWidget(QLabel("No hay devoluciones registradas para este cliente."))
        else:
            for fecha, motivo, cantidad in devoluciones:
                layout.addWidget(QLabel(f"Fecha: {fecha} | Cantidad: {cantidad} | Motivo: {motivo}"))
        dialog.setLayout(layout)
        dialog.exec_()

    def abrir_devoluciones_py(self):
        """Abre devoluciones.py como una miniventana modal."""
        try:
            import importlib.util
            from PyQt5.QtWidgets import QDialog
            script_path = os.path.join(os.path.dirname(__file__), "devoluciones.py")
            spec = importlib.util.spec_from_file_location("devoluciones_mod", script_path)
            devoluciones_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(devoluciones_mod)
            # Instancia la ventana sin argumentos
            if hasattr(devoluciones_mod, "DevolucionesWindow"):
                self.miniventana_devoluciones = devoluciones_mod.DevolucionesWindow()
                self.miniventana_devoluciones.show()
            else:
                QMessageBox.warning(self, "Error", "No se encontró la clase 'DevolucionesWindow' en devoluciones.py.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir devoluciones.py como miniventana: {str(e)}")

    def reintegrar_devolucion(self):
        """Permite reintegrar una devolución al inventario."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle("Reintegrar devolución")
        layout = QVBoxLayout()
        # Buscar devoluciones del cliente
        if not self.cliente_actual:
            QMessageBox.information(self, "Sin cliente", "Primero seleccione un cliente.")
            return
        ci = self.cliente_actual['ci']
        self.cursor.execute("SELECT id_devolucion, id_producto, cantidad, motivo, fecha_devolucion FROM devoluciones WHERE CI_cliente = ? AND reintegrado IS NULL ORDER BY fecha_devolucion DESC", (ci,))
        devoluciones = self.cursor.fetchall()
        if not devoluciones:
            layout.addWidget(QLabel("No hay devoluciones pendientes de reintegrar para este cliente."))
        else:
            combo = QComboBox()
            for id_dev, id_prod, cantidad, motivo, fecha in devoluciones:
                combo.addItem(f"ID: {id_dev} | Producto: {id_prod} | Cantidad: {cantidad} | Motivo: {motivo} | Fecha: {fecha}", id_dev)
            layout.addWidget(combo)
            btn = QPushButton("Reintegrar")
            layout.addWidget(btn)
            def confirmar():
                id_devolucion = combo.currentData()
                # Actualiza la devolución como reintegrada y suma al inventario
                self.cursor.execute("SELECT id_producto, cantidad FROM devoluciones WHERE id_devolucion = ?", (id_devolucion,))
                prod_row = self.cursor.fetchone()
                if prod_row:
                    id_producto, cantidad = prod_row
                    self.cursor.execute("UPDATE productos SET unidades = unidades + ? WHERE id_producto = ?", (cantidad, id_producto))
                    self.cursor.execute("UPDATE devoluciones SET reintegrado = 1 WHERE id_devolucion = ?", (id_devolucion,))
                    self.conexion.commit()
                    QMessageBox.information(dialog, "Reintegrado", "La devolución ha sido reintegrada al inventario.")
                    dialog.accept()
            btn.clicked.connect(confirmar)
        dialog.setLayout(layout)
        dialog.exec_()

    def aplicar_tema(self):
        """Aplica tema púrpura/rosa/cian coherente a la ventana de ventas."""
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #2e0b3a, stop:1 #3a0f5a); }
            QLabel { color: #f1f2f7; }
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8e44ad, stop:1 #c099ff); color: #fff; border-radius:8px; padding:6px 12px; font-weight:600; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6f2a8f, stop:1 #9b59b6); }
            QLineEdit, QComboBox, QSpinBox, QDateEdit { background-color: rgba(255,255,255,0.03); color: #eef3ff; border: 1px solid rgba(255,255,255,0.06); border-radius:6px; padding:4px; }
            QTableWidget { background-color: rgba(255,255,255,0.02); color: #ffffff; gridline-color: rgba(255,255,255,0.05); }
            QHeaderView::section { background: rgba(0,0,0,0.35); color: #fff; }
            QProgressBar { background: rgba(255,255,255,0.03); color: #fff; border-radius:6px; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentasWindow()
    ventana.showMaximized()
    sys.exit(app.exec_())