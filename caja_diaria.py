import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout, QComboBox, QGraphicsBlurEffect
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
        # Fondo difuminado desde la base de datos
        from PyQt5.QtGui import QPixmap
        def obtener_pixmap_fondo():
            try:
                conn = sqlite3.connect(obtener_db_path())
                cursor = conn.cursor()
                cursor.execute("SELECT datos FROM imagenes WHERE nombre LIKE '%mar%' LIMIT 1")
                row = cursor.fetchone()
                conn.close()
                if row:
                    datos = row[0]
                    pixmap = QPixmap()
                    pixmap.loadFromData(datos)
                    return pixmap
            except Exception:
                pass
            return QPixmap()

        pixmap = obtener_pixmap_fondo()
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        if not pixmap.isNull():
            self.bg_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(12)
            self.bg_label.setGraphicsEffect(blur)
        else:
            self.bg_label.setStyleSheet("background: #3a0f5a;")
        self.bg_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.bg_label.lower()

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Contenedor centrado (horiz. y vert.)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_widget.setLayout(content_layout)

        self.label_estado = QLabel("Registro de caja para el día: " + self.fecha)
        self.label_estado.setAlignment(Qt.AlignCenter)
        self.label_estado.setStyleSheet("color:#ffffff; font-weight:bold; font-size:16px;")
        content_layout.addWidget(self.label_estado, alignment=Qt.AlignCenter)

        self.form_layout = QFormLayout()
        # Combo de empleados
        self.combo_empleado = QComboBox()
        empleados = self.obtener_empleados()
        for id_emp, nombre, rol in empleados:
            self.combo_empleado.addItem(f"{nombre} ({rol}) [ID: {id_emp}]", id_emp)
        self.combo_empleado.setStyleSheet("background: rgba(0,0,0,0.35); color:#fff; border-radius:8px; padding:6px;")
        label_empleado = QLabel("Empleado:")
        label_empleado.setStyleSheet("color:#ffffff;")
        self.form_layout.addRow(label_empleado, self.combo_empleado)
        # Campo monto inicial
        self.input_monto_inicial = QLineEdit()
        self.input_monto_inicial.setPlaceholderText("Monto inicial de la caja")
        self.input_monto_inicial.setStyleSheet("background: rgba(0,0,0,0.35); color:#fff; border-radius:8px; padding:6px;")
        label_monto = QLabel("Monto inicial:")
        label_monto.setStyleSheet("color:#ffffff;")
        self.form_layout.addRow(label_monto, self.input_monto_inicial)
        # Añadir form_layout al content_layout (centrado)
        form_container = QWidget()
        form_container.setLayout(self.form_layout)
        content_layout.addWidget(form_container, alignment=Qt.AlignCenter)

        btn_style = "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6); color:#22223b; border-radius:10px; padding:8px;"
        self.btn_registrar_inicial = QPushButton("Registrar inicio de caja")
        self.btn_registrar_inicial.setStyleSheet(btn_style)
        self.btn_registrar_inicial.clicked.connect(self.registrar_inicio_caja)
        content_layout.addWidget(self.btn_registrar_inicial, alignment=Qt.AlignCenter)

        self.btn_omitir = QPushButton("Omitir registro de caja")
        self.btn_omitir.setStyleSheet(btn_style)
        self.btn_omitir.clicked.connect(self.omitir_registro)
        content_layout.addWidget(self.btn_omitir, alignment=Qt.AlignCenter)

        self.btn_ir_menu = QPushButton("Ir a menú principal")
        self.btn_ir_menu.setStyleSheet(btn_style)
        self.btn_ir_menu.clicked.connect(self.abrir_menu)
        content_layout.addWidget(self.btn_ir_menu, alignment=Qt.AlignCenter)

        # Centrar verticalmente: agregar stretch arriba y abajo
        main_layout.addStretch(1)
        main_layout.addWidget(content_widget, alignment=Qt.AlignCenter)
        main_layout.addStretch(1)

    def resizeEvent(self, event):
        # Ajustar el pixmap de fondo cuando la ventana cambie de tamaño
        if hasattr(self, 'bg_label'):
            pixmap = self.bg_label.pixmap()
            if pixmap:
                self.bg_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        return super().resizeEvent(event)

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
            ruta_menu = os.path.abspath(os.path.join(os.path.dirname(__file__), "menu.py"))
            subprocess.Popen([sys.executable, ruta_menu, str(id_empleado)])
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el inicio de la caja: {str(e)}")

    def omitir_registro(self):
        self.abrir_menu()

    def abrir_menu(self):
        id_empleado = self.combo_empleado.currentData()
        import subprocess
        import sys
        import os
        ruta_menu = os.path.abspath(os.path.join(os.path.dirname(__file__), "menu.py"))
        subprocess.Popen([sys.executable, ruta_menu, str(id_empleado)])
        self.close()

    def closeEvent(self, event):
        self.conexion.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CajaDiariaWindow()
    window.showMaximized()
    sys.exit(app.exec_())
