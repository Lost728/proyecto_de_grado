import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt

class HistorialProducto(QWidget):
    def __init__(self, codigo_producto):
        super().__init__()
        self.setWindowTitle(f"Historial de Movimientos - {codigo_producto}")
        self.resize(900, 500)
        self.db_path = "pruebas.db"
        self.codigo_producto = codigo_producto

        layout = QVBoxLayout(self)

        # Título y botón volver
        top_layout = QHBoxLayout()
        lbl_titulo = QLabel(f"Historial de Movimientos - {codigo_producto}")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_layout.addWidget(lbl_titulo)
        top_layout.addStretch()
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(self.volver_a_reporte_prod)
        top_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.clicked.connect(self.ir_menu_principal)
        top_layout.addWidget(btn_menu)

        layout.addLayout(top_layout)

        # Tabla de historial (coincide con la estructura de movimientos_inventario)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID Movimiento", "Código Producto", "Tipo Movimiento", "Cantidad", "Fecha Movimiento", "Observaciones", "Usuario"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)

        self.cargar_historial()

    def volver_a_reporte_prod(self):
        self.close()

    def ir_menu_principal(self):
        """Ir a menu.py"""
        try:
            import subprocess
            script_path = os.path.join(os.path.dirname(__file__), "menu.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir menu.py: {e}")

    def cargar_historial(self):
        self.tabla.setRowCount(0)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_movimiento, codigo_producto, tipo_movimiento, cantidad, fecha_movimiento, observaciones, usuario
                FROM movimientos_inventario
                WHERE codigo_producto = ?
                ORDER BY fecha_movimiento DESC
            """, (self.codigo_producto,))
            movimientos = cursor.fetchall()
            conn.close()
            for row_num, (id_mov, cod_prod, tipo, cantidad, fecha, obs, usuario) in enumerate(movimientos):
                self.tabla.insertRow(row_num)
                self.tabla.setItem(row_num, 0, QTableWidgetItem(str(id_mov)))
                self.tabla.setItem(row_num, 1, QTableWidgetItem(str(cod_prod)))
                self.tabla.setItem(row_num, 2, QTableWidgetItem(str(tipo)))
                self.tabla.setItem(row_num, 3, QTableWidgetItem(str(cantidad)))
                self.tabla.setItem(row_num, 4, QTableWidgetItem(str(fecha)))
                self.tabla.setItem(row_num, 5, QTableWidgetItem(str(obs) if obs else ""))
                self.tabla.setItem(row_num, 6, QTableWidgetItem(str(usuario)))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el historial: {e}")

if __name__ == "__main__":
    import sys
    codigo = sys.argv[1] if len(sys.argv) > 1 else "P001"
    app = QApplication(sys.argv)
    ventana = HistorialProducto(codigo)
    ventana.showMaximized()
    sys.exit(app.exec_())