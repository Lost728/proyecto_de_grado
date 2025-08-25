import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QDateEdit, QWidget, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
import sqlite3
from datetime import datetime
import subprocess
import cv2  # <--- Asegúrate de tener instalado opencv-python

# ----------------- INICIO DE MODIFICACIONES -----------------

def obtener_db_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # CORRECCIÓN: Usar la base de datos pruebas.db
        db_path = os.path.join(exe_dir, "pruebas.db")
        if os.path.exists(db_path):
            return db_path
        base_path = sys._MEIPASS
        return os.path.join(base_path, "pruebas.db")
    else:
        # CORRECCIÓN: Usar la base de datos pruebas.db
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "pruebas.db"))

db_path = obtener_db_path()

def verificar_tablas():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        print("Tablas existentes:")
        for tabla in tablas:
            print(f"- {tabla[0]}")
            
    except sqlite3.Error as e:
        print(f"Error al verificar tablas: {e}")
    finally:
        if conn:
            conn.close()

def mostrar_columnas():
    # CORRECCIÓN: Usar la tabla 'productos'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(productos)")
    print("Columnas de la tabla productos:")
    for col in cursor.fetchall():
        print(col)
    conn.close()

class InsertarProductoWindow(QMainWindow):
    def __init__(self, id_empleado):
        super().__init__()
        self.id_empleado = id_empleado
        self.setWindowTitle("Insertar Nuevo Producto")
        self.setGeometry(100, 100, 600, 500)
        
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
            QLineEdit, QDateEdit {
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
            #title {
                font-size: 18px;
                font-weight: bold;
                background-color: #e0e0e0;
                padding: 10px;
                text-align: center;
            }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        title = QLabel("Insertar Nuevo Producto")
        title.setObjectName("title")
        main_layout.addWidget(title)

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(30, 20, 30, 20)

        # Campos del formulario (ajustados a la tabla 'productos')
        self.campos = {
            "nombre": self.crear_campo("Nombre del Producto:", QLineEdit(), form_layout),
            "codigo": self.crear_campo("Código:", QLineEdit(), form_layout),
            "imagen": QLineEdit(),
            "precio": self.crear_campo("Precio (Bs.):", QLineEdit(), form_layout),
            "stock": self.crear_campo("Stock:", QLineEdit(), form_layout), # Cambiado de 'cantidad' a 'stock'
            "fecha_vencimiento": self.crear_campo("Fecha de Vencimiento:", QDateEdit(), form_layout)
        }

        # Configurar el QDateEdit
        self.campos["fecha_vencimiento"].setCalendarPopup(True)
        self.campos["fecha_vencimiento"].setDate(QDate.currentDate())
        self.campos["fecha_vencimiento"].setDisplayFormat("yyyy-MM-dd")

        # Validadores para campos numéricos
        self.campos["precio"].setValidator(self.crear_validador_numerico())
        self.campos["stock"].setValidator(self.crear_validador_numerico(entero=True))

        buttons_layout = QHBoxLayout()
        
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_guardar.clicked.connect(self.guardar_producto)
        buttons_layout.addWidget(btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setStyleSheet("background-color: #f39c12; color: white;")
        btn_limpiar.clicked.connect(self.limpiar_formulario)
        buttons_layout.addWidget(btn_limpiar)

        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #95a5a6; color: white;")
        btn_volver.clicked.connect(self.volver_a_lista)
        buttons_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; padding: 8px 15px; border-radius: 5px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        buttons_layout.addWidget(btn_menu)

        form_layout.addLayout(buttons_layout)
        main_layout.addLayout(form_layout)

        self.campos["codigo"].setPlaceholderText("Ejemplo: 0001")

        # Guardar el id_empleado para usarlo al guardar el producto
        self.id_empleado = id_empleado

        # Reemplaza la línea de imagen por este bloque:
        imagen_layout = QHBoxLayout()
        imagen_layout.addWidget(self.campos["imagen"])
        btn_cargar_imagen = QPushButton("Cargar Imagen")
        btn_cargar_imagen.clicked.connect(self.cargar_imagen)
        imagen_layout.addWidget(btn_cargar_imagen)
        btn_camara = QPushButton("Tomar Foto")
        btn_camara.clicked.connect(self.tomar_foto)
        imagen_layout.addWidget(btn_camara)
        form_layout.addWidget(QLabel("Imagen del Producto:"))
        form_layout.addLayout(imagen_layout)

    def crear_campo(self, label_text, widget, layout):
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        return widget

    def crear_validador_numerico(self, entero=False):
        from PyQt5.QtGui import QDoubleValidator, QIntValidator
        
        if entero:
            validator = QIntValidator()
            validator.setBottom(0)
        else:
            validator = QDoubleValidator()
            validator.setBottom(0)
            validator.setDecimals(2)
            
        return validator

    def guardar_producto(self):
        # Obtener datos del formulario
        datos = {
            "nombre": self.campos["nombre"].text().strip(),
            "codigo": self.campos["codigo"].text().strip(),
            "imagen": self.campos["imagen"].text().strip(),
            "precio": self.campos["precio"].text().strip(),
            "stock": self.campos["stock"].text().strip(),
            "fecha_vencimiento": self.campos["fecha_vencimiento"].date().toPyDate()
        }

        # Validar campos obligatorios
        if not datos["nombre"] or not datos["codigo"] or not datos["imagen"] or not datos["precio"] or not datos["stock"]:
            QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios.")
            return
        
        # Validar formato de código (ejemplo)
        if len(datos["codigo"]) < 4 or not datos["codigo"].isdigit():
            QMessageBox.warning(self, "Advertencia", "El código debe tener al menos 4 dígitos numéricos (ejemplo: 0001).")
            return

        # Validar fecha de vencimiento
        hoy = datetime.now().date()
        if datos["fecha_vencimiento"] < hoy:
            QMessageBox.warning(self, "Advertencia", "La fecha de vencimiento no puede ser anterior a hoy.")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Verificar si el código ya existe
            cursor.execute("SELECT COUNT(*) FROM productos WHERE codigo = ?", (datos["codigo"],))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Advertencia", "El código ya existe. Ingrese uno diferente.")
                conn.close()
                return

            # Convertir la fecha a timestamp INTEGER
            fecha_venc_timestamp = int(datetime.combine(datos["fecha_vencimiento"], datetime.min.time()).timestamp())
            
            # Insertar el producto con los campos correctos de la tabla
            cursor.execute("""
                INSERT INTO productos (
                    codigo, imagen, nombre, precio, stock, fecha_venc, id_empleado
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datos["codigo"],
                datos["imagen"],
                datos["nombre"],
                float(datos["precio"]),
                int(datos["stock"]),
                fecha_venc_timestamp,
                self.id_empleado  # <--- Aquí se registra el id del administrador
            ))

            conn.commit()

            cursor.execute("SELECT nombre FROM empleado WHERE id_empleado = ?", (self.id_empleado,))
            nombre_admin = cursor.fetchone()
            if nombre_admin:
                QMessageBox.information(self, "Éxito", f"Producto guardado correctamente\nRegistrado por: {nombre_admin[0]}")
            else:
                QMessageBox.information(self, "Éxito", "Producto guardado correctamente\nRegistrado por: (desconocido)")

            self.limpiar_formulario()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Advertencia", "Error de integridad. El código podría ya existir.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el producto: {e}")
        except ValueError:
            QMessageBox.warning(self, "Error de formato", "Verifique los valores numéricos (precio, stock)")

    def limpiar_formulario(self):
        for campo in self.campos.values():
            if isinstance(campo, QLineEdit):
                campo.clear()
            elif isinstance(campo, QDateEdit):
                campo.setDate(QDate.currentDate())
        self.campos["nombre"].setFocus()

    def volver_a_lista(self):
        abrir_aplicacion("ver_productos.py")
        self.close()

    def cargar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if ruta:
            # Copia la imagen a la carpeta local de imágenes
            carpeta_destino = os.path.join(os.path.dirname(__file__), "imagenes_productos")
            os.makedirs(carpeta_destino, exist_ok=True)
            nombre_archivo = os.path.basename(ruta)
            destino = os.path.join(carpeta_destino, nombre_archivo)
            shutil.copy(ruta, destino)
            # Guarda la ruta relativa en el campo
            self.campos["imagen"].setText(os.path.relpath(destino, os.path.dirname(__file__)))

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
                self.campos["imagen"].setText(os.path.relpath(destino, os.path.dirname(__file__)))
                break
            elif key == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def ir_menu_principal(self):
        """Ir a menu.py"""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "menu.py")
            if not os.path.exists(script_path):
                QMessageBox.critical(self, "Error", f"No se encontró el archivo: {script_path}")
                return
            self.close()
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir menu.py: {e}")

def abrir_aplicacion(nombre_py, argumentos=None):
    """
    Abre un archivo .py o .exe, usando ruta absoluta o relativa.
    Si es .py, lo ejecuta con el intérprete de Python.
    Permite pasar argumentos.
    """
    # Si es ruta absoluta y existe, úsala directamente
    if os.path.isabs(nombre_py) and os.path.exists(nombre_py):
        if nombre_py.endswith('.py'):
            cmd = [sys.executable, nombre_py]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return
        elif nombre_py.endswith('.exe'):
            cmd = [nombre_py]
            if argumentos:
                cmd += argumentos
            subprocess.Popen(cmd)
            return

    # Si es solo nombre, busca en cwd y en _MEIPASS y en la carpeta del script actual
    base_paths = [os.getcwd(), os.path.dirname(__file__)]
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
                        f"No se encontró el archivo:\n{nombre_py}")

if __name__ == "__main__":
    verificar_tablas() # Para verificar que la tabla 'productos' existe
    mostrar_columnas() # Para ver las columnas de la tabla 'productos'
    app = QApplication(sys.argv)
    # Define aquí el id_empleado_actual (por ejemplo, 1 para pruebas)
    id_empleado_actual = 1  # Cambia este valor según corresponda
    window = InsertarProductoWindow(id_empleado_actual)
    window.show()
    sys.exit(app.exec_())