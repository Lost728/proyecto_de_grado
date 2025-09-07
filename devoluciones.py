import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QSpinBox, QTextEdit, QHeaderView
)
from PyQt5.QtCore import Qt

DB_PATH = "pruebas.db"  # Cambia si tu base de datos tiene otro nombre

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
        form_layout = QHBoxLayout()
        self.producto_combo = QComboBox()
        self._load_productos()
        form_layout.addWidget(QLabel("Producto:"))
        form_layout.addWidget(self.producto_combo)

        self.cantidad_spin = QSpinBox()
        self.cantidad_spin.setMinimum(1)
        self.cantidad_spin.setMaximum(1000)
        form_layout.addWidget(QLabel("Cantidad:"))
        form_layout.addWidget(self.cantidad_spin)

        self.motivo_text = QTextEdit()
        self.motivo_text.setPlaceholderText("Motivo de la devolución")
        self.motivo_text.setFixedHeight(40)
        form_layout.addWidget(QLabel("Motivo:"))
        form_layout.addWidget(self.motivo_text)

        self.empleado_combo = QComboBox()
        self._load_empleados()
        form_layout.addWidget(QLabel("Empleado:"))
        form_layout.addWidget(self.empleado_combo)

        btn_devolver = QPushButton("Registrar Devolución")
        btn_devolver.clicked.connect(self.registrar_devolucion)
        form_layout.addWidget(btn_devolver)

        main_layout.addLayout(form_layout)

        # Tabla de devoluciones
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Producto", "Cantidad", "Motivo", "Fecha", "Empleado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.tabla)

        self.setCentralWidget(central)

    def _load_productos(self):
        self.producto_combo.clear()
        self.cursor.execute("SELECT id_producto, nombre FROM productos")
        for id_producto, nombre in self.cursor.fetchall():
            self.producto_combo.addItem(f"{nombre} (ID:{id_producto})", id_producto)

    def _load_empleados(self):
        self.empleado_combo.clear()
        self.cursor.execute("SELECT id_empleado, nombre FROM empleado")
        for id_empleado, nombre in self.cursor.fetchall():
            self.empleado_combo.addItem(f"{nombre} (ID:{id_empleado})", id_empleado)

    def registrar_devolucion(self):
        id_producto = self.producto_combo.currentData()
        cantidad = self.cantidad_spin.value()
        motivo = self.motivo_text.toPlainText().strip()
        id_empleado = self.empleado_combo.currentData()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not motivo:
            QMessageBox.warning(self, "Motivo requerido", "Debe ingresar el motivo de la devolución.")
            return

        try:
            self.cursor.execute(
                "INSERT INTO devoluciones (id_producto, cantidad, motivo, fecha_devolucion, id_empleado) VALUES (?, ?, ?, ?, ?)",
                (id_producto, cantidad, motivo, fecha, id_empleado)
            )
            self.conn.commit()
            QMessageBox.information(self, "Devolución registrada", "La devolución se registró correctamente.")
            self._load_devoluciones()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la devolución:\n{e}")

    def _load_devoluciones(self):
        self.tabla.setRowCount(0)
        self.cursor.execute("""
            SELECT d.id_devolucion, p.nombre, d.cantidad, d.motivo, d.fecha_devolucion, e.nombre
            FROM devoluciones d
            JOIN productos p ON d.id_producto = p.id_producto
            JOIN empleado e ON d.id_empleado = e.id_empleado
            ORDER BY d.fecha_devolucion DESC
        """)
        for row_num, row_data in enumerate(self.cursor.fetchall()):
            self.tabla.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                self.tabla.setItem(row_num, col_num, QTableWidgetItem(str(data)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = DevolucionesWindow()
    ventana.showMaximized()
    sys.exit(app.exec_())