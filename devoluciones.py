import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QSpinBox, QTextEdit, QHeaderView, QFormLayout
)
from PyQt5.QtCore import Qt

DB_PATH = "pruebas.db"

class DevolucionesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Devoluciones")
        self.setMinimumSize(800, 500)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self._setup_ui()
        self._load_devoluciones()

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Formulario de devolución
        self.form_layout = QFormLayout()
        # Selección de producto
        self.combo_producto = QComboBox()
        productos = self.obtener_productos()
        for id_prod, nombre in productos:
            self.combo_producto.addItem(f"{nombre} [ID: {id_prod}]", id_prod)
        self.form_layout.addRow("Producto:", self.combo_producto)
        # Cantidad
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(1000)
        self.form_layout.addRow("Cantidad:", self.spin_cantidad)
        # Motivo
        self.input_motivo = QTextEdit()
        self.input_motivo.setPlaceholderText("Motivo de la devolución")
        self.form_layout.addRow("Motivo:", self.input_motivo)
        # Empleado
        self.combo_empleado = QComboBox()
        empleados = self.obtener_empleados()
        for id_emp, nombre in empleados:
            self.combo_empleado.addItem(f"{nombre} [ID: {id_emp}]", id_emp)
        self.form_layout.addRow("Empleado:", self.combo_empleado)
        # Botón registrar
        self.btn_registrar = QPushButton("Registrar devolución")
        self.btn_registrar.clicked.connect(self.registrar_devolucion)
        self.form_layout.addRow(self.btn_registrar)
        self.setLayout(self.form_layout)

        # Tabla de devoluciones
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Producto", "Cantidad", "Motivo", "Fecha", "Empleado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.tabla)

        # Botón para volver al menú principal
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; padding: 8px 15px; border-radius: 5px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        main_layout.addWidget(btn_menu, alignment=Qt.AlignLeft)

        self.setCentralWidget(central)

    def obtener_productos(self):
        self.cursor.execute("SELECT id_producto, nombre FROM productos")
        return self.cursor.fetchall()

    def obtener_empleados(self):
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        return self.cursor.fetchall()

    def registrar_devolucion(self):
        id_producto = self.combo_producto.currentData()
        cantidad = self.spin_cantidad.value()
        motivo = self.input_motivo.toPlainText().strip()
        fecha_devolucion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_empleado = self.combo_empleado.currentData()
        if not motivo:
            QMessageBox.warning(self, "Error", "Debe ingresar el motivo de la devolución.")
            return
        try:
            self.cursor.execute(
                "INSERT INTO devoluciones (id_producto, cantidad, motivo, fecha_devolucion, id_empleado) VALUES (?, ?, ?, ?, ?)",
                (id_producto, cantidad, motivo, fecha_devolucion, id_empleado)
            )
            self.conn.commit()
            QMessageBox.information(self, "Registro exitoso", "La devolución ha sido registrada correctamente.")
            self._load_devoluciones()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la devolución: {str(e)}")

    def _load_devoluciones(self):
        self.tabla.setRowCount(0)
        self.cursor.execute("""
            SELECT d.id_devolucion, p.nombre, d.cantidad, d.motivo, d.fecha_devolucion, e.nombre
            FROM devoluciones d
            JOIN productos p ON d.id_producto = p.id_producto
            JOIN empleado e ON d.id_empleado = e.id_empleado
            ORDER BY d.fecha_devolucion DESC
        """)
        devoluciones = self.cursor.fetchall()
        for row_num, row_data in enumerate(devoluciones):
            self.tabla.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(data)))
            # Botón reintegrar
            btn_reintegrar = QPushButton("Reintegrar")
            btn_reintegrar.setStyleSheet("background-color: #0984e3; color: white; font-size: 13px;")
            btn_reintegrar.clicked.connect(lambda _, id_dev=row_data[0], cant=row_data[2], prod=row_data[1]: self.reintegrar_devolucion(id_dev, cant, prod))
            self.tabla.setCellWidget(row_num, self.tabla.columnCount()-1, btn_reintegrar)

    def reintegrar_devolucion(self, id_devolucion, cantidad, nombre_producto):
        """Reintegra la devolución seleccionada al inventario."""
        # Buscar el id_producto
        self.cursor.execute("SELECT id_producto FROM devoluciones WHERE id_devolucion = ?", (id_devolucion,))
        row = self.cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "Error", "No se encontró el producto para reintegrar.")
            return
        id_producto = row[0]
        # Actualizar inventario y marcar devolución como reintegrada
        self.cursor.execute("UPDATE productos SET unidades = unidades + ? WHERE id_producto = ?", (cantidad, id_producto))
        self.cursor.execute("UPDATE devoluciones SET reintegrado = 1 WHERE id_devolucion = ?", (id_devolucion,))
        self.conn.commit()
        QMessageBox.information(self, "Reintegrado", f"La devolución de '{nombre_producto}' ha sido reintegrada al inventario.")
        self._load_devoluciones()

    def ir_menu_principal(self):
        import os, subprocess
        script_path = os.path.join(os.path.dirname(__file__), "menu.py")
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
            return
        self.close()
        subprocess.Popen([sys.executable, script_path])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = DevolucionesWindow()
    ventana.showMaximized()
    sys.exit(app.exec_())