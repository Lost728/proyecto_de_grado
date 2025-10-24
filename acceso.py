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
        self.setWindowTitle("Acceso al sistema")
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
        login_box.setFixedWidth(400)
        login_box.setStyleSheet("""
            QWidget {
                background: rgba(60, 20, 100, 0.85);
                border-radius: 28px;
                border: 2.5px solid #a259f7;
                box-shadow: 0 0 32px 0 #7c3aed;
            }
        """)
        box_layout = QVBoxLayout(login_box)
        box_layout.setContentsMargins(30, 30, 30, 30)
        box_layout.setSpacing(18)

        # Título
        title_label = QLabel("Acceso al Sistema")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #7ed6fa; font-size: 32px; font-weight: bold; letter-spacing: 2px; text-shadow: 0 2px 12px #a259f7;")
        box_layout.addWidget(title_label)

        # Usuario
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                background: rgba(120, 80, 200, 0.18);
                border: 2px solid #7ed6fa;
                border-radius: 12px;
                color: #fff;
                padding: 12px 16px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #ffb6e6;
                background: rgba(120, 80, 200, 0.28);
            }
        """)
        box_layout.addWidget(self.input_usuario)

        # Contraseña
        self.input_contraseña = QLineEdit()
        self.input_contraseña.setPlaceholderText("Contraseña")
        self.input_contraseña.setEchoMode(QLineEdit.Password)
        self.input_contraseña.setStyleSheet("""
            QLineEdit {
                background: rgba(120, 80, 200, 0.18);
                border: 2px solid #ffb6e6;
                border-radius: 12px;
                color: #fff;
                padding: 12px 16px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #7ed6fa;
                background: rgba(120, 80, 200, 0.28);
            }
        """)
        box_layout.addWidget(self.input_contraseña)

        # Botón Login
        self.boton_login = QPushButton("Iniciar Sesión")
        self.boton_login.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6);
                color: #22223b;
                font-size: 21px;
                font-weight: bold;
                border-radius: 24px;
                padding: 14px 0;
                letter-spacing: 1px;
                box-shadow: 0 2px 16px #a259f7;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffb6e6, stop:1 #7ed6fa);
                color: #7ed6fa;
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
        info_label.setStyleSheet("font-size: 13px; color: #7ed6fa; background: transparent; margin-top: 8px;")
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
                    archivo = "caja_diaria.py" if "admin" in rol or "gerente" in rol else "caja_diariaE.py"
                    try:
                        ruta_menu = os.path.abspath(os.path.join(os.path.dirname(__file__), archivo))
                        subprocess.Popen([sys.executable, ruta_menu, str(id_empleado)])
                        # Abrir caja_diaria.py para todos los usuarios (ya no necesario, solo se abre el archivo correspondiente)
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