import sys
import sqlite3
import bcrypt
import subprocess
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

class LoginApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio de Sesión")
        self.setFixedSize(350, 300)
        self.setup_ui()
        self.center_window()

    def center_window(self):
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Sistema de Farmacia")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        main_layout.addWidget(title_label)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        main_layout.addWidget(self.input_usuario)

        self.input_contraseña = QLineEdit()
        self.input_contraseña.setPlaceholderText("Contraseña")
        self.input_contraseña.setEchoMode(QLineEdit.Password)
        main_layout.addWidget(self.input_contraseña)

        self.boton_login = QPushButton("Iniciar Sesión")
        self.boton_login.clicked.connect(self.verificar_login)
        main_layout.addWidget(self.boton_login)

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
        info_label.setStyleSheet("font-size: 11px; color: gray;")
        main_layout.addWidget(info_label)

        self.setLayout(main_layout)

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
    ventana.show()
    sys.exit(app.exec_())