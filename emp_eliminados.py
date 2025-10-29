import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import Qt
from fpdf import FPDF
import tempfile
import os

class ReporteEmpleadosRetirados(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Empleados Retirados")
        self.setMinimumSize(1000, 600)

        # Fondo con imagen desde la base de datos (estilo devoluciones.py)
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QLabel, QGraphicsBlurEffect
        from PyQt5.QtCore import Qt
        def obtener_pixmap_fondo():
            try:
                conn = sqlite3.connect("pruebas.db")
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

        # Layout principal y widgets
        central = QWidget()
        main_layout = QVBoxLayout(central)
        self.setLayout(main_layout)

        # Buscador
        buscador_layout = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o CI...")
        self.input_busqueda.setStyleSheet("background: #E3F6FF; color: #311b92; border-radius: 8px; padding: 6px; font-size: 15px;")
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("background-color: #4AD0FF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_buscar.clicked.connect(self.buscar_empleados)
        buscador_layout.addWidget(self.input_busqueda)
        buscador_layout.addWidget(btn_buscar)
        main_layout.addLayout(buscador_layout)

        # Tabla de empleados eliminados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "CI", "Nombre", "Celular", "Rol", "Fecha de Creación", "Fecha de Borrado", "Acciones"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget { background: transparent; color: #E3F6FF; border: none; }
            QTableWidget::item { background: transparent; color: #E3F6FF; }
            QTableWidget::item:selected { background: rgba(74,208,255,0.12); }
            QHeaderView::section { background: rgba(106,27,154,0.45); color: #AEEFFF; border: none; padding: 6px; }
        """)
        main_layout.addWidget(self.tabla)

        # Botones inferiores
        botones_layout = QHBoxLayout()
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #4AD0FF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        btn_volver = QPushButton("Volver a Buscar Empleado")
        btn_volver.setStyleSheet("background-color: #AEEFFF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_volver.clicked.connect(self.volver_a_buscar_empleado)
        btn_pdf = QPushButton("Generar PDF")
        btn_pdf.setStyleSheet("background-color: #4AD0FF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_pdf.clicked.connect(self.generar_pdf)
        botones_layout.addWidget(btn_menu)
        botones_layout.addWidget(btn_volver)
        botones_layout.addWidget(btn_pdf)
        main_layout.addLayout(botones_layout)

        self.cargar_datos()
        self.setCentralWidget = self.setLayout  # Para compatibilidad con QMainWindow si se usa
    def resizeEvent(self, event):
        # Ajustar el pixmap de fondo cuando la ventana cambie de tamaño
        if hasattr(self, 'bg_label'):
            pixmap = self.bg_label.pixmap()
            if pixmap:
                self.bg_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        return super().resizeEvent(event)

    def ir_menu_principal(self):
        """Ir a menu.py"""
        try:
            import subprocess
            script_path = os.path.join(os.path.dirname(__file__), "menu.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir menu.py: {e}")

    def volver_a_buscar_empleado(self):
        try:
            from buscar_empleado import VerEmpleados
            self.ventana_buscar = VerEmpleados()
            self.ventana_buscar.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de búsqueda:\n{e}")

    def cargar_datos(self, filtro=""):
        conexion = sqlite3.connect("pruebas.db")
        cursor = conexion.cursor()

        if filtro:
            cursor.execute("""
                SELECT id_empleado, ci, nombre, celular, rol, fecha_creacion, fecha_borrado 
                FROM empleados_eliminados
                WHERE nombre LIKE ? OR ci LIKE ?
            """, (f"%{filtro}%", f"%{filtro}%"))
        else:
            cursor.execute("""
                SELECT id_empleado, ci, nombre, celular, rol, fecha_creacion, fecha_borrado 
                FROM empleados_eliminados
            """)
        datos = cursor.fetchall()
        self.tabla.setRowCount(len(datos))

        for fila_idx, fila in enumerate(datos):
            ci = fila[1]
            for col_idx in range(1, len(fila)):
                item = QTableWidgetItem(str(fila[col_idx]))
                item.setForeground(Qt.white)
                self.tabla.setItem(fila_idx, col_idx - 1, item)

            # Crear botones con estilo moderno
            layout_acciones = QHBoxLayout()
            btn_restaurar = QPushButton("Restaurar")
            btn_restaurar.setStyleSheet("background-color: #4AD0FF; color: #311b92; font-size: 14px; border-radius: 8px; font-weight: bold;")
            btn_restaurar.clicked.connect(lambda _, ci=ci: self.restaurar_empleado(ci))

            btn_borrar = QPushButton("Borrar Definitivamente")
            btn_borrar.setStyleSheet("background-color: #f44336; color: #E3F6FF; font-size: 14px; border-radius: 8px; font-weight: bold;")
            btn_borrar.clicked.connect(lambda _, ci=ci: self.borrar_definitivo(ci))

            contenedor_botones = QWidget()
            layout_acciones.addWidget(btn_restaurar)
            layout_acciones.addWidget(btn_borrar)
            contenedor_botones.setLayout(layout_acciones)

            self.tabla.setCellWidget(fila_idx, 6, contenedor_botones)

        conexion.close()

    def buscar_empleados(self):
        texto = self.input_busqueda.text().strip()
        self.cargar_datos(filtro=texto)

    def restaurar_empleado(self, ci):
        confirmacion = QMessageBox.question(
            self, "Confirmar", f"¿Deseas restaurar al empleado con CI {ci}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmacion == QMessageBox.Yes:
            try:
                con = sqlite3.connect("pruebas.db")
                cur = con.cursor()

                cur.execute("SELECT * FROM empleados_eliminados WHERE ci = ?", (ci,))
                datos = cur.fetchone()

                if datos:
                    cur.execute("""
                        INSERT INTO empleado (id_empleado, ci, nombre, celular, contrasena_hash, rol, fecha_creacion)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (datos[1], datos[2], datos[3], datos[4], "restaurada123", datos[5], datos[6]))  # Puedes cambiar el hash si lo deseas

                    cur.execute("DELETE FROM empleados_eliminados WHERE ci = ?", (ci,))
                    con.commit()
                    QMessageBox.information(self, "Éxito", "Empleado restaurado correctamente.")
                    self.cargar_datos()
                else:
                    QMessageBox.warning(self, "Error", "Empleado no encontrado.")
                con.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def borrar_definitivo(self, ci):
        confirmacion = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar PERMANENTEMENTE al empleado con CI {ci}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmacion == QMessageBox.Yes:
            try:
                con = sqlite3.connect("pruebas.db")
                cur = con.cursor()
                cur.execute("DELETE FROM empleados_eliminados WHERE ci = ?", (ci,))
                con.commit()
                con.close()
                QMessageBox.information(self, "Eliminado", "Empleado eliminado permanentemente.")
                self.cargar_datos()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def generar_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt="Reporte de Empleados Retirados", ln=True, align='C')

        headers = ["CI", "Nombre", "Celular", "Rol", "Fecha de Creación", "Fecha de Borrado"]
        for header in headers:
            pdf.cell(32, 10, txt=header, border=1)
        pdf.ln()

        for fila in range(self.tabla.rowCount()):
            for col in range(6):
                texto = self.tabla.item(fila, col).text() if self.tabla.item(fila, col) else ""
                pdf.cell(32, 10, txt=texto, border=1)
            pdf.ln()

        temp_path = tempfile.mktemp(suffix=".pdf")
        pdf.output(temp_path)
        os.startfile(temp_path)  # Windows

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = ReporteEmpleadosRetirados()
    ventana.showMaximized()
    sys.exit(app.exec_())