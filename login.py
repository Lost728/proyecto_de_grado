import sys
import sqlite3
import bcrypt
import subprocess
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QColor

class LoginApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio de Sesión")
        self.setup_ui()

    def setup_ui(self):
        # Fondo con imagen
        self.setAutoFillBackground(True)
        palette = QPalette()
        pixmap = QPixmap("mar.jpg")
        palette.setBrush(QPalette.Window, QBrush(pixmap))
        self.setPalette(palette)

        # Layout principal centrado
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Caja central translúcida
        login_box = QWidget(self)
        login_box.setFixedWidth(350)
        login_box.setStyleSheet("""
            QWidget {
                background: rgba(40, 20, 80, 0.7);
                border-radius: 18px;
            }
        """)
        box_layout = QVBoxLayout(login_box)
        box_layout.setContentsMargins(30, 30, 30, 30)
        box_layout.setSpacing(18)

        # Título
        title_label = QLabel("Sistema de Registro")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        box_layout.addWidget(title_label)

        # Usuario
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.15);
                border: 1.5px solid #fff;
                border-radius: 8px;
                color: #fff;
                padding: 8px 12px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #a29bfe;
                background: rgba(255,255,255,0.25);
            }
        """)
        box_layout.addWidget(self.input_usuario)

        # Contraseña
        self.input_contraseña = QLineEdit()
        self.input_contraseña.setPlaceholderText("Contraseña")
        self.input_contraseña.setEchoMode(QLineEdit.Password)
        self.input_contraseña.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.15);
                border: 1.5px solid #fff;
                border-radius: 8px;
                color: #fff;
                padding: 8px 12px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #a29bfe;
                background: rgba(255,255,255,0.25);
            }
        """)
        box_layout.addWidget(self.input_contraseña)

        # Botón Login
        self.boton_login = QPushButton("Iniciar Sesión")
        self.boton_login.setStyleSheet("""
            QPushButton {
                background: #fff;
                color: #5f27cd;
                font-size: 17px;
                font-weight: bold;
                border-radius: 20px;
                padding: 10px 0;
            }
            QPushButton:hover {
                background: #a29bfe;
                color: #fff;
            }
        """)
        self.boton_login.clicked.connect(self.verificar_login)
        box_layout.addWidget(self.boton_login)

        # Obtener números de administradores desde la base de datos
        try:
            conn = sqlite3.connect(obtener_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, celular FROM empleado WHERE rol LIKE '%admin%'")
            admins = cursor.fetchall()
            conn.close()
            if admins:
                admin_info = "\n".join([f"{nombre}: {celular}" for nombre, celular in admins])
                info_text = (
                    "Contacte al administrador si olvidó sus credenciales\n" +
                    admin_info
                )
            else:
                info_text = "Contacte al administrador si olvidó sus credenciales\n(No hay administradores registrados)"
        except Exception as e:
            info_text = "Contacte al administrador si olvidó sus credenciales\n(No se pudo obtener el número)"

        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 11px; color: #eee;")
        box_layout.addWidget(info_label)

        login_box.setLayout(box_layout)
        main_layout.addWidget(login_box, alignment=Qt.AlignCenter)

        self.input_usuario.returnPressed.connect(self.verificar_login)
        self.input_contraseña.returnPressed.connect(self.verificar_login)

    def verificar_login(self):
        nombre = self.input_usuario.text().strip()
        contraseña = self.input_contraseña.text().strip()

        if not nombre or not contraseña:
            self.show_message("Campos vacíos", "Por favor, ingrese su usuario y contraseña.", "warning")
            return

        self.boton_login.setEnabled(False)
        self.boton_login.setText("Verificando...")

        try:
            conn = sqlite3.connect(obtener_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id_empleado, contrasena_hash, rol FROM empleado WHERE nombre = ?", (nombre,))
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                id_empleado, hash_guardado, rol = resultado
                if bcrypt.checkpw(contraseña.encode(), hash_guardado.encode()):
                    self.close()
                    rol = rol.strip().lower()
                    archivo = "menu.py" if "admin" in rol or "gerente" in rol else "ventas.py"
                    try:
                        ruta_menu = os.path.abspath(os.path.join(os.path.dirname(__file__), archivo))
                        subprocess.Popen([sys.executable, ruta_menu, str(id_empleado)])
                    except Exception as e:
                        self.show_message("Error", str(e), "error")
                else:
                    self.show_message("Error de Autenticación", "La contraseña ingresada es incorrecta.", "error")
            else:
                self.show_message("Usuario no encontrado", "El usuario ingresado no existe en el sistema.", "error")
        except sqlite3.Error as e:
            self.show_message("Error de Base de Datos", f"Error al conectar con la base de datos:\n{str(e)}", "error")
        except Exception as e:
            self.show_message("Error del Sistema", f"Ocurrió un error inesperado:\n{str(e)}", "error")
        finally:
            self.boton_login.setEnabled(True)
            self.boton_login.setText("Iniciar Sesión")

    def show_message(self, title, message, msg_type):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if msg_type == "success":
            msg_box.setIcon(QMessageBox.Information)
        elif msg_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif msg_type == "error":
            msg_box.setIcon(QMessageBox.Critical)
        msg_box.exec_()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = LoginApp()
    ventana.showMaximized()
    sys.exit(app.exec_())