import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QBrush, QLinearGradient, QColor, QFont
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
        self.setGeometry(100, 100, 450, 420)

        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()

        # Crear tabla si no existe
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

        # Fondo gradiente moderno
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, 600)
        gradient.setColorAt(0.0, QColor("#8E2DE2"))  # púrpura
        gradient.setColorAt(1.0, QColor("#4A00E0"))  # azul profundo
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        # Configurar interfaz
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz gráfica."""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # --- Tarjeta flotante estilo “glassmorphism” ---
        card = QWidget()
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)
        card.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 20px;
                padding: 20px;
                color: white;
                font-family: 'Segoe UI';
                backdrop-filter: blur(8px);
            }
        """)

        # Título
        title_label = QLabel("Registrar Nuevo Cliente")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        card_layout.addWidget(title_label)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.input_ci = QLineEdit()
        self.input_ci.setPlaceholderText("Ingrese el CI del cliente")

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ingrese el nombre del cliente")

        self.input_apellidos = QLineEdit()
        self.input_apellidos.setPlaceholderText("Ingrese los apellidos del cliente")

        self.input_celular = QLineEdit()
        self.input_celular.setPlaceholderText("Ingrese el número de celular (opcional)")

        self.input_descuento = QLineEdit()
        self.input_descuento.setPlaceholderText("Ingrese el descuento inicial (0-100%)")
        self.input_descuento.setText("0.0")

        for campo in [self.input_ci, self.input_nombre, self.input_apellidos, self.input_celular, self.input_descuento]:
            campo.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255,255,255,0.3);
                    border: 1px solid rgba(255,255,255,0.5);
                    border-radius: 10px;
                    padding: 8px;
                    color: white;
                }
                QLineEdit::placeholder {
                    color: rgba(255,255,255,0.7);
                }
                QLineEdit:focus {
                    border: 1px solid #00BFFF;
                    background-color: rgba(255,255,255,0.4);
                }
            """)

        form_layout.addRow("CI:", self.input_ci)
        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Apellidos:", self.input_apellidos)
        form_layout.addRow("Celular:", self.input_celular)
        form_layout.addRow("Descuento (%):", self.input_descuento)
        card_layout.addLayout(form_layout)

        # Botones
        button_layout = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_registrar = QPushButton("Registrar Cliente")

        estilo_boton = """
            QPushButton {
                background-color: #6EC1E4;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #8FD4F5;
            }
            QPushButton:pressed {
                background-color: #5AAED1;
            }
        """
        btn_cancelar.setStyleSheet(estilo_boton)
        btn_registrar.setStyleSheet(estilo_boton)

        btn_cancelar.clicked.connect(self.close)
        btn_registrar.clicked.connect(self.registrar_cliente)

        button_layout.addWidget(btn_cancelar)
        button_layout.addWidget(btn_registrar)

        card_layout.addLayout(button_layout)
        main_layout.addStretch()
        main_layout.addWidget(card)
        main_layout.addStretch()

    def registrar_cliente(self):
        """Valida y guarda un nuevo cliente."""
        ci = self.input_ci.text().strip()
        nombre = self.input_nombre.text().strip()
        apellidos = self.input_apellidos.text().strip()
        celular = self.input_celular.text().strip()

        try:
            descuento = float(self.input_descuento.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "El descuento debe ser un número válido.")
            return

        if not ci or not nombre or not apellidos:
            QMessageBox.warning(self, "Error", "Por favor, complete todos los campos obligatorios.")
            return

        if descuento < 0 or descuento > 100:
            QMessageBox.warning(self, "Error", "El descuento debe estar entre 0 y 100%.")
            return

        self.cursor.execute("SELECT CI FROM clientes WHERE CI = ?", (ci,))
        if self.cursor.fetchone():
            QMessageBox.warning(self, "Error", "Ya existe un cliente con este CI.")
            return

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
        self.conexion.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegistrarClienteWindow()
    window.show()
    sys.exit(app.exec_())
