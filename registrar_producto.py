import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QDateEdit, QWidget, QComboBox, QFileDialog, QGraphicsBlurEffect
)
from PyQt5.QtCore import Qt, QDate
import sqlite3
from datetime import datetime
import subprocess
import cv2 

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
    def __init__(self, id_empleado=None):
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Producto")
        self.setGeometry(100, 100, 600, 400)

        # Fondo decorativo (image3.jpg)
        fondo = os.path.abspath(os.path.join(os.path.dirname(__file__), 'image3.jpg'))
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

        # Hoja de estilos adaptada a la paleta (púrpura / rosa / celeste)
        self.setStyleSheet("""
            QWidget { background: transparent; font-family: Arial; font-size: 13px; color: #ffffff; }
            QLabel { font-weight: bold; color: #ffffff; }
            QLineEdit, QDateEdit { padding: 8px; border-radius: 8px; background: rgba(0,0,0,0.35); color: #ffffff; }
            QComboBox { padding: 8px; border-radius: 8px; background: rgba(0,0,0,0.35); color: #ffffff; }
            QPushButton { padding: 8px 15px; border-radius: 10px; color: #22223b; font-weight: 700; }
            #title { font-size: 20px; font-weight: bold; color: #ffffff; padding: 12px; text-align: center; }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        title = QLabel("Registrar Nuevo Producto")
        title.setObjectName("title")
        main_layout.addWidget(title)

        # Usar una cuadrícula para el formulario (2 columnas)
        form_grid = QGridLayout()
        form_grid.setContentsMargins(30, 20, 30, 20)
        form_grid.setHorizontalSpacing(20)
        form_grid.setVerticalSpacing(12)

        # Campo para seleccionar el empleado que registra el producto
        self.combo_empleado = QComboBox()
        self.cargar_empleados()
        form_grid.addWidget(QLabel("Empleado que registra:"), 0, 0)
        form_grid.addWidget(self.combo_empleado, 0, 1)

        # Solo los campos requeridos - crear en filas (fila 1..n)
        row = 1
        self.campos = {}
        self.campos["nombre"] = self.crear_campo("Nombre del Producto:", QLineEdit(), form_grid, row); row += 1
        self.campos["codigo"] = self.crear_campo("Código:", QLineEdit(), form_grid, row); row += 1
        # imagen será un QLineEdit manejado aparte
        self.campos["imagen"] = QLineEdit()
        self.campos["imagen"].setStyleSheet("background: rgba(0,0,0,0.35); color:#fff; border-radius:8px; padding:6px;")
        form_grid.addWidget(QLabel("Imagen del Producto:"), row, 0)
        # contenedor para la caja de texto + botones
        imagen_container = QWidget()
        imagen_layout = QHBoxLayout()
        imagen_layout.setContentsMargins(0,0,0,0)
        imagen_layout.addWidget(self.campos["imagen"])
        btn_cargar_imagen = QPushButton("Cargar Imagen")
        btn_cargar_imagen.clicked.connect(self.cargar_imagen)
        imagen_layout.addWidget(btn_cargar_imagen)
        btn_camara = QPushButton("Tomar Foto")
        btn_camara.clicked.connect(self.tomar_foto)
        imagen_layout.addWidget(btn_camara)
        imagen_container.setLayout(imagen_layout)
        form_grid.addWidget(imagen_container, row, 1)
        row += 1

        self.campos["precio"] = self.crear_campo("Precio (Bs.):", QLineEdit(), form_grid, row); row += 1
        self.campos["fecha_vencimiento"] = self.crear_campo("Fecha de Vencimiento:", QDateEdit(), form_grid, row); row += 1
        self.campos["cajas"] = self.crear_campo("Cajas:", QLineEdit(), form_grid, row); row += 1
        self.campos["paquetes_por_caja"] = self.crear_campo("Paquetes por caja:", QLineEdit(), form_grid, row); row += 1
        self.campos["unidades_por_paquete"] = self.crear_campo("Unidades por paquete:", QLineEdit(), form_grid, row); row += 1
        self.campos["unidades"] = self.crear_campo("Unidades sueltas:", QLineEdit(), form_grid, row); row += 1

        self.campos["fecha_vencimiento"].setCalendarPopup(True)
        self.campos["fecha_vencimiento"].setDate(QDate.currentDate())
        self.campos["fecha_vencimiento"].setDisplayFormat("yyyy-MM-dd")

        # Validadores para campos numéricos
        self.campos["precio"].setValidator(self.crear_validador_numerico())
        self.campos["cajas"].setValidator(self.crear_validador_numerico(entero=True))
        self.campos["paquetes_por_caja"].setValidator(self.crear_validador_numerico(entero=True))
        self.campos["unidades_por_paquete"].setValidator(self.crear_validador_numerico(entero=True))
        self.campos["unidades"].setValidator(self.crear_validador_numerico(entero=True))

        self.campos["codigo"].setPlaceholderText("Ejemplo: 0001")

        # Agregar la cuadrícula dentro de un contenedor y al layout principal
        form_container = QWidget()
        form_container.setLayout(form_grid)
        main_layout.addWidget(form_container)

        # Botones al fondo
        buttons_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("guardar")
        btn_guardar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7ed6fa, stop:1 #ffb6e6); color:#22223b;")
        btn_guardar.clicked.connect(self.guardar_producto)
        buttons_layout.addWidget(btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("limpiar")
        btn_limpiar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ffa69e, stop:1 #ffb6e6); color:#22223b;")
        btn_limpiar.clicked.connect(self.limpiar_formulario)
        buttons_layout.addWidget(btn_limpiar)

        btn_volver = QPushButton("Volver")
        btn_volver.setObjectName("volver")
        btn_volver.setStyleSheet("background: rgba(255,255,255,0.12); color: #ffffff; border: 1px solid rgba(255,255,255,0.08);")
        btn_volver.clicked.connect(self.volver_a_lista)
        buttons_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setObjectName("menu")
        btn_menu.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8bd3ff, stop:1 #ffb6e6); color:#22223b; font-weight: bold; padding: 8px 15px; border-radius: 8px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        buttons_layout.addWidget(btn_menu)

        # Colocar los botones justo después del formulario y centrar
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        main_layout.addWidget(buttons_widget, alignment=Qt.AlignCenter)
        # Mantener un stretch abajo para empujar todo ligeramente hacia arriba
        main_layout.addStretch(1)

    def resizeEvent(self, event):
        # Escala el pixmap de fondo para cubrir la ventana si existe
        try:
            if hasattr(self, '_bg_pixmap') and self._bg_pixmap and hasattr(self, 'bg_label'):
                scaled = self._bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.bg_label.setPixmap(scaled)
                self.bg_label.resize(self.size())
                self.bg_label.lower()
        except Exception:
            pass
        return super().resizeEvent(event)

    def cargar_empleados(self):
        """Carga los empleados en el combo desde la tabla empleado, mostrando solo nombre e ID."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id_empleado, nombre, rol FROM empleado")
        empleados = cursor.fetchall()
        self.combo_empleado.clear()
        for id_empleado, nombre, rol in empleados:
            self.combo_empleado.addItem(f"{nombre} - ID: {id_empleado} - Rol: {rol}", id_empleado)
        conn.close()

    def crear_campo(self, label_text, widget, layout, row=None):
        """Crea un par etiqueta+widget. Si se pasa un QGridLayout y row, lo coloca en (row, 0/1).
        Si no, lo coloca usando addWidget secuencialmente (para compatibilidad).
        """
        label = QLabel(label_text)
        from PyQt5.QtWidgets import QGridLayout, QDateEdit
        # Estilizar inputs basicos
        try:
            if isinstance(widget, (QLineEdit, QDateEdit)):
                widget.setStyleSheet("background: rgba(0,0,0,0.35); color:#fff; border-radius:8px; padding:6px;")
        except Exception:
            pass

        if isinstance(layout, QGridLayout) and row is not None:
            layout.addWidget(label, row, 0)
            layout.addWidget(widget, row, 1)
        else:
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
            "fecha_vencimiento": self.campos["fecha_vencimiento"].date().toPyDate(),
            "cajas": self.campos["cajas"].text().strip(),
            "paquetes_por_caja": self.campos["paquetes_por_caja"].text().strip(),
            "unidades_por_paquete": self.campos["unidades_por_paquete"].text().strip(),
            "unidades": self.campos["unidades"].text().strip()
        }

        # Validar campos obligatorios (imagen ahora es opcional)
        if not datos["nombre"] or not datos["codigo"] or not datos["precio"]:
            QMessageBox.warning(self, "Advertencia", "Nombre, código y precio son obligatorios.")
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

            fecha_venc_timestamp = int(datetime.combine(datos["fecha_vencimiento"], datetime.min.time()).timestamp())

            imagen_valor = datos["imagen"] if datos["imagen"] else ""

            # Obtener el id_empleado seleccionado
            id_empleado = self.combo_empleado.currentData()

            # Inserta el producto en la tabla productos
            cursor.execute("""
                INSERT INTO productos (
                    codigo, imagen, nombre, precio, fecha_venc, id_empleado,
                    cajas, paquetes, unidades, unidades_por_paquete, paquetes_por_caja
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos["codigo"],
                imagen_valor,
                datos["nombre"],
                float(datos["precio"]),
                fecha_venc_timestamp,
                id_empleado,
                int(datos["cajas"]) if datos["cajas"] else 0,
                0,  # paquetes
                int(datos["unidades"]) if datos["unidades"] else 0,
                int(datos["unidades_por_paquete"]) if datos["unidades_por_paquete"] else 0,
                int(datos["paquetes_por_caja"]) if datos["paquetes_por_caja"] else 0
            ))

            conn.commit()

            cursor.execute("SELECT nombre FROM empleado WHERE id_empleado = ?", (id_empleado,))
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
            QMessageBox.warning(self, "Error de formato", "Verifique los valores numéricos.")

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

    def actualizar_label_empleado(self):
        """Muestra el nombre del empleado que está registrando el producto."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM empleado WHERE id_empleado = ?", (self.id_empleado,))
            nombre_admin = cursor.fetchone()
            if nombre_admin:
                self.label_empleado.setText(f"Registrando como: {nombre_admin[0]}")
            else:
                self.label_empleado.setText(f"Registrando como: Empleado ID {self.id_empleado}")
            conn.close()
        except Exception:
            self.label_empleado.setText(f"Registrando como: Empleado ID {self.id_empleado}")

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
    app = QApplication(sys.argv)
    # Define aquí el id_empleado_actual (por ejemplo, 1 para pruebas)
    id_empleado_actual = 1  # Cambia este valor según corresponda
    window = InsertarProductoWindow(id_empleado_actual)
    window.showMaximized()
    sys.exit(app.exec_())