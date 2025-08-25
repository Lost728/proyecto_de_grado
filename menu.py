import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QWidget, QLabel, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from datetime import datetime
import shutil

def abrir_aplicacion(nombre_py):
    if not os.path.isabs(nombre_py):
        base_dir = os.path.dirname(__file__)
        nombre_py = os.path.join(base_dir, nombre_py)
    if os.path.exists(nombre_py):
        try:
            subprocess.Popen([sys.executable, nombre_py])
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo abrir el ejecutable:\n{e}")
            return
    else:
        QMessageBox.warning(None, "Archivo no encontrado", f"No se encontró el archivo:\n{nombre_py}")

class MenuPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menú Principal - Sistema de Farmacia")
        self._construir_ui()

    def _construir_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Título simple
        title = QLabel("Menú Principal")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Lista de botones y scripts
        botones = [
            ("Ver Productos", "ver_productos.py"),
            ("Insertar Producto", "insertar_producto.py"),
            ("Ventas", "ventas_admin.py"),
            ("Ver Empleados", "buscar_empleado.py"),
            ("Estadisticas", "estadistica.py"),
            ("Insertar Empleado", "insertar_empleado.py"),
            ("Reporte General", "reporte.py"),
            ("Reporte de Productos", "reporte_producto.py"),
            ("Productos Eliminados", "productos_eliminados.py"),
            ("Empleados Eliminados", "emp_eliminados.py"),
            ("Historial de Producto", "historial_prod.py"),
            ("Ver Lotes", "ver_lotes.py"),
            ("Ver Proveedor", "ver_proveedor.py"),
            #("Exportar Base de Datos", "exportar_db"),
            ("Volver", "volver")
        ]

        for texto, script in botones:
            btn = QPushButton(texto)
            btn.setMinimumHeight(40)
            if script == "volver":
                btn.clicked.connect(self.volver_a_login)
            elif script == "exportar_db":
                btn.clicked.connect(self.exportar_base_datos)
            else:
                btn.clicked.connect(lambda _, s=script: self.abrir_script(s))
            layout.addWidget(btn)

        layout.addStretch(1)

    def abrir_script(self, script_name):
        if not os.path.isabs(script_name):
            base_dir = os.path.dirname(__file__)
            script_path = os.path.join(base_dir, script_name)
        else:
            script_path = script_name
        abrir_aplicacion(script_path)
        self.close()

    def exportar_base_datos(self):
        db_path = os.path.join(os.path.dirname(__file__), "pruebas.db")
        if not os.path.exists(db_path):
            QMessageBox.warning(self, "Base de datos no encontrada", f"No se encontró la base de datos en:\n{db_path}")
            return
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        sugerido = f"respaldo_pruebas_{fecha}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Base de Datos",
            sugerido,
            "Base de datos (*.db);;Todos los archivos (*)"
        )
        if not file_path:
            return
        try:
            shutil.copy2(db_path, file_path)
            QMessageBox.information(self, "Exportación exitosa", f"Base de datos exportada a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar la base de datos:\n{e}")

    def volver_a_login(self):
        """Cerrar menú y volver a login.py"""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "login.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir login.py: {e}")

def main():
    app = QApplication(sys.argv)
    window = MenuPrincipal()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MenuPrincipal()
    window.showMaximized()
    sys.exit(app.exec_())