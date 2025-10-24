import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt
from datetime import datetime

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

class CajaDiariaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Caja Diaria")
        self.setGeometry(100, 100, 400, 220)
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        self.fecha = datetime.now().strftime("%Y-%m-%d")
        self.id_caja = None
        self.setup_ui()
        self.crear_tabla_si_no_existe()
        self.verificar_registro_inicial()

    def obtener_empleados(self):
        self.cursor.execute("SELECT id_empleado, nombre, rol FROM empleado")
        return self.cursor.fetchall()

    def crear_tabla_si_no_existe(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS caja_diaria (
                id_caja INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                id_empleado INTEGER NOT NULL,
                monto_inicial REAL NOT NULL,
                monto_final REAL,
                total_ventas REAL DEFAULT 0,
                observaciones TEXT
            )
        """)
        self.conexion.commit()

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.label_estado = QLabel("Registro de caja para el día: " + self.fecha)
        self.label_estado.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label_estado)

        self.form_layout = QFormLayout()
        # Combo de empleados
        self.combo_empleado = QComboBox()
        empleados = self.obtener_empleados()
        for id_emp, nombre, rol in empleados:
            self.combo_empleado.addItem(f"{nombre} ({rol}) [ID: {id_emp}]", id_emp)
        self.form_layout.addRow("Empleado:", self.combo_empleado)
        # Campo monto inicial
        self.input_monto_inicial = QLineEdit()
        self.input_monto_inicial.setPlaceholderText("Monto inicial de la caja")
        self.form_layout.addRow("Monto inicial:", self.input_monto_inicial)
        main_layout.addLayout(self.form_layout)

        self.btn_registrar_inicial = QPushButton("Registrar inicio de caja")
        self.btn_registrar_inicial.clicked.connect(self.registrar_inicio_caja)
        main_layout.addWidget(self.btn_registrar_inicial)

        self.btn_abrir_ventas = QPushButton("Ir a ventas")
        self.btn_abrir_ventas.clicked.connect(self.abrir_ventas)
        main_layout.addWidget(self.btn_abrir_ventas)

    def abrir_ventas(self):
        id_empleado = self.combo_empleado.currentData()
        import subprocess
        import sys
        import os
        ruta_ventas = os.path.abspath(os.path.join(os.path.dirname(__file__), "ventas_empleados.py"))
        subprocess.Popen([sys.executable, ruta_ventas, str(id_empleado)])
        self.close()

    def verificar_registro_inicial(self):
        id_empleado = self.combo_empleado.currentData()
        self.cursor.execute("SELECT id_caja, monto_inicial FROM caja_diaria WHERE fecha = ? AND id_empleado = ?", (self.fecha, id_empleado))
        resultado = self.cursor.fetchone()
        if resultado:
            self.id_caja = resultado[0]
            self.input_monto_inicial.setText(str(resultado[1]))
            self.input_monto_inicial.setEnabled(False)
            self.btn_registrar_inicial.setEnabled(False)
            self.label_estado.setText(f"Caja iniciada el {self.fecha}.")
        else:
            self.btn_registrar_inicial.setEnabled(True)

    def registrar_inicio_caja(self):
        id_empleado = self.combo_empleado.currentData()
        try:
            monto_inicial = float(self.input_monto_inicial.text())
            if monto_inicial <= 0:
                QMessageBox.warning(self, "Error", "El monto inicial debe ser mayor a cero.")
                return
            self.cursor.execute(
                "INSERT INTO caja_diaria (fecha, id_empleado, monto_inicial) VALUES (?, ?, ?)",
                (self.fecha, id_empleado, monto_inicial)
            )
            self.conexion.commit()
            self.verificar_registro_inicial()
            QMessageBox.information(self, "Registro exitoso", "Se ha registrado el inicio de la caja.")
            import subprocess
            import sys
            import os
            ruta_ventas = os.path.abspath(os.path.join(os.path.dirname(__file__), "ventas_empleados.py"))
            subprocess.Popen([sys.executable, ruta_ventas, str(id_empleado)])
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el inicio de la caja: {str(e)}")

    def closeEvent(self, event):
        self.conexion.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CajaDiariaWindow()
    window.show()
    sys.exit(app.exec_())
