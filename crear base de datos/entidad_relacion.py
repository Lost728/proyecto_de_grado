import sys
import sqlite3
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem,
    QGraphicsTextItem, QFileDialog, QPushButton, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsItem
)
from PyQt5.QtGui import QPen, QBrush, QFont, QColor, QPainter, QPolygonF, QCursor
from PyQt5.QtCore import Qt, QPointF, pyqtSignal

class VistaZoomeable(QGraphicsView):
    """Vista personalizada con funcionalidad de zoom"""

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.factor_zoom = 1.0
        self.zoom_min = 0.3
        self.zoom_max = 3.0

    def wheelEvent(self, event):
        """Maneja el zoom con Ctrl + rueda del ratón"""
        if event.modifiers() == Qt.ControlModifier:
            # Factor de zoom
            factor = 1.2

            if event.angleDelta().y() > 0:
                # Zoom in
                if self.factor_zoom * factor <= self.zoom_max:
                    self.scale(factor, factor)
                    self.factor_zoom *= factor
            else:
                # Zoom out
                if self.factor_zoom / factor >= self.zoom_min:
                    self.scale(1/factor, 1/factor)
                    self.factor_zoom /= factor

            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        """Aumenta el zoom"""
        factor = 1.2
        if self.factor_zoom * factor <= self.zoom_max:
            self.scale(factor, factor)
            self.factor_zoom *= factor

    def zoom_out(self):
        """Disminuye el zoom"""
        factor = 1.2
        if self.factor_zoom / factor >= self.zoom_min:
            self.scale(1/factor, 1/factor)
            self.factor_zoom /= factor

    def reset_zoom(self):
        """Resetea el zoom al 100%"""
        self.resetTransform()
        self.factor_zoom = 1.0

class EntidadMovible(QGraphicsRectItem):
    """Entidad que puede ser movida por el usuario"""

    def __init__(self, nombre, columnas=None, x=0, y=0, ancho=200):
        self.nombre = nombre
        self.columnas = columnas if columnas else []
        self.ancho = ancho

        # Se inicializa el rectángulo con un tamaño provisional
        super().__init__(x, y, self.ancho, 100) # El tamaño se ajustará más tarde

        self.conexiones = []  # Lista de conexiones asociadas

        # Configuración visual
        self.setPen(QPen(QColor("#1976d2"), 3))
        self.setBrush(QBrush(QColor("#e3f2fd")))

        # Configuración de movimiento
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Crear elementos de texto y la línea separadora
        self.crear_textos()
        # Ajustar el tamaño final después de crear los textos
        self.ajustar_tamano()

        # Cursor al pasar el mouse
        self.setAcceptHoverEvents(True)

    def crear_textos(self):
        """Crea el título y las columnas de la tabla"""
        self.textos_columnas = []
        
        # Título de la tabla
        self.texto_titulo = QGraphicsTextItem(self.nombre, self)
        self.texto_titulo.setFont(QFont("Arial", 12, QFont.Bold))
        self.texto_titulo.setDefaultTextColor(Qt.black)
        
        # Textos de las columnas
        y_actual = 45 # Posición vertical inicial para las columnas
        for i, columna in enumerate(self.columnas):
            texto_columna = QGraphicsTextItem(columna, self)
            texto_columna.setFont(QFont("Arial", 10))
            texto_columna.setDefaultTextColor(QColor("#333"))
            texto_columna.setPos(10, y_actual) # Posición relativa a la entidad
            self.textos_columnas.append(texto_columna)
            y_actual += 25
            
    def ajustar_tamano(self):
        """Ajusta el ancho y alto del rectángulo para que quepan todos los textos"""
        max_ancho_texto = self.texto_titulo.boundingRect().width()
        for texto_columna in self.textos_columnas:
            max_ancho_texto = max(max_ancho_texto, texto_columna.boundingRect().width())
            
        # Nuevo ancho: max_ancho_texto + margen (20 para los 10px de cada lado)
        nuevo_ancho = max_ancho_texto + 20
        self.ancho = nuevo_ancho
        
        # Nueva altura: altura del título + línea + altura de todas las columnas
        altura_titulo = 40
        altura_columna = 25
        nuevo_alto = altura_titulo + len(self.columnas) * altura_columna + 10
        self.alto = nuevo_alto
        
        # Actualizar el rectángulo
        self.setRect(0, 0, self.ancho, self.alto)
        
        # Reposicionar el título y la línea separadora
        rect_titulo = self.texto_titulo.boundingRect()
        x_titulo = (self.ancho - rect_titulo.width()) / 2
        self.texto_titulo.setPos(x_titulo, 8)
        
        # Línea separadora después del título (ahora es un hijo del rectángulo)
        y_separador = 35
        # Remover la línea anterior si existe
        if hasattr(self, 'linea_separadora') and self.linea_separadora:
            self.scene().removeItem(self.linea_separadora)
        
        self.linea_separadora = QGraphicsLineItem(
            5, y_separador, 
            self.ancho - 5, y_separador,
            self # <-- Esto hace que sea un hijo de la EntidadMovible
        )
        self.linea_separadora.setPen(QPen(QColor("#1976d2"), 2))
        
        # Asegurar que todos los hijos no sean movibles independientemente
        self.texto_titulo.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.texto_titulo.setFlag(QGraphicsItem.ItemIsSelectable, False)
        for texto_columna in self.textos_columnas:
            texto_columna.setFlag(QGraphicsItem.ItemIsMovable, False)
            texto_columna.setFlag(QGraphicsItem.ItemIsSelectable, False)
            
    def hoverEnterEvent(self, event):
        """Cambia el cursor cuando el mouse entra"""
        self.setCursor(QCursor(Qt.OpenHandCursor))
        # Resaltar la entidad
        self.setPen(QPen(QColor("#0d47a1"), 4))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Restaura el cursor cuando el mouse sale"""
        self.setCursor(QCursor(Qt.ArrowCursor))
        # Restaurar apariencia normal
        self.setPen(QPen(QColor("#1976d2"), 3))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Cambia cursor al hacer clic"""
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Restaura cursor al soltar"""
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """Se ejecuta cuando la entidad se mueve"""
        if change == QGraphicsItem.ItemPositionChange:
            # Actualizar todas las conexiones asociadas
            for conexion in self.conexiones:
                conexion.actualizar_posicion()
        return super().itemChange(change, value)

    def agregar_conexion(self, conexion):
        """Añade una conexión a esta entidad"""
        if conexion not in self.conexiones:
            self.conexiones.append(conexion)

    def centro(self):
        """Retorna el centro de la entidad en coordenadas de escena"""
        # Calcular el centro en las coordenadas locales del ítem
        local_center = self.rect().center()
        # Mapear el centro local a coordenadas de la escena
        return self.mapToScene(local_center)


class ConexionDinamica:
    """Representa una conexión entre dos entidades que se actualiza automáticamente"""

    def __init__(self, scene, entidad_origen, entidad_destino):
        self.scene = scene
        self.entidad_origen = entidad_origen
        self.entidad_destino = entidad_destino

        # Elementos gráficos
        self.linea = None
        self.flecha = None

        # Configuración visual
        self.pen_linea = QPen(QColor("#1976d2"), 2)
        self.pen_linea.setCapStyle(Qt.RoundCap)

        self.pen_flecha = QPen(QColor("#1976d2"))
        self.brush_flecha = QBrush(QColor("#1976d2"))

        # Registrar esta conexión en ambas entidades
        entidad_origen.agregar_conexion(self)
        entidad_destino.agregar_conexion(self)

        # Crear elementos gráficos iniciales
        self.actualizar_posicion()

    def actualizar_posicion(self):
        """Actualiza la posición de la línea y flecha"""
        # Obtener centros de las entidades
        centro_origen = self.entidad_origen.centro()
        centro_destino = self.entidad_destino.centro()

        # Calcular puntos de conexión en los bordes
        punto_salida = self.punto_borde_rect(centro_origen, centro_destino, self.entidad_origen)
        punto_llegada = self.punto_borde_rect(centro_destino, centro_origen, self.entidad_destino)

        # Actualizar o crear línea
        if self.linea:
            self.scene.removeItem(self.linea)
        self.linea = self.scene.addLine(
            punto_salida.x(), punto_salida.y(),
            punto_llegada.x(), punto_llegada.y(),
            self.pen_linea
        )

        # Actualizar o crear flecha
        if self.flecha:
            self.scene.removeItem(self.flecha)
        self.flecha = self.dibujar_flecha(punto_salida, punto_llegada)

    def punto_borde_rect(self, centro, destino, entidad):
        """Calcula el punto en el borde del rectángulo más cercano al destino"""
        # Convert the entity's rectangle from item coordinates to scene coordinates
        entidad_rect_scene = entidad.mapToScene(entidad.rect()).boundingRect()

        dx = destino.x() - centro.x()
        dy = destino.y() - centro.y()

        if dx == 0 and dy == 0:
            return centro

        # Calcular intersección con el rectángulo delimitador en coordenadas de la escena
        ancho = entidad_rect_scene.width()
        alto = entidad_rect_scene.height()

        if abs(dx / ancho) > abs(dy / alto):
            # Intersección con lado izquierdo o derecho
            factor = (ancho / 2) / abs(dx)
            offset_x = (ancho / 2) * (1 if dx > 0 else -1)
            offset_y = dy * factor
        else:
            # Intersección con lado superior o inferior
            factor = (alto / 2) / abs(dy)
            offset_x = dx * factor
            offset_y = (alto / 2) * (1 if dy > 0 else -1)

        return QPointF(centro.x() + offset_x, centro.y() + offset_y)

    def dibujar_flecha(self, inicio, fin):
        """Dibuja una flecha al final de la línea"""
        angulo = math.atan2(fin.y() - inicio.y(), fin.x() - inicio.x())
        longitud = 16
        angulo_flecha = math.pi / 6

        punto1 = QPointF(
            fin.x() - longitud * math.cos(angulo - angulo_flecha),
            fin.y() - longitud * math.sin(angulo - angulo_flecha)
        )
        punto2 = QPointF(
            fin.x() - longitud * math.cos(angulo + angulo_flecha),
            fin.y() - longitud * math.sin(angulo + angulo_flecha)
        )

        flecha_poligono = QPolygonF([fin, punto1, punto2])
        return self.scene.addPolygon(flecha_poligono, self.pen_flecha, self.brush_flecha)

    def remover(self):
        """Remueve la conexión de la escena"""
        if self.linea:
            self.scene.removeItem(self.linea)
        if self.flecha:
            self.scene.removeItem(self.flecha)

class DiagramaER(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador de Diagrama ER - Interactivo")
        self.setGeometry(100, 100, 1200, 800)
        self.entidades = {}
        self.conexiones = []
        self.space_pressed = False  # Para controlar si la tecla espacio está presionada
        self.drag_pos = None  # Para arrastrar la ventana
        self.initUI()

    def initUI(self):
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Título mejorado
        titulo = QLabel("📊 Visualizador de Entidad-Relación Interactivo")
        titulo.setFont(QFont("Arial", 24, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: #1976d2; margin: 10px;")
        main_layout.addWidget(titulo)

        # Instrucciones mejoradas (añadida información sobre espacio + click)
        instrucciones = QLabel("💡 Arrastra las tablas para reorganizar | Ctrl + Rueda = Zoom | Botones + - = Zoom | Espacio + Click = Mover ventana")
        instrucciones.setFont(QFont("Arial", 11))
        instrucciones.setAlignment(Qt.AlignCenter)
        instrucciones.setStyleSheet("color: #666; font-style: italic; margin: 5px;")
        main_layout.addWidget(instrucciones)

        # Botones y estado
        controles_layout = QHBoxLayout()

        self.btn_cargar = QPushButton("📂 Cargar Base de Datos")
        self.btn_cargar.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_cargar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.btn_cargar.clicked.connect(self.cargar_base_datos)

        self.btn_reorganizar = QPushButton("🔄 Reorganizar Automáticamente")
        self.btn_reorganizar.setFont(QFont("Arial", 12))
        self.btn_reorganizar.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
            }
        """)
        self.btn_reorganizar.clicked.connect(self.reorganizar_automaticamente)
        self.btn_reorganizar.setEnabled(False)

        # Botones de zoom
        zoom_layout = QHBoxLayout()

        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.setFont(QFont("Arial", 14, QFont.Bold))
        self.btn_zoom_in.setFixedSize(50, 40)
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #ef6c00;
            }
        """)
        self.btn_zoom_in.clicked.connect(self.zoom_in)

        self.btn_zoom_out = QPushButton("🔍-")
        self.btn_zoom_out.setFont(QFont("Arial", 14, QFont.Bold))
        self.btn_zoom_out.setFixedSize(50, 40)
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #ef6c00;
            }
        """)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.btn_zoom_reset = QPushButton("100%")
        self.btn_zoom_reset.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_zoom_reset.setFixedSize(50, 40)
        self.btn_zoom_reset.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e24aa;
            }
            QPushButton:pressed {
                background-color: #7b1fa2;
            }
        """)
        self.btn_zoom_reset.clicked.connect(self.zoom_reset)

        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.btn_zoom_in)
        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_reset)

        self.lbl_estado = QLabel("⏳ No se ha cargado ninguna base de datos.")
        self.lbl_estado.setFont(QFont("Arial", 11))
        self.lbl_estado.setStyleSheet("color: #666; padding: 10px;")

        controles_layout.addWidget(self.btn_cargar)
        controles_layout.addWidget(self.btn_reorganizar)
        controles_layout.addLayout(zoom_layout)
        controles_layout.addStretch()
        controles_layout.addWidget(self.lbl_estado)
        main_layout.addLayout(controles_layout)

        # Área de diagrama mejorada
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor("#f8fffe"))
        self.scene.setSceneRect(-1000, -1000, 2000, 2000)

        self.view = VistaZoomeable(self.scene)
        self.view.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: white;
            }
        """)

        main_layout.addWidget(self.view)

        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def keyPressEvent(self, event):
        """Detecta cuando se presiona la tecla espacio"""
        if event.key() == Qt.Key_Space:
            self.space_pressed = True
            self.setCursor(Qt.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Detecta cuando se suelta la tecla espacio"""
        if event.key() == Qt.Key_Space:
            self.space_pressed = False
            self.setCursor(Qt.ArrowCursor)
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        """Inicia el arrastre de la ventana si se presiona espacio + click izquierdo"""
        if self.space_pressed and event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Mueve la ventana mientras se mantiene espacio + click izquierdo"""
        if self.space_pressed and self.drag_pos and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finaliza el arrastre de la ventana"""
        if event.button() == Qt.LeftButton and self.space_pressed:
            self.drag_pos = None
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def limpiar_diagrama(self):
        """Limpia completamente el diagrama"""
        for conexion in self.conexiones:
            conexion.remover()
        self.scene.clear()
        self.entidades = {}
        self.conexiones = []

    def cargar_base_datos(self):
        """Carga una base de datos SQLite y genera el diagrama"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecciona una base de datos SQLite",
            "",
            "SQLite DB (*.sqlite *.db *.sqlite3);;Todos los archivos (*)"
        )

        if not archivo:
            return

        self.limpiar_diagrama()

        try:
            conn = sqlite3.connect(archivo)
            cursor = conn.cursor()

            # Obtener tablas y sus columnas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tablas = [fila[0] for fila in cursor.fetchall()]

            if not tablas:
                self.lbl_estado.setText("❌ No se encontraron tablas en la base de datos.")
                return

            # Crear entidades con sus columnas
            posiciones = self.calcular_posiciones_circulares(len(tablas))

            for idx, tabla in enumerate(tablas):
                # Obtener información de las columnas
                cursor.execute(f"PRAGMA table_info('{tabla}')")
                info_columnas = cursor.fetchall()

                # Formatear información de columnas
                columnas = []
                for col_info in info_columnas:
                    nombre_col = col_info[1]
                    tipo_col = col_info[2]
                    es_pk = col_info[5] == 1
                    no_null = col_info[3] == 1

                    # Crear texto descriptivo para cada columna
                    texto_col = f"📋 {nombre_col}: {tipo_col}"
                    if es_pk:
                        texto_col = f"🔑 {nombre_col}: {tipo_col} (PK)"
                    elif no_null:
                        texto_col = f"📋 {nombre_col}: {tipo_col} (NOT NULL)"

                    columnas.append(texto_col)

                x, y = posiciones[idx]
                entidad = self.crear_entidad(tabla, columnas, x, y)
                self.entidades[tabla] = entidad

            # Crear conexiones basadas en claves foráneas
            for tabla in tablas:
                cursor.execute(f"PRAGMA foreign_key_list('{tabla}')")
                for fk in cursor.fetchall():
                    tabla_destino = fk[2]
                    if tabla_destino in self.entidades:
                        self.crear_conexion(tabla, tabla_destino)

            # Centrar la vista en el contenido
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

            nombre_archivo = archivo.split('/')[-1]
            self.lbl_estado.setText(f"✅ Base de datos cargada: {nombre_archivo} ({len(tablas)} tablas)")
            self.btn_reorganizar.setEnabled(True)

            conn.close()

        except Exception as e:
            self.lbl_estado.setText(f"❌ Error al cargar la base de datos: {str(e)}")

    def calcular_posiciones_circulares(self, n):
        """Calcula posiciones en círculo para las entidades"""
        if n == 1:
            return [(0, 0)]

        radio = max(300, 50 * n)
        posiciones = []

        for i in range(n):
            angulo = 2 * math.pi * i / n
            x = radio * math.cos(angulo)
            y = radio * math.sin(angulo)
            posiciones.append((x, y))

        return posiciones

    def crear_entidad(self, nombre, columnas, x, y):
        """Crea una entidad movible con sus columnas"""
        # La posición se ajusta automáticamente, no es necesario centrar aquí
        entidad = EntidadMovible(nombre, columnas, x, y)
        self.scene.addItem(entidad)
        return entidad

    def crear_conexion(self, tabla_origen, tabla_destino):
        """Crea una conexión dinámica entre dos tablas"""
        if tabla_origen in self.entidades and tabla_destino in self.entidades:
            entidad_origen = self.entidades[tabla_origen]
            entidad_destino = self.entidades[tabla_destino]

            conexion = ConexionDinamica(self.scene, entidad_origen, entidad_destino)
            self.conexiones.append(conexion)

    def reorganizar_automaticamente(self):
        """Reorganiza las entidades automáticamente en un círculo"""
        if not self.entidades:
            return

        tablas = list(self.entidades.keys())
        posiciones = self.calcular_posiciones_circulares(len(tablas))

        for idx, tabla in enumerate(tablas):
            entidad = self.entidades[tabla]
            x, y = posiciones[idx]
            entidad.setPos(x, y) # La entidad se centra a sí misma

        # Centrar la vista
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def zoom_in(self):
        """Método para aumentar zoom"""
        self.view.zoom_in()

    def zoom_out(self):
        """Método para disminuir zoom"""
        self.view.zoom_out()

    def zoom_reset(self):
        """Método para resetear zoom"""
        self.view.reset_zoom()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Mejor apariencia visual
    ventana = DiagramaER()
    ventana.showMaximized()
    sys.exit(app.exec_())