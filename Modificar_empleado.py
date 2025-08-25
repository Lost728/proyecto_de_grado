import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFormLayout
)
import subprocess
import bcrypt

def obtener_db_path():
    """Retorna la ruta de la base de datos 'pruebas.db'."""
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

# ----------------- Ventana Principal -----------------

class ModificarEmpleadoWindow(QMainWindow):
    def __init__(self, empleado_id):
        super().__init__()
        self.setWindowTitle("Modificar Empleado")
        self.setGeometry(200, 200, 500, 550)
        self.empleado_id = empleado_id

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 13px;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 3px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #aaa;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                min-width: 80px;
            }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        form_layout = QFormLayout()
        form_layout.setContentsMargins(30, 20, 30, 20)

        self.inputs = {}

        self.inputs["nombre"] = QLineEdit()
        form_layout.addRow("Nombre:", self.inputs["nombre"])

        # NUEVO: Apellidos
        self.inputs["apellidos"] = QLineEdit()
        form_layout.addRow("Apellidos:", self.inputs["apellidos"])

        self.inputs["CI"] = QLineEdit()
        form_layout.addRow("CI:", self.inputs["CI"])

        self.inputs["celular"] = QLineEdit()
        form_layout.addRow("Celular:", self.inputs["celular"])

        self.inputs["rol"] = QLineEdit()
        form_layout.addRow("Rol:", self.inputs["rol"])

        self.inputs["contrasena"] = QLineEdit()
        self.inputs["contrasena"].setEchoMode(QLineEdit.Password)
        self.inputs["contrasena"].setPlaceholderText("Dejar vacío para no cambiar")
        form_layout.addRow("Nueva Contraseña:", self.inputs["contrasena"])

        self.inputs["confirmar_contrasena"] = QLineEdit()
        self.inputs["confirmar_contrasena"].setEchoMode(QLineEdit.Password)
        self.inputs["confirmar_contrasena"].setPlaceholderText("Repetir nueva contraseña")
        form_layout.addRow("Confirmar Nueva Contraseña:", self.inputs["confirmar_contrasena"])

        main_layout.addLayout(form_layout)

        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_guardar.clicked.connect(self.guardar_cambios)
        main_layout.addWidget(btn_guardar)

        btn_volver = QPushButton("Volver a la lista de empleados")
        btn_volver.setStyleSheet("background-color: #95a5a6; color: white;")
        btn_volver.clicked.connect(self.volver_a_lista_empleados)
        main_layout.addWidget(btn_volver)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre, apellidos, CI, celular, rol
                FROM empleado WHERE id_empleado = ?
            """, (self.empleado_id,))
            empleado = cursor.fetchone()
            conn.close()

            if empleado:
                self.inputs["nombre"].setText(str(empleado[0]) if empleado[0] else "")
                self.inputs["apellidos"].setText(str(empleado[1]) if empleado[1] else "")
                self.inputs["CI"].setText(str(empleado[2]) if empleado[2] else "")
                self.inputs["celular"].setText(str(empleado[3]) if empleado[3] else "")
                self.inputs["rol"].setText(str(empleado[4]) if empleado[4] else "")
            else:
                QMessageBox.critical(self, "Error", "No se encontró el empleado.")
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el empleado: {e}")

    def guardar_cambios(self):
        datos = {key: widget.text().strip() for key, widget in self.inputs.items()}

        # Validar coincidencia de contraseñas si se va a cambiar
        if datos["contrasena"]:
            if datos["contrasena"] != datos["confirmar_contrasena"]:
                QMessageBox.warning(self, "Advertencia", "Las contraseñas no coinciden. Por favor, verifique.")
                return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            if datos["contrasena"]:
                nueva_contrasena_hash = bcrypt.hashpw(datos["contrasena"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("""
                    UPDATE empleado SET
                        nombre = ?, apellidos = ?, CI = ?, celular = ?, rol = ?, contrasena_hash = ?
                    WHERE id_empleado = ?
                """, (
                    datos["nombre"], datos["apellidos"], datos["CI"], datos["celular"],
                    datos["rol"], nueva_contrasena_hash, self.empleado_id
                ))
            else:
                cursor.execute("""
                    UPDATE empleado SET
                        nombre = ?, apellidos = ?, CI = ?, celular = ?, rol = ?
                    WHERE id_empleado = ?
                """, (
                    datos["nombre"], datos["apellidos"], datos["CI"], datos["celular"],
                    datos["rol"], self.empleado_id
                ))

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Empleado modificado correctamente.")
            self.volver_a_lista_empleados()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo modificar el empleado: {e}")

    def volver_a_lista_empleados(self):
        abrir_aplicacion("buscar_empleado.py")
        self.close()

def abrir_aplicacion(nombre_py):
    try:
        script_path = os.path.join(os.path.dirname(__file__), nombre_py)
        subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        QMessageBox.critical(None, "Error", f"No se pudo abrir el archivo {nombre_py}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            empleado_id = int(sys.argv[1])
            app = QApplication(sys.argv)
            window = ModificarEmpleadoWindow(empleado_id)
            window.show()
            sys.exit(app.exec_())
        except (ValueError, IndexError):
            print("Error: Debe proporcionar un ID de empleado válido como argumento.")
            sys.exit(1)
    else:
        print("Debe proporcionar el ID del empleado como argumento.")