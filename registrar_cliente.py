import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout
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

class RegistrarClienteWindow(QMainWindow):
    def __init__(self):
        """Inicializa la ventana para registrar un nuevo cliente."""
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Cliente")
        self.setGeometry(100, 100, 400, 300)
        
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        
        # Verificar si existe la tabla clientes, si no, crearla
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
        
        # Configurar la interfaz
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz gráfica de usuario."""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Título
        title_label = QLabel("Registrar Nuevo Cliente")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Campo CI
        self.input_ci = QLineEdit()
        self.input_ci.setPlaceholderText("Ingrese el CI del cliente")
        form_layout.addRow("CI:", self.input_ci)
        
        # Campo Nombre
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ingrese el nombre del cliente")
        form_layout.addRow("Nombre:", self.input_nombre)
        
        # Campo Apellidos
        self.input_apellidos = QLineEdit()
        self.input_apellidos.setPlaceholderText("Ingrese los apellidos del cliente")
        form_layout.addRow("Apellidos:", self.input_apellidos)
        
        # Campo Celular
        self.input_celular = QLineEdit()
        self.input_celular.setPlaceholderText("Ingrese el número de celular (opcional)")
        form_layout.addRow("Celular:", self.input_celular)
        
        # Campo Descuento
        self.input_descuento = QLineEdit()
        self.input_descuento.setPlaceholderText("Ingrese el descuento inicial (0-100%)")
        self.input_descuento.setText("0.0")
        form_layout.addRow("Descuento (%):", self.input_descuento)
        
        main_layout.addLayout(form_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.close)
        button_layout.addWidget(btn_cancelar)
        
        btn_registrar = QPushButton("Registrar Cliente")
        btn_registrar.clicked.connect(self.registrar_cliente)
        button_layout.addWidget(btn_registrar)
        
        main_layout.addLayout(button_layout)
    
    def registrar_cliente(self):
        """Valida y guarda un nuevo cliente en la base de datos."""
        # Obtener los datos del formulario
        ci = self.input_ci.text().strip()
        nombre = self.input_nombre.text().strip()
        apellidos = self.input_apellidos.text().strip()
        celular = self.input_celular.text().strip()
        
        try:
            descuento = float(self.input_descuento.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "El descuento debe ser un número válido.")
            return
        
        # Validar datos obligatorios
        if not ci:
            QMessageBox.warning(self, "Error", "El CI es obligatorio.")
            return
        
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return
        
        if not apellidos:
            QMessageBox.warning(self, "Error", "Los apellidos son obligatorios.")
            return
        
        # Validar descuento
        if descuento < 0 or descuento > 100:
            QMessageBox.warning(self, "Error", "El descuento debe estar entre 0 y 100%.")
            return
        
        # Verificar si el cliente ya existe
        self.cursor.execute("SELECT CI FROM clientes WHERE CI = ?", (ci,))
        if self.cursor.fetchone():
            QMessageBox.warning(self, "Error", "Ya existe un cliente con este CI.")
            return
        
        # Registrar el nuevo cliente
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            "INSERT INTO clientes (CI, nombre, apellidos, celular, puntos_acumulados, descuento, fecha_registro) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ci, nombre, apellidos, celular, 0, descuento, fecha_registro)
        )
        self.conexion.commit()
        
        QMessageBox.information(
            self, 
            "Cliente Registrado", 
            f"El cliente {nombre} {apellidos} ha sido registrado exitosamente."
        )
        
        self.close()
    
    def closeEvent(self, event):
        """Cerrar la conexión a la base de datos al cerrar la ventana."""
        self.conexion.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegistrarClienteWindow()
    window.show()
    sys.exit(app.exec_())