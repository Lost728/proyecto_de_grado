import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QWidget, QComboBox, QGraphicsBlurEffect
)
from PyQt5.QtCore import Qt
import sqlite3
import os
from datetime import datetime
import hashlib
import bcrypt
import subprocess
import pathlib

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

        # Fondo decorativo (image4.jpg)
        fondo = os.path.abspath(os.path.join(os.path.dirname(__file__), 'image4.jpg'))
        if os.path.exists(fondo):
            from PyQt5.QtGui import QPixmap
            self._bg_pixmap = QPixmap(fondo)
            self.bg_label = QLabel(self)
            self.bg_label.setScaledContents(True)
            blur = QGraphicsBlurEffect(self.bg_label)
            blur.setBlurRadius(12)
            self.bg_label.setGraphicsEffect(blur)
            self.bg_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.bg_label.lower()

        # Estilos base
        self.setStyleSheet("""
            QWidget { background: transparent; color: #ffffff; font-family: Arial; }
            QLabel { font-weight: bold; color: #ffffff; }
            QLineEdit { background: rgba(0,0,0,0.35); color: #ffffff; border-radius: 8px; padding: 6px; }
            QPushButton { color: #22223b; font-weight: 700; }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20,20,20,20)
        main_layout.setSpacing(10)
        main_widget.setLayout(main_layout)
        main_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(main_widget)

        title = QLabel("Insertar Nuevo Empleado")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; padding-bottom: 8px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Top buttons (volver + menu) en una fila
        top_btns = QHBoxLayout()
        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background: rgba(255,255,255,0.06); color:#ffffff; border-radius:8px; padding:8px 14px; border:1px solid rgba(255,255,255,0.06);")
        btn_volver.clicked.connect(self.volver_a_ver_empleado)
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6); color:#22223b; border-radius:8px; padding:8px 14px; font-weight:700;")
        btn_menu.clicked.connect(self.menu_principal)
        top_btns.addWidget(btn_volver)
        top_btns.addStretch(1)
        top_btns.addWidget(btn_menu)
        main_layout.addLayout(top_btns)

        # Formulario en grid (etiquetas | campos)
        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(18)
        form_grid.setVerticalSpacing(10)
        row = 0
        self.campos = {}
        self.campos["nombre"] = QLineEdit()
        form_grid.addWidget(QLabel("Nombre:"), row, 0)
        form_grid.addWidget(self.campos["nombre"], row, 1)
        row += 1
        self.campos["apellidos"] = QLineEdit()
        form_grid.addWidget(QLabel("Apellidos:"), row, 0)
        form_grid.addWidget(self.campos["apellidos"], row, 1)
        row += 1
        self.campos["ci"] = QLineEdit()
        form_grid.addWidget(QLabel("CI:"), row, 0)
        form_grid.addWidget(self.campos["ci"], row, 1)
        row += 1
        self.campos["celular"] = QLineEdit()
        form_grid.addWidget(QLabel("Celular:"), row, 0)
        form_grid.addWidget(self.campos["celular"], row, 1)
        row += 1
        # Rol combo
        combo_rol = QComboBox()
        combo_rol.addItems(["administrador", "empleado"])
        form_grid.addWidget(QLabel("Rol:"), row, 0)
        form_grid.addWidget(combo_rol, row, 1)
        self.campos["rol"] = combo_rol
        row += 1
        # Contraseñas
        self.campos["contrasena_hash"] = QLineEdit()
        self.campos["contrasena_hash"].setEchoMode(QLineEdit.Password)
        form_grid.addWidget(QLabel("Contraseña:"), row, 0)
        form_grid.addWidget(self.campos["contrasena_hash"], row, 1)
        row += 1
        self.campos["confirmar_contrasena"] = QLineEdit()
        self.campos["confirmar_contrasena"].setEchoMode(QLineEdit.Password)
        form_grid.addWidget(QLabel("Confirmar Contraseña:"), row, 0)
        form_grid.addWidget(self.campos["confirmar_contrasena"], row, 1)
        row += 1

        # Botones de acción (centrados, justo después del formulario)
        buttons_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6); color:#22223b; border-radius:10px; padding:8px 16px; font-weight:700;")
        btn_guardar.clicked.connect(self.guardar_empleado)
        buttons_layout.addWidget(btn_guardar)
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setStyleSheet("background: rgba(255,255,255,0.06); color:#ffffff; border-radius:10px; padding:8px 16px; border:1px solid rgba(255,255,255,0.06);")
        btn_limpiar.clicked.connect(self.limpiar_formulario)
        buttons_layout.addWidget(btn_limpiar)

        # Agregar grid y botones al layout principal
        form_container = QWidget()
        form_container.setLayout(form_grid)
        main_layout.addWidget(form_container)
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch(1)

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
        
    def menu_principal(self):
        try:
            script_path = os.path.join(os.path.dirname(__file__), "menu.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el menú principal:\n{e}")

    def volver_a_ver_empleado(self):
        try:
            from buscar_empleado import VerEmpleados
            self.ventana_buscar = VerEmpleados()
            self.ventana_buscar.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de búsqueda:\n{e}")

    def resizeEvent(self, event):
        try:
            if hasattr(self, '_bg_pixmap') and self._bg_pixmap and hasattr(self, 'bg_label'):
                scaled = self._bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.bg_label.setPixmap(scaled)
                self.bg_label.resize(self.size())
                self.bg_label.lower()
        except Exception:
            pass
        return super().resizeEvent(event)

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