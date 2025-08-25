# Módulos estándar
import sys
import os
import sqlite3
import shutil
import subprocess
import cv2  # Asegúrate de tener instalado opencv-python
from datetime import datetime

# Módulos de PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QDateEdit, QComboBox, QFileDialog
)
from PyQt5.QtCore import QDate

# Constantes
DB_NAME = "pruebas.db"

# Funciones de utilidad
def obtener_db_path():
    """
    Determina la ruta de la base de datos 'pruebas.db'
    buscando en la carpeta del ejecutable o en el directorio de trabajo.
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        db_path = os.path.join(exe_dir, DB_NAME)
        if os.path.exists(db_path):
            return db_path
        base_path = sys._MEIPASS
        return os.path.join(base_path, DB_NAME)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), DB_NAME))

def abrir_aplicacion(nombre_py, argumentos=None):
    """
    Abre el archivo .exe si existe, si no, ejecuta el .py en un nuevo proceso.
    """
    base_paths = [os.getcwd()]
    if hasattr(sys, '_MEIPASS'):
        base_paths.append(sys._MEIPASS)

    for base_path in base_paths:
        exe_path = os.path.join(base_path, nombre_py.replace('.py', '.exe'))
        py_path = os.path.join(base_path, nombre_py)
       
        if os.path.exists(exe_path):
            cmd = [exe_path]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return
        elif os.path.exists(py_path):
            cmd = [sys.executable, py_path]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return

    QMessageBox.warning(None, "⚠️ Archivo no encontrado",
                        f"No se encontró el archivo:\n{nombre_py.replace('.py', '.exe')} ni {nombre_py}")

# Clases
class ModificarProductoWindow(QMainWindow):
    def __init__(self, producto_id, empleado_actual_id):
        super().__init__()
        self.producto_id = producto_id
        self.empleado_actual_id = empleado_actual_id
        self.setWindowTitle("Modificar Producto")
        self.setGeometry(200, 200, 500, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f6fb;
            }
            QLabel {
                font-size: 15px;
                color: #22223b;
            }
            QLineEdit, QDateEdit {
                background-color: #ffffff;
                border: 2px solid #dbe2ef;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                color: #22223b;
            }
            QLineEdit:focus, QDateEdit:focus {
                border-color: #a3cef1;
                background-color: #f0f4fa;
            }
            QPushButton {
                background-color: #b7e4c7;
                color: #22223b;
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d8f3dc;
            }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Campos del formulario actualizados para coincidir con la tabla 'productos'
        self.inputs = {}
        campos = [
            ("nombre", "Nombre"),
            ("codigo", "Código"),
            ("imagen", "Imagen"),
            ("precio", "Precio"),
            ("stock", "Stock"),
            ("fecha_venc", "Fecha de Vencimiento"),
        ]
       
        for key, label_text in campos:
            label = QLabel(label_text)
            main_layout.addWidget(label)
            if key == "fecha_venc":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("yyyy-MM-dd")
            else:
                widget = QLineEdit()
            self.inputs[key] = widget
            main_layout.addWidget(widget)

        # Label y combo box para empleado
        label_empleado = QLabel("Empleado que modifica:")
        main_layout.addWidget(label_empleado)
        self.combo_empleado = QComboBox()
        main_layout.addWidget(self.combo_empleado)
        self._cargar_empleados()

        # Botón guardar
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.clicked.connect(self.guardar_cambios)
        main_layout.addWidget(btn_guardar)

        # Botón volver
        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ef;
                color: #22223b;
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c9d6e3;
            }
        """)
        btn_volver.clicked.connect(self.close)
        main_layout.addWidget(btn_volver)

        # Layout para imagen con botones de cargar imagen y tomar foto
        imagen_layout = QHBoxLayout()
        imagen_layout.addWidget(self.inputs["imagen"])

        btn_cargar_imagen = QPushButton("Cargar Imagen")
        btn_cargar_imagen.clicked.connect(self.cargar_imagen)
        imagen_layout.addWidget(btn_cargar_imagen)

        btn_camara = QPushButton("Tomar Foto")
        btn_camara.clicked.connect(self.tomar_foto)
        imagen_layout.addWidget(btn_camara)

        main_layout.addLayout(imagen_layout)

        self.cargar_datos()

    def _cargar_empleados(self):
        """Carga todos los empleados en el combo."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id_empleado, nombre FROM empleado")
        empleados = cursor.fetchall()
        conn.close()
        self.combo_empleado.clear()
        for id_emp, nombre in empleados:
            self.combo_empleado.addItem(f"{nombre} (ID:{id_emp})", id_emp)

    def cargar_datos(self):
        """Carga los datos del producto seleccionado en los campos del formulario."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_producto, p.codigo, p.imagen, p.nombre, p.precio, p.stock, p.fecha_venc, p.id_empleado, IFNULL(e.nombre, 'Sin asignar')
                FROM productos p
                LEFT JOIN empleado e ON p.id_empleado = e.id_empleado
                WHERE p.id_producto = ?
            """, (self.producto_id,))
            producto = cursor.fetchone()
            conn.close()

            if producto:
                (id_producto, codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado, nombre_empleado) = producto
                self.inputs["codigo"].setText(str(codigo))
                self.inputs["imagen"].setText(str(imagen))
                self.inputs["nombre"].setText(str(nombre))
                self.inputs["precio"].setText(str(precio))
                self.inputs["stock"].setText(str(stock))
                
                # Si fecha_venc es tipo 'YYYYMMDD' (ejemplo: 20250811)
                fecha_str = str(fecha_venc)
                if len(fecha_str) == 8:
                    year = int(fecha_str[:4])
                    month = int(fecha_str[4:6])
                    day = int(fecha_str[6:8])
                    qdate = QDate(year, month, day)
                    self.inputs["fecha_venc"].setDate(qdate)
                else:
                    self.inputs["fecha_venc"].setDate(QDate.currentDate())

                # Mostrar el nombre del empleado en un QLabel
                if hasattr(self, "label_empleado"):
                    self.label_empleado.setText(f"Modificado por: {nombre_empleado}")
                else:
                    self.label_empleado = QLabel(f"Modificado por: {nombre_empleado}")
                    self.centralWidget().layout().insertWidget(0, self.label_empleado)

                # Establecer el empleado actual en el combo box
                index = self.combo_empleado.findData(id_empleado)
                if index >= 0:
                    self.combo_empleado.setCurrentIndex(index)
            else:
                QMessageBox.critical(self, "Error", "No se encontró el producto.")
                self.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de base de datos", f"Error al cargar datos: {e}")
            self.close()

    def guardar_cambios(self):
        """Guarda los cambios realizados en el producto en la base de datos."""
        datos = {}
        for key, widget in self.inputs.items():
            if key == "fecha_venc":
                datos[key] = widget.date().toString("yyyy-MM-dd")
            else:
                datos[key] = widget.text().strip()

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if not datos["nombre"] or not datos["codigo"]:
                QMessageBox.warning(self, "⚠️ Error de validación", "Nombre y código son obligatorios.")
                return
            
            try:
                datos["precio"] = float(datos["precio"])
                datos["stock"] = int(datos["stock"])
            except Exception as e:
                QMessageBox.warning(self, "⚠️ Error de validación", "Precio y stock deben ser números.")
                return

            # Convierte la fecha a formato timestamp INTEGER
            try:
                fecha_dt = QDate.fromString(datos["fecha_venc"], "yyyy-MM-dd")
                fecha_py = fecha_dt.toPyDate()
                fecha_venc_timestamp = int(datetime.combine(fecha_py, datetime.min.time()).timestamp())
            except Exception:
                fecha_venc_timestamp = 0

            cursor.execute("""
                UPDATE productos SET
                    codigo = ?, imagen = ?, nombre = ?, precio = ?,
                    stock = ?, fecha_venc = ?, id_empleado = ?
                WHERE id_producto = ?
            """, (
                datos["codigo"],
                datos["imagen"],
                datos["nombre"],
                datos["precio"],
                datos["stock"],
                fecha_venc_timestamp,
                self.combo_empleado.currentData(),  # <--- El empleado seleccionado
                self.producto_id
            ))
            conn.commit()

            # Mostrar el nombre del administrador que modificó
            cursor.execute("SELECT nombre FROM empleado WHERE id_empleado = ?", (self.combo_empleado.currentData(),))
            nombre_admin = cursor.fetchone()
            if nombre_admin:
                QMessageBox.information(self, "Éxito", f"Producto modificado correctamente\nModificado por: {nombre_admin[0]}")
            else:
                QMessageBox.information(self, "Éxito", "Producto modificado correctamente\nModificado por: (desconocido)")

            conn.close()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo modificar el producto: {e}")

    def _edit_product(self, product_id):
        self.close()
        abrir_aplicacion("Modificar_producto.py", [str(product_id), str(self.empleado_actual_id)])

    def cargar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if ruta:
            carpeta_destino = os.path.join(os.path.dirname(__file__), "imagenes_productos")
            os.makedirs(carpeta_destino, exist_ok=True)
            nombre_archivo = os.path.basename(ruta)
            destino = os.path.join(carpeta_destino, nombre_archivo)
            shutil.copy(ruta, destino)
            # Guarda la ruta relativa en el campo
            self.inputs["imagen"].setText(os.path.relpath(destino, os.path.dirname(__file__)))

    def tomar_foto(self):
        carpeta_destino = os.path.join(os.path.dirname(__file__), "imagenes_productos")
        os.makedirs(carpeta_destino, exist_ok=True)
        nombre_archivo = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        destino = os.path.join(carpeta_destino, nombre_archivo)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.warning(self, "Error", "No se pudo acceder a la cámara.")
            return
        QMessageBox.information(self, "Cámara", "Presiona 's' para tomar la foto y 'q' para cancelar.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Tomar Foto (presiona 's' para guardar, 'q' para cancelar)", frame)
            key = cv2.waitKey(1)
            if key == ord('s'):
                cv2.imwrite(destino, frame)
                self.inputs["imagen"].setText(os.path.relpath(destino, os.path.dirname(__file__)))
                break
            elif key == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

# Código principal
db_path = obtener_db_path()
print("Ruta de la base de datos:", db_path)
print("¿Existe la base de datos?", os.path.exists(db_path))
print("Argumentos recibidos:", sys.argv)

if __name__ == "__main__":
    producto_id = int(sys.argv[1])
    empleado_actual_id = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "None" else None
    app = QApplication(sys.argv)
    window = ModificarProductoWindow(producto_id, empleado_actual_id)
    window.show()
    sys.exit(app.exec_())