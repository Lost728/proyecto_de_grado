import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QWidget, QComboBox
)
from PyQt5.QtCore import Qt
import sqlite3
import os
from datetime import datetime
import hashlib
import bcrypt
import subprocess
import pathlib

# ----------------- CÓDIGO CORREGIDO -----------------

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

class InsertarEmpleadoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Insertar Nuevo Empleado")
        self.setGeometry(100, 100, 600, 400)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        title = QLabel("Insertar Nuevo Empleado")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px;")
        btn_volver.clicked.connect(self.volver_a_ver_empleado)
        main_layout.addWidget(btn_volver, alignment=Qt.AlignLeft)

        form_layout = QVBoxLayout()
        self.campos = {}

        self.campos["nombre"] = self.crear_campo("Nombre:", QLineEdit(), form_layout)
        # Nuevo campo para apellidos
        self.campos["apellidos"] = self.crear_campo("Apellidos:", QLineEdit(), form_layout)
        self.campos["ci"] = self.crear_campo("CI:", QLineEdit(), form_layout)
        self.campos["celular"] = self.crear_campo("Celular:", QLineEdit(), form_layout)

        label_rol = QLabel("Rol:")
        combo_rol = QComboBox()
        combo_rol.addItems(["administrador", "empleado"])
        form_layout.addWidget(label_rol)
        form_layout.addWidget(combo_rol)
        self.campos["rol"] = combo_rol

        # Contraseña y Confirmar Contraseña
        self.campos["contrasena_hash"] = self.crear_campo("Contraseña:", QLineEdit(), form_layout)
        self.campos["contrasena_hash"].setEchoMode(QLineEdit.Password)
        self.campos["confirmar_contrasena"] = self.crear_campo("Confirmar Contraseña:", QLineEdit(), form_layout)
        self.campos["confirmar_contrasena"].setEchoMode(QLineEdit.Password)

        buttons_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        btn_guardar.clicked.connect(self.guardar_empleado)
        buttons_layout.addWidget(btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setStyleSheet("background-color: #FFA500; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        btn_limpiar.clicked.connect(self.limpiar_formulario)
        buttons_layout.addWidget(btn_limpiar)

        form_layout.addLayout(buttons_layout)
        main_layout.addLayout(form_layout)

        self.campos["ci"].setPlaceholderText("Ejemplo: 12345678")

    def crear_campo(self, label_text, widget, layout):
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        return widget

    def guardar_empleado(self):
        contraseña_plana = self.campos["contrasena_hash"].text().strip()
        confirmar_contraseña = self.campos["confirmar_contrasena"].text().strip()
        if not contraseña_plana or len(contraseña_plana) < 4:
            QMessageBox.warning(self, "Advertencia", "La contraseña es obligatoria y debe tener al menos 4 caracteres.")
            return
        if contraseña_plana != confirmar_contraseña:
            QMessageBox.warning(self, "Advertencia", "Las contraseñas no coinciden. Por favor, verifique.")
            return

        hash_contraseña = bcrypt.hashpw(contraseña_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        datos = {
            "nombre": self.campos["nombre"].text().strip(),
            "apellidos": self.campos["apellidos"].text().strip(),
            "ci": self.campos["ci"].text().strip(),
            "contrasena_hash": hash_contraseña,
            "celular": self.campos["celular"].text().strip(),
            "rol": self.campos["rol"].currentText()
        }

        if not datos["nombre"] or not datos["apellidos"] or not datos["ci"] or not datos["celular"]:
            QMessageBox.warning(self, "Advertencia", "Nombre, Apellidos, CI y Celular son obligatorios.")
            return
        
        if not datos["ci"].isdigit() or len(datos["ci"]) < 4:
            QMessageBox.warning(self, "Advertencia", "El CI debe ser numérico y tener al menos 4 dígitos.")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Asegúrate de que tu tabla empleado tenga el campo 'apellidos'
            cursor.execute("""
                INSERT INTO empleado (
                    CI, nombre, apellidos, celular, contrasena_hash, rol
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                int(datos["ci"]),
                datos["nombre"],
                datos["apellidos"],
                datos["celular"],
                datos["contrasena_hash"],
                datos["rol"]
            ))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Empleado guardado correctamente")
            self.limpiar_formulario()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: empleado.CI" in str(e):
                QMessageBox.warning(self, "Advertencia", "El CI ya existe. Ingrese uno diferente.")
            elif "CHECK constraint failed: rol" in str(e):
                QMessageBox.critical(self, "Error de validación", "El valor del Rol no es válido. Debe ser 'administrador' o 'empleado'.")
            else:
                QMessageBox.critical(self, "Error de integridad", f"Error de integridad de la base de datos: {e}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el empleado: {e}")
        except ValueError:
            QMessageBox.critical(self, "Error de tipo de dato", "El valor de CI no es un número válido.")

    def limpiar_formulario(self):
        for campo in self.campos.values():
            if isinstance(campo, QLineEdit):
                campo.clear()
            elif isinstance(campo, QComboBox):
                campo.setCurrentIndex(0)
        self.campos["nombre"].setFocus()

    def volver_a_ver_empleado(self):
        try:
            from buscar_empleado import VerEmpleados
            self.ventana_buscar = VerEmpleados()
            self.ventana_buscar.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de búsqueda:\n{e}")

def abrir_aplicacion(nombre_py):
    rutas = []
    if hasattr(sys, '_MEIPASS'):
        rutas.append(sys._MEIPASS)
    # Ruta del directorio padre para encontrar archivos en la estructura del proyecto
    rutas.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

    exe_name = nombre_py.replace('.py', '.exe')

    for base_path in rutas:
        exe_path = os.path.join(base_path, nombre_py.replace('.py', '.exe'))
        py_path = os.path.join(base_path, nombre_py)
        if os.path.exists(exe_path):
            try:
                cmd = [exe_path]
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen(cmd, startupinfo=startupinfo)
                else:
                    subprocess.Popen(cmd)
                return
            except Exception as e:
                QMessageBox.critical(None, "❌ Error", f"No se pudo abrir el ejecutable:\n{e}")
                return
        elif os.path.exists(py_path):
            try:
                cmd = [sys.executable, py_path]
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen(cmd, startupinfo=startupinfo)
                else:
                    subprocess.Popen(cmd)
                return
            except Exception as e:
                QMessageBox.critical(None, "❌ Error", f"No se pudo abrir el script:\n{e}")
                return

    QMessageBox.warning(None, "⚠️ Archivo no encontrado",
                        f"No se encontró el archivo:\n{exe_name} ni {nombre_py}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InsertarEmpleadoWindow()
    window.showMaximized()
    sys.exit(app.exec_())