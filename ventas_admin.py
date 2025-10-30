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
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Aplicar tema visual mejorado
        self.aplicar_tema()

        # Título
        title_label = QLabel("Sistema de Ventas")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("titulo")
        main_layout.addWidget(title_label)
        
        # Sección de Cliente
        cliente_layout = QHBoxLayout()
        cliente_layout.setSpacing(8)
        
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
        btn_registrar_cliente.setObjectName("btnSecundario")
        btn_registrar_cliente.clicked.connect(self.abrir_registro_cliente)
        cliente_layout.addWidget(btn_registrar_cliente)
        
        # Información del cliente
        cliente_info_layout = QHBoxLayout()
        cliente_info_layout.setSpacing(15)
        
        self.label_info_cliente = QLabel("Cliente: No registrado")
        self.label_info_cliente.setObjectName("infoCliente")
        cliente_info_layout.addWidget(self.label_info_cliente)
        
        self.label_puntos_cliente = QLabel("Puntos: 0")
        self.label_puntos_cliente.setObjectName("infoPuntos")
        cliente_info_layout.addWidget(self.label_puntos_cliente)
        
        self.label_descuento_cliente = QLabel("Descuento: 0%")
        self.label_descuento_cliente.setObjectName("infoDescuento")
        cliente_info_layout.addWidget(self.label_descuento_cliente)
        
        btn_historial_puntos = QPushButton("Ver Historial de Puntos")
        btn_historial_puntos.setObjectName("btnVerde")
        btn_historial_puntos.clicked.connect(lambda: self.mostrar_historial_puntos(self.cliente_actual['ci']) if self.cliente_actual else QMessageBox.information(self, "Sin cliente", "Primero seleccione un cliente."))
        cliente_info_layout.addWidget(btn_historial_puntos)
        
        btn_ver_devoluciones = QPushButton("Ver Devoluciones")
        btn_ver_devoluciones.setObjectName("btnNaranja")
        btn_ver_devoluciones.clicked.connect(self.abrir_devoluciones_py)
        cliente_info_layout.addWidget(btn_ver_devoluciones)
        
        btn_reintegrar_devolucion = QPushButton("Reintegrar Devolución")
        btn_reintegrar_devolucion.setObjectName("btnAzul")
        btn_reintegrar_devolucion.clicked.connect(self.reintegrar_devolucion)
        cliente_info_layout.addWidget(btn_reintegrar_devolucion)
        
        # Agregar los layouts al layout principal
        main_layout.addLayout(cliente_layout)
        main_layout.addLayout(cliente_info_layout)

        # Barra de navegación
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        # Botones de navegación a la izquierda
        btn_productos = QPushButton("Ver Productos")
        btn_productos.setObjectName("btnNavegacion")
        btn_productos.clicked.connect(lambda: self.abrir_script("ver_productos.py"))
        nav_layout.addWidget(btn_productos)
        
        btn_nuevo_producto = QPushButton("Nuevo Producto")
        btn_nuevo_producto.setObjectName("btnNavegacion")
        btn_nuevo_producto.clicked.connect(lambda: self.abrir_script("insertar_producto.py"))
        nav_layout.addWidget(btn_nuevo_producto)
        
        btn_empleados = QPushButton("Empleados")
        btn_empleados.setObjectName("btnNavegacion")
        btn_empleados.clicked.connect(lambda: self.abrir_script(os.path.join("empleados", "ver_empleado.py")))
        nav_layout.addWidget(btn_empleados)
        
        btn_nuevo_empleado = QPushButton("Nuevo Empleado")
        btn_nuevo_empleado.setObjectName("btnNavegacion")
        btn_nuevo_empleado.clicked.connect(lambda: self.abrir_script(os.path.join("empleados", "insertar_empleado.py")))
        nav_layout.addWidget(btn_nuevo_empleado)

        nav_layout.addStretch()

        # Acciones importantes a la derecha
        btn_ventas = QPushButton("Ventas")
        btn_ventas.setObjectName("btnImportante")
        btn_ventas.clicked.connect(lambda: self.abrir_script("venta_registro.py"))
        nav_layout.addWidget(btn_ventas)

        btn_devoluciones = QPushButton("Registrar Devolución")
        btn_devoluciones.setObjectName("btnRojo")
        btn_devoluciones.clicked.connect(self.abrir_miniventana_devolucion)
        nav_layout.addWidget(btn_devoluciones)

        btn_cerrar_dia = QPushButton("Cerrar Día")
        btn_cerrar_dia.setObjectName("btnGris")
        btn_cerrar_dia.clicked.connect(self.cerrar_dia)
        nav_layout.addWidget(btn_cerrar_dia)

        main_layout.addLayout(nav_layout)

        # Buscador de productos
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
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
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.tabla)

        # Panel de agregar al carrito
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)
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
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_al_carrito)
        add_layout.addWidget(btn_agregar)
        main_layout.addLayout(add_layout)

        # Tabla del carrito
        cart_label = QLabel("Carrito de Venta")
        cart_label.setObjectName("subtitulo")
        main_layout.addWidget(cart_label)
        
        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(4)
        self.tabla_carrito.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad", "Subtotal"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_carrito.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.tabla_carrito)

        # Panel de total y botones
        total_layout = QHBoxLayout()
        total_layout.setSpacing(10)
        self.label_total = QLabel("Total: $0.00")
        self.label_total.setObjectName("labelTotal")
        total_layout.addWidget(self.label_total)
        total_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar Venta")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.clicked.connect(self.cancelar_venta)
        total_layout.addWidget(btn_cancelar)
        
        btn_vender = QPushButton("Procesar Venta")
        btn_vender.setObjectName("btnProcesar")
        btn_vender.clicked.connect(self.vender_todo)
        total_layout.addWidget(btn_vender)
        main_layout.addLayout(total_layout)

        # Panel de pago y cambio
        pago_layout = QHBoxLayout()
        pago_layout.setSpacing(8)
        pago_label = QLabel("Pago del cliente (Bs.):")
        pago_layout.addWidget(pago_label)
        self.input_pago = QLineEdit()
        self.input_pago.setPlaceholderText("Ejemplo: 50")
        pago_layout.addWidget(self.input_pago)
        btn_calcular_cambio = QPushButton("Calcular Cambio")
        btn_calcular_cambio.clicked.connect(self.calcular_cambio)
        pago_layout.addWidget(btn_calcular_cambio)
        self.label_cambio = QLabel("Cambio: 0.00 Bs.")
        self.label_cambio.setObjectName("labelCambio")
        pago_layout.addWidget(self.label_cambio)
        main_layout.addLayout(pago_layout)

        # Panel de descuento
        descuento_layout = QHBoxLayout()
        descuento_layout.setSpacing(8)
        descuento_label = QLabel("Descuento (%):")
        descuento_layout.addWidget(descuento_label)
        self.input_descuento = QLineEdit()
        self.input_descuento.setPlaceholderText("Ejemplo: 10")
        descuento_layout.addWidget(self.input_descuento)
        btn_aplicar_descuento = QPushButton("Aplicar Descuento")
        btn_aplicar_descuento.clicked.connect(self.aplicar_descuento)
        descuento_layout.addWidget(btn_aplicar_descuento)
        self.label_descuento = QLabel("Descuento aplicado: 0.00 Bs.")
        self.label_descuento.setObjectName("labelDescuento")
        descuento_layout.addWidget(self.label_descuento)
        main_layout.addLayout(descuento_layout)

        self.descuento_porcentaje = 0.0

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

        if cantidad > unidades_disponibles:
            QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficientes unidades de '{nombre}'.")
            return
        
        cantidad_unidades = cantidad
        descripcion = f"{cantidad_unidades} unidad(es)"

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
        
        self.cursor.execute(sql, params)
        resultados = self.cursor.fetchall()
        
        if not resultados:
            QMessageBox.information(self, "Cliente no encontrado", 
                                  "No se encontró ningún cliente con ese criterio. Las ventas se realizarán sin descuento.")
            self.cliente_actual = None
            self.descuento_cliente = 0.0
            self.label_info_cliente.setText("Cliente: No registrado")
            self.label_puntos_cliente.setText("Puntos: 0")
            self.label_descuento_cliente.setText("Descuento: 0%")
            return
        
        if len(resultados) > 1:
            self.mostrar_seleccion_cliente(resultados)
            return
            
        ci, nombre, apellidos, puntos, descuento = resultados[0]
        self.seleccionar_cliente(ci, nombre, apellidos, puntos, descuento)
    
    def seleccionar_cliente(self, ci, nombre, apellidos, puntos, descuento):
        """Selecciona un cliente y muestra su información."""
        self.cliente_actual = {
            'ci': ci,
            'nombre': nombre,
            'apellidos': apellidos,
            'puntos': puntos,
            'descuento': descuento
        }
        self.descuento_cliente = descuento
        
        nivel, porcentaje = self.calcular_nivel_puntaje(puntos)
        
        self.label_info_cliente.setText(f"Cliente: {nombre} {apellidos}")
        self.label_puntos_cliente.setText(f"Puntos: {puntos} | Nivel: {nivel}")
        self.label_descuento_cliente.setText(f"Descuento: {porcentaje}%")
        self.input_descuento.setText(str(porcentaje))
    
    def mostrar_seleccion_cliente(self, resultados):
        """Muestra un diálogo para seleccionar un cliente cuando hay múltiples resultados."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel
        
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Seleccionar Cliente")
        dialogo.setMinimumSize(500, 350)
        dialogo.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("Se encontraron múltiples clientes. Seleccione uno:")
        label.setObjectName("tituloDialog")
        layout.addWidget(label)
        
        lista = QListWidget()
        lista.setObjectName("listaDialog")
        for ci, nombre, apellidos, puntos, descuento in resultados:
            item = QListWidgetItem(f"{nombre} {apellidos} - CI: {ci}")
            item.setData(Qt.UserRole, (ci, nombre, apellidos, puntos, descuento))
            lista.addItem(item)
        layout.addWidget(lista)
        
        btn_seleccionar = QPushButton("Seleccionar")
        btn_seleccionar.setObjectName("btnDialog")
        
        def confirmar():
            item = lista.currentItem()
            if item:
                ci, nombre, apellidos, puntos, descuento = item.data(Qt.UserRole)
                self.seleccionar_cliente(ci, nombre, apellidos, puntos, descuento)
                dialogo.accept()
        
        btn_seleccionar.clicked.connect(confirmar)
        layout.addWidget(btn_seleccionar)
        
        dialogo.setLayout(layout)
        dialogo.exec_()
    
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
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Historial de puntos y canjes")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        self.cursor.execute("SELECT fecha_venta, total_venta FROM ventas WHERE id_cliente = ? ORDER BY fecha_venta DESC", (ci,))
        ventas = self.cursor.fetchall()
        
        self.cursor.execute("SELECT premios_canjeados FROM clientes WHERE CI = ?", (ci,))
        row = self.cursor.fetchone()
        premios = row[0] if row else 0
        
        label_premios = QLabel(f"Premios canjeados: {premios}")
        label_premios.setObjectName("labelResumen")
        layout.addWidget(label_premios)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for fecha, total in ventas:
            label_venta = QLabel(f"Venta: {fecha} | Monto: {total} Bs.")
            scroll_layout.addWidget(label_venta)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def actualizar_puntos_cliente(self, total_compra):
        if not self.cliente_actual:
            return
        ci = self.cliente_actual['ci']
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
            self.cursor.execute("SELECT unidades FROM productos WHERE id_producto = ?", (item["id"],))
            result = self.cursor.fetchone()
            if not result:
                continue
                
            unidades_actual = result[0]
            unidades_vendidas = item["cantidad"]
            nuevas_unidades = unidades_actual - unidades_vendidas
            
            self.cursor.execute(
                "UPDATE productos SET unidades = ? WHERE id_producto = ?",
                (nuevas_unidades, item["id"])
            )

            self.cursor.execute(
                "INSERT INTO movimientos_inventario (codigo_producto, tipo_movimiento, cantidad, fecha_movimiento, observaciones, usuario) VALUES (?, ?, ?, ?, ?, ?)",
                (item["codigo"], "venta", item["cantidad"], fecha_mov, "Venta realizada desde sistema admin", "admin")
            )
        
        try:
            self.cursor.execute(
                "INSERT INTO ventas (fecha_venta, total_venta, id_empleado) VALUES (?, ?, ?)",
                (fecha_mov, total_con_descuento, self.id_empleado)
            )
            
            if self.cliente_actual:
                self.actualizar_puntos_cliente(total_con_descuento)
            
        except Exception as e:
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
        dialog.setMinimumSize(500, 450)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        form = QFormLayout()
        form.setSpacing(10)

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
        buscar_producto()

        spin_cantidad = QSpinBox()
        spin_cantidad.setMinimum(1)
        form.addRow("Cantidad:", spin_cantidad)
        
        input_motivo = QTextEdit()
        input_motivo.setPlaceholderText("Motivo de la devolución")
        input_motivo.setMaximumHeight(80)
        form.addRow("Motivo:", input_motivo)
        
        combo_empleado = QComboBox()
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        for id_emp, nombre in self.cursor.fetchall():
            combo_empleado.addItem(f"{nombre} [ID: {id_emp}]", id_emp)
        form.addRow("Empleado:", combo_empleado)
        
        btn_registrar = QPushButton("Registrar devolución")
        btn_registrar.setObjectName("btnProcesar")
        
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
        dialog.setMinimumSize(400, 200)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("Seleccione el empleado que realizará las ventas hoy:")
        label.setObjectName("tituloDialog")
        layout.addWidget(label)
        
        combo = QComboBox()
        combo.setStyleSheet("""
                QComboBox {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e0e7ff, stop:1 #c7d2fe);
                    border: 2px solid #4dabf5;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-size: 15px;
                    color: #22223b;
                }
                QComboBox::drop-down {
                    border: none;
                    background: #4dabf5;
                    width: 28px;
                    border-top-right-radius: 8px;
                    border-bottom-right-radius: 8px;
                }
                QComboBox QAbstractItemView {
                    background: #f8fafc;
                    border: 1px solid #4dabf5;
                    selection-background-color: #c7d2fe;
                    selection-color: #22223b;
                    font-size: 15px;
                    color: #22223b;
                    border-radius: 8px;
                }
            """)
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        empleados = self.cursor.fetchall()
        for id_emp, nombre in empleados:
            combo.addItem(f"{nombre} [ID: {id_emp}]", id_emp)
        layout.addWidget(combo)
        
        btn = QPushButton("Confirmar")
        btn.setObjectName("btnDialog")
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
        btn_cerrar_dia.setObjectName("btnGris")
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
        dialog.setMinimumSize(500, 400)
        
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
        dialog.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        if not self.cliente_actual:
            QMessageBox.information(self, "Sin cliente", "Primero seleccione un cliente.")
            return
        
        ci = self.cliente_actual['ci']
        self.cursor.execute("SELECT id_devolucion, id_producto, cantidad, motivo, fecha_devolucion FROM devoluciones WHERE CI_cliente = ? AND reintegrado IS NULL ORDER BY fecha_devolucion DESC", (ci,))
        devoluciones = self.cursor.fetchall()
        
        if not devoluciones:
            label_vacio = QLabel("No hay devoluciones pendientes de reintegrar para este cliente.")
            label_vacio.setObjectName("labelInfo")
            layout.addWidget(label_vacio)
        else:
            label_titulo = QLabel("Seleccione la devolución a reintegrar:")
            label_titulo.setObjectName("tituloDialog")
            layout.addWidget(label_titulo)
            
            combo = QComboBox()
            for id_dev, id_prod, cantidad, motivo, fecha in devoluciones:
                combo.addItem(f"ID: {id_dev} | Producto: {id_prod} | Cantidad: {cantidad} | Motivo: {motivo} | Fecha: {fecha}", id_dev)
            layout.addWidget(combo)
            
            btn = QPushButton("Reintegrar")
            btn.setObjectName("btnProcesar")
            layout.addWidget(btn)
            
            def confirmar():
                id_devolucion = combo.currentData()
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
        """Aplica tema moderno y profesional con gradientes suaves."""
        self.setStyleSheet("""
            /* Ventana Principal */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }
            
            /* Labels generales */
            QLabel {
                color: #eef2f7;
                font-size: 13px;
                font-weight: 500;
            }
            
            /* Título principal */
            QLabel#titulo {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(16, 172, 132, 0.2), stop:1 rgba(33, 150, 243, 0.2));
                border-radius: 12px;
                margin-bottom: 10px;
            }
            
            /* Subtítulos */
            QLabel#subtitulo {
                color: #10ac84;
                font-size: 18px;
                font-weight: 600;
                padding: 8px 0;
            }
            
            /* Labels de información del cliente */
            QLabel#infoCliente, QLabel#infoPuntos, QLabel#infoDescuento {
                color: #f8f9fa;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                border: 1px solid rgba(16, 172, 132, 0.3);
            }
            
            /* Label de total */
            QLabel#labelTotal {
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
                padding: 10px 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10ac84, stop:1 #1dd1a1);
                border-radius: 10px;
            }
            
            /* Label de cambio */
            QLabel#labelCambio {
                color: #2196F3;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 12px;
                background: rgba(33, 150, 243, 0.15);
                border-radius: 8px;
            }
            
            /* Label de descuento */
            QLabel#labelDescuento {
                color: #ee5a6f;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 12px;
                background: rgba(238, 90, 111, 0.15);
                border-radius: 8px;
            }
            
            /* Botones principales */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976D2, stop:1 #1565C0);
            }
            
            /* Botones de navegación */
            QPushButton#btnNavegacion {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 8px 15px;
                min-width: 80px;
            }
            
            QPushButton#btnNavegacion:hover {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
            
            /* Botón secundario */
            QPushButton#btnSecundario {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
            }
            
            QPushButton#btnSecundario:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #b07cc6, stop:1 #9b59b6);
            }
            
            /* Botón importante */
            QPushButton#btnImportante {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                font-weight: 700;
            }
            
            QPushButton#btnImportante:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5b041, stop:1 #f39c12);
            }
            
            /* Botón agregar */
            QPushButton#btnAgregar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10ac84, stop:1 #0e8f6e);
                font-size: 15px;
                padding: 12px 20px;
            }
            
            QPushButton#btnAgregar:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1dd1a1, stop:1 #10ac84);
            }
            
            /* Botón procesar */
            QPushButton#btnProcesar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10ac84, stop:1 #0e8f6e);
                font-size: 16px;
                font-weight: 700;
                padding: 12px 24px;
                min-width: 140px;
            }
            
            QPushButton#btnProcesar:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1dd1a1, stop:1 #10ac84);
            }
            
            /* Botón cancelar */
            QPushButton#btnCancelar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #636e72, stop:1 #2d3436);
            }
            
            QPushButton#btnCancelar:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #757f83, stop:1 #636e72);
            }
            
            /* Botones de colores específicos */
            QPushButton#btnVerde {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00b894, stop:1 #00a383);
            }
            
            QPushButton#btnVerde:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00d1a3, stop:1 #00b894);
            }
            
            QPushButton#btnNaranja {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e17055, stop:1 #d35400);
            }
            
            QPushButton#btnNaranja:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fab1a0, stop:1 #e17055);
            }
            
            QPushButton#btnAzul {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0984e3, stop:1 #0652DD);
            }
            
            QPushButton#btnAzul:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
            }
            
            QPushButton#btnRojo {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ee5a6f, stop:1 #d63031);
            }
            
            QPushButton#btnRojo:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff7675, stop:1 #ee5a6f);
            }
            
            QPushButton#btnGris {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #636e72, stop:1 #2d3436);
            }
            
            QPushButton#btnGris:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #b2bec3, stop:1 #636e72);
            }
            
            /* Campos de entrada */
            QLineEdit, QSpinBox, QComboBox {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f8f9fa;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                selection-background-color: #2196F3;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #2196F3;
                background-color: rgba(255, 255, 255, 0.12);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f8f9fa;
                margin-right: 8px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d3436;
                color: #f8f9fa;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                selection-background-color: #2196F3;
                padding: 4px;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                width: 20px;
                border-radius: 4px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* Tablas */
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                color: #f8f9fa;
                gridline-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                font-size: 13px;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            QTableWidget::item:selected {
                background-color: rgba(33, 150, 243, 0.3);
                color: #ffffff;
            }
            
            QTableWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(33, 150, 243, 0.3), stop:1 rgba(33, 150, 243, 0.2));
                color: #ffffff;
                padding: 10px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 2px solid rgba(33, 150, 243, 0.5);
                font-weight: 600;
                font-size: 13px;
            }
            
            QHeaderView::section:first {
                border-top-left-radius: 10px;
            }
            
            QHeaderView::section:last {
                border-top-right-radius: 10px;
                border-right: none;
            }
            
            /* Barra de progreso */
            QProgressBar {
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                text-align: center;
                font-weight: 600;
                height: 25px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10ac84, stop:1 #1dd1a1);
                border-radius: 7px;
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* TextEdit */
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f8f9fa;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                selection-background-color: #2196F3;
            }
            
            QTextEdit:focus {
                border: 2px solid #2196F3;
                background-color: rgba(255, 255, 255, 0.12);
            }
            
            /* Estilos para diálogos */
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
            }
            
            QLabel#tituloDialog {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
                padding: 10px 0;
            }
            
            QLabel#labelResumen {
                color: #10ac84;
                font-size: 15px;
                font-weight: 600;
                padding: 8px 12px;
                background: rgba(16, 172, 132, 0.15);
                border-radius: 8px;
                border: 1px solid rgba(16, 172, 132, 0.3);
            }
            
            QLabel#labelInfo {
                color: #f8f9fa;
                font-size: 14px;
                padding: 12px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            
            QListWidget#listaDialog {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f8f9fa;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            
            QListWidget#listaDialog::item {
                padding: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                margin: 2px 0;
            }
            
            QListWidget#listaDialog::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(33, 150, 243, 0.4), stop:1 rgba(33, 150, 243, 0.3));
                color: #ffffff;
                font-weight: 600;
            }
            
            QListWidget#listaDialog::item:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            
            QPushButton#btnDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                min-height: 40px;
                font-size: 15px;
                font-weight: 700;
            }
            
            QPushButton#btnDialog:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
            
            /* Placeholders */
            QLineEdit[placeholderText]:!focus {
                color: rgba(248, 249, 250, 0.5);
            }
            
            /* MessageBox personalizado */
            QMessageBox {
                background-color: #16213e;
            }
            
            QMessageBox QLabel {
                color: #f8f9fa;
                font-size: 13px;
            }
            
            QMessageBox QPushButton {
                min-width: 80px;
                padding: 8px 16px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VentasWindow()
    window.showMaximized()
    sys.exit(app.exec_())