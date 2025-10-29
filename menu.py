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
import sqlite3

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
        # Fondo con imagen 'mar' desde la base de datos (estilo devoluciones.py)
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QLabel, QGraphicsBlurEffect
        def obtener_pixmap_fondo():
            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "pruebas.db"))
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
            blur.setBlurRadius(14)
            self.bg_label.setGraphicsEffect(blur)
        else:
            self.bg_label.setStyleSheet("background: #6a1b9a;")
        self.bg_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.bg_label.lower()

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Título destacado mejorado
        title = QLabel("Menú Principal")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #AEEFFF;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7b1fa2, stop:1 #4AD0FF);
            padding: 28px 36px;
            border-radius: 22px;
            margin-bottom: 38px;
            letter-spacing: 2.5px;
            box-shadow: 0 8px 32px rgba(74,208,255,0.18);
        """)
        layout.addWidget(title)

        # Lista de botones y scripts (sin duplicados y con nombres claros)
        botones = [
            ("Realizar ventas", "ventas_admin.py"),
            ("Ventas empleados", "ventas_empleados.py"),
            ("Ventas pruebas", "ventas_pruebas.py"),
            ("Ver Productos", "ver_productos.py"),
            ("Registrar Producto", "registrar_producto.py"),
            ("Empleados", "buscar_empleado.py"),
            ("Registrar Empleado", "registrar_emp.py"),
            ("Devoluciones", "devoluciones.py"),
            ("Lotes", "ver_lotes.py"),
            ("Registrar Lote", "registrar_lote.py"),
            ("Proveedores", "ver_proveedor.py"),
            ("Registrar Proveedor", "registrar_proveedor.py"),
            ("Productos Eliminados", "productos_eliminados.py"),
            ("Empleados Retirados", "emp_eliminados.py"),
            ("Historial de Producto", "historial_prod.py"),
            ("Estadísticas", "estadistica.py"),
            ("Reporte de Productos", "reporte_productos.py"),
            ("Reporte de Empleados", "reporte_emp.py"),
            ("Volver", "acceso.py"),
        ]

        for texto, script in botones:
            btn = QPushButton(texto)
            btn.setMinimumHeight(44)
            btn.setMaximumWidth(320)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4AD0FF, stop:1 #7b1fa2);
                    color: #fff;
                    font-weight: bold;
                    border-radius: 14px;
                    font-size: 18px;
                    margin-bottom: 12px;
                    box-shadow: 0 2px 8px rgba(74,208,255,0.18);
                    padding: 10px 0;
                    border: none;
                    transition: background 0.3s, color 0.3s;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b1fa2, stop:1 #4AD0FF);
                    color: #AEEFFF;
                }
                QPushButton:pressed {
                    background: #311b92;
                    color: #fff;
                }
            """)
            if script == "volver":
                btn.clicked.connect(self.volver_a_login)
            elif script == "exportar_db":
                btn.clicked.connect(self.exportar_base_datos)
            else:
                btn.clicked.connect(lambda _, s=script: self.abrir_script(s))
            layout.addWidget(btn, alignment=Qt.AlignHCenter)

        layout.addStretch(1)
    def resizeEvent(self, event):
        # Ajustar el pixmap de fondo cuando la ventana cambie de tamaño
        if hasattr(self, 'bg_label'):
            pixmap = self.bg_label.pixmap()
            if pixmap:
                self.bg_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        return super().resizeEvent(event)

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