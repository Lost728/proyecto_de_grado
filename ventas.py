import sys
import sqlite3
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QSpinBox, QHeaderView
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
        # btn_productos = QPushButton("Ver Productos")
        # btn_productos.clicked.connect(lambda: self.abrir_script("ver_productos.py"))
        # nav_layout.addWidget(btn_productos)
        # btn_nuevo_producto = QPushButton("Nuevo Producto")
        # btn_nuevo_producto.clicked.connect(lambda: self.abrir_script("insertar_producto.py"))
        # nav_layout.addWidget(btn_nuevo_producto)
        # btn_empleados = QPushButton("Empleados")
        # btn_empleados.clicked.connect(lambda: self.abrir_script(os.path.join("empleados", "ver_empleado.py")))
        # nav_layout.addWidget(btn_empleados)
        # btn_nuevo_empleado = QPushButton("Nuevo Empleado")
        # btn_nuevo_empleado.clicked.connect(lambda: self.abrir_script(os.path.join("empleados", "insertar_empleado.py")))
        # nav_layout.addWidget(btn_nuevo_empleado)
        # btn_ventas = QPushButton("Ventas")
        # btn_ventas.clicked.connect(lambda: self.abrir_script("venta_registro.py"))
        # nav_layout.addWidget(btn_ventas)
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
            "ID", "Nombre", "Código", "Precio", "Stock"
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

        self.tabla.selectionModel().selectionChanged.connect(self.actualizar_spinbox)
        self.cargar_todos_productos()

    def cargar_todos_productos(self):
        """Carga todos los productos con stock disponible en la tabla principal."""
        self.cursor.execute("SELECT id_producto, nombre, codigo, precio, stock FROM productos WHERE stock > 0")
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
        """Muestra los productos en la tabla principal."""
        self.tabla.setRowCount(0)
        for row_num, row_data in enumerate(resultados):
            self.tabla.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                self.tabla.setItem(row_num, col_num, item)
        self.tabla.resizeColumnsToContents()
        self.spin_cantidad.setMaximum(1)

    def actualizar_spinbox(self):
        """Actualiza el máximo del spinbox de cantidad según el stock del producto seleccionado."""
        selected = self.tabla.currentRow()
        if selected == -1:
            self.spin_cantidad.setMaximum(1)
            return
        try:
            stock = int(self.tabla.item(selected, 4).text())
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
            producto_id = int(self.tabla.item(selected, 0).text())
            nombre = self.tabla.item(selected, 1).text()
            codigo = self.tabla.item(selected, 2).text()
            precio = float(self.tabla.item(selected, 3).text())
            stock = int(self.tabla.item(selected, 4).text())
        except Exception:
            QMessageBox.warning(self, "Error", "Error al leer los datos del producto seleccionado.")
            return
        cantidad = self.spin_cantidad.value()
        if cantidad > stock:
            QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficiente stock de '{nombre}'.")
            return
        for item in self.carrito:
            if item["id"] == producto_id:
                if item["cantidad"] + cantidad > stock:
                    QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficiente stock de '{nombre}'.")
                    return
                item["cantidad"] += cantidad
                self.actualizar_tabla_carrito()
                self.spin_cantidad.setValue(1)
                return
        self.carrito.append({
            "id": producto_id,
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "stock": stock,
            "codigo": codigo
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
            self.tabla_carrito.setItem(row_num, 2, QTableWidgetItem(str(item["cantidad"])))
            subtotal = item["cantidad"] * item["precio"]
            subtotal_item = QTableWidgetItem(f"{subtotal:.2f} Bs.")
            self.tabla_carrito.setItem(row_num, 3, subtotal_item)
        total = sum(item["cantidad"] * item["precio"] for item in self.carrito)
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
            self.cursor.execute(
                "UPDATE productos SET stock = stock - ? WHERE id_producto = ? AND stock >= ?",
                (item["cantidad"], item["id"], item["cantidad"])
            )
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

    def abrir_script(self, script):
        try:
            if self.conexion:
                self.conexion.close()
        except Exception:
            pass
        subprocess.Popen([sys.executable, script])
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentasWindow()
    ventana.showMaximized()
    sys.exit(app.exec_())