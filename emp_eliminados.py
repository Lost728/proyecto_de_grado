import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QHBoxLayout, QLineEdit
)
from fpdf import FPDF
import tempfile
import os

class ReporteEmpleadosRetirados(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Empleados Retirados")
        self.setGeometry(100, 100, 1000, 600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        buscador_layout = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o CI...")
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar_empleados)
        self.input_busqueda.returnPressed.connect(self.buscar_empleados)
        buscador_layout.addWidget(self.input_busqueda)
        buscador_layout.addWidget(btn_buscar)
        # Botón para volver atrás
        self.boton_volver = QPushButton("Volver a Buscar Empleado")
        self.boton_volver.clicked.connect(self.volver_a_buscar_empleado)
        buscador_layout.addWidget(self.boton_volver)
        # Botón para ir a menú principal
        self.boton_menu = QPushButton("Menú Principal")
        self.boton_menu.clicked.connect(self.ir_menu_principal)
        buscador_layout.addWidget(self.boton_menu)
        self.layout.addLayout(buscador_layout)

        # Tabla de empleados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "CI", "Nombre", "Celular", "Rol", "Fecha de Creación", "Fecha de Borrado", "Acciones"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.tabla)

        # Botón de PDF
        self.boton_pdf = QPushButton("Previsualizar PDF")
        self.boton_pdf.clicked.connect(self.generar_pdf)
        self.layout.addWidget(self.boton_pdf)

        self.cargar_datos()

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
                self.tabla.setItem(fila_idx, col_idx - 1, QTableWidgetItem(str(fila[col_idx])))

            # Crear botones
            layout_acciones = QHBoxLayout()
            btn_restaurar = QPushButton("Restaurar")
            btn_restaurar.setStyleSheet("background-color: #4CAF50; color: white;")
            btn_restaurar.clicked.connect(lambda _, ci=ci: self.restaurar_empleado(ci))

            btn_borrar = QPushButton("Borrar Definitivamente")
            btn_borrar.setStyleSheet("background-color: #f44336; color: white;")
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