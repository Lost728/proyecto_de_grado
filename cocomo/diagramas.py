import sys
import math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

class FlowchartNode(QGraphicsItem):
    """Clase que representa un nodo en el diagrama de flujo."""
    
    def __init__(self, text="Nodo", node_type="rectangle"):
        super().__init__()
        self.text = text
        self.node_type = node_type
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        self.connections = []
        self.input_connections = []
        
        self.width = 140
        self.height = 50
        
        if self.node_type == "diamond":
            self.width = 120
            self.height = 60
        
    def boundingRect(self):
        if self.node_type == "diamond":
            return QRectF(-self.width/2 - 10, -self.height/2 - 10, self.width + 20, self.height + 20)
        else:
            return QRectF(-self.width/2 - 10, -self.height/2 - 10, self.width + 20, self.height + 20)
    
    def paint(self, painter, option, widget):
        pen = QPen(QColor(80, 80, 80), 2)
        if self.isSelected():
            pen = QPen(QColor(255, 100, 100), 3)
            
        brush = QBrush()
        if self.node_type == "diamond":
            brush.setColor(QColor(255, 255, 200))
        elif self.node_type == "rounded_rect":
            brush.setColor(QColor(200, 255, 200))
        else:
            brush.setColor(QColor(200, 220, 255))
        
        brush.setStyle(Qt.SolidPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if self.node_type == "diamond":
            points = [
                QPointF(0, -self.height/2), QPointF(self.width/2, 0),
                QPointF(0, self.height/2), QPointF(-self.width/2, 0)
            ]
            polygon = QPolygonF(points)
            painter.drawPolygon(polygon)
        elif self.node_type == "rounded_rect":
            rect = QRectF(-self.width/2, -self.height/2, self.width, self.height)
            painter.drawRoundedRect(rect, 15, 15)
        else:
            rect = QRectF(-self.width/2, -self.height/2, self.width, self.height)
            painter.drawRect(rect)
        
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for point in self._getConnectionPoints():
                painter.drawEllipse(point, 4, 4)

        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        text_rect = QRectF(-self.width/2, -self.height/2, self.width, self.height)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)
        
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._editText()
        else:
            super().keyPressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self._editText()
    
    def _editText(self):
        text, ok = QInputDialog.getText(None, 'Editar Texto del Nodo', 'Nuevo texto:', text=self.text)
        if ok and text.strip():
            self.text = text.strip()
            self.update()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for connection in self.connections + self.input_connections:
                connection.updatePath()
        return super().itemChange(change, value)
    
    def addConnection(self, connection, is_input=False):
        if is_input:
            if connection not in self.input_connections:
                self.input_connections.append(connection)
        else:
            if connection not in self.connections:
                self.connections.append(connection)
            
    def removeConnection(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)
        if connection in self.input_connections:
            self.input_connections.remove(connection)

    def _getConnectionPoints(self):
        if self.node_type == "diamond":
            return [
                QPointF(0, -self.height/2), QPointF(self.width/2, 0),
                QPointF(0, self.height/2), QPointF(-self.width/2, 0)
            ]
        else:
            return [
                QPointF(0, -self.height/2), QPointF(self.width/2, 0),
                QPointF(0, self.height/2), QPointF(-self.width/2, 0)
            ]
    
    def getOptimalConnectionPoint(self, target_pos, connection=None):
        """Calcula el punto de conexión óptimo en el borde del nodo, con desfase si hay varias conexiones."""
        node_center = self.scenePos()
        dx = target_pos.x() - node_center.x()
        dy = target_pos.y() - node_center.y()

        # Desfase para conexiones múltiples
        offset = 0
        if connection and hasattr(self, "input_connections"):
            # Solo para conexiones entrantes
            if connection in self.input_connections:
                idx = self.input_connections.index(connection)
                total = len(self.input_connections)
                if total > 1:
                    # Desfase de hasta +/-15 px según el número de conexiones
                    offset = (idx - (total - 1) / 2) * 18  # antes era 15

        if self.node_type == "diamond":
            angle = math.atan2(dy, dx)
            tan_theta = abs(dy / dx) if dx != 0 else float('inf')
            if tan_theta < self.height / self.width:
                if dx > 0:
                    point = node_center + QPointF(self.width/2, 0)
                else:
                    point = node_center + QPointF(-self.width/2, 0)
            else:
                if dy > 0:
                    point = node_center + QPointF(0, self.height/2)
                else:
                    point = node_center + QPointF(0, -self.height/2)
        else:
            if abs(dx) * self.height > abs(dy) * self.width:
                point = QPointF(self.width / 2 if dx > 0 else -self.width / 2, 0)
            else:
                point = QPointF(0, self.height / 2 if dy > 0 else -self.height / 2)
            point = node_center + point

        # Aplica el desfase perpendicular a la dirección de la flecha
        if offset != 0:
            angle = math.atan2(dy, dx)
            perp_angle = angle + math.pi / 2
            point += QPointF(math.cos(perp_angle) * offset, math.sin(perp_angle) * offset)

        return point

class ConnectionLabel(QGraphicsItem):
    """Clase para la etiqueta de una conexión."""
    def __init__(self, text="", connection=None):
        super().__init__()
        self.text = text
        self.connection = connection
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.offset = QPointF(0, -15)
        
    def boundingRect(self):
        if not self.text:
            return QRectF()
        font_metrics = QFontMetrics(QFont("Arial", 9))
        text_width = font_metrics.width(self.text)
        text_height = font_metrics.height()
        return QRectF(-text_width/2 - 8, -text_height/2 - 4, text_width + 16, text_height + 8)
    
    def paint(self, painter, option, widget):
        if not self.text:
            return
            
        pen = QPen(QColor(0, 0, 0), 1)
        brush = QBrush(QColor(255, 255, 255, 220))
        if self.isSelected():
            pen = QPen(QColor(255, 0, 0), 2)
            brush = QBrush(QColor(255, 255, 200))
        
        rect = self.boundingRect().adjusted(2, 2, -2, -2)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRoundedRect(rect, 5, 5)
        
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text)
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._editText()
        else:
            super().keyPressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self._editText()
    
    def _editText(self):
        text, ok = QInputDialog.getText(None, 'Editar Etiqueta', 'Nueva etiqueta:', text=self.text)
        if ok:
            self.text = text.strip()
            self.prepareGeometryChange()
            self.update()

class Connection(QGraphicsItem):
    """Clase para la conexión (flecha) entre dos nodos."""
    
    def __init__(self, start_node, end_node, label=""):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        start_node.addConnection(self)
        end_node.addConnection(self, is_input=True)
        
        self.label_item = None
        self.createLabel(label)
            
    def createLabel(self, text):
        if self.label_item and self.scene():
            self.scene().removeItem(self.label_item)
            
        if text.strip():
            self.label_item = ConnectionLabel(text, self)
            if self.scene():
                self.scene().addItem(self.label_item)
            self.updateLabelPosition()
    
    def updateLabelPosition(self):
        if not self.label_item or not self.start_node or not self.end_node:
            return
            
        start_pos = self.start_node.pos()
        end_pos = self.end_node.pos()
        mid_point = (start_pos + end_pos) / 2
        
        self.label_item.setPos(mid_point + self.label_item.offset)
        
    def boundingRect(self):
        if not self.start_node or not self.end_node:
            return QRectF()
        
        start_pos = self.start_node.pos()
        end_pos = self.end_node.pos()
        
        rect = QRectF(start_pos, end_pos).normalized()
        return rect.adjusted(-20, -20, 20, 20)
    
    def paint(self, painter, option, widget):
        if not self.start_node or not self.end_node:
            return
        
        start_point = self.start_node.getOptimalConnectionPoint(self.end_node.scenePos(), self)
        end_point = self.end_node.getOptimalConnectionPoint(self.start_node.scenePos(), self)
        
        pen = QPen(QColor(50, 50, 50), 2)
        if self.isSelected():
            pen = QPen(QColor(255, 100, 100), 3)
        painter.setPen(pen)
        
        line = QLineF(start_point, end_point)
        painter.drawLine(line)
        self._drawArrow(painter, start_point, end_point)
    
    def _drawArrow(self, painter, start_point, end_point):
        angle = math.atan2(end_point.y() - start_point.y(), end_point.x() - start_point.x())
        
        arrow_length = 15
        arrow_degrees = math.pi / 6
        
        arrowHead1 = QPointF(
            end_point.x() - arrow_length * math.cos(angle - arrow_degrees),
            end_point.y() - arrow_length * math.sin(angle - arrow_degrees)
        )
        arrowHead2 = QPointF(
            end_point.x() - arrow_length * math.cos(angle + arrow_degrees),
            end_point.y() - arrow_length * math.sin(angle + arrow_degrees)
        )
        
        arrowHeadPolygon = QPolygonF([end_point, arrowHead1, arrowHead2])
        painter.setBrush(QBrush(painter.pen().color()))
        painter.drawPolygon(arrowHeadPolygon)
    
    def updatePath(self):
        self.prepareGeometryChange()
        self.updateLabelPosition()
        
    def destroy(self):
        self.start_node.removeConnection(self)
        self.end_node.removeConnection(self)
        if self.label_item:
            self.scene().removeItem(self.label_item)

class FlowchartScene(QGraphicsScene):
    """Clase para la escena del editor, maneja la interacción con los elementos."""
    
    sigConnectionStarted = pyqtSignal()
    sigConnectionCancelled = pyqtSignal()
    sigConnectionCompleted = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connecting_mode = False
        self.start_node = None
        self.connection_label = ""
        
    def mousePressEvent(self, event):
        if self.connecting_mode and event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, FlowchartNode):
                if self.start_node is None:
                    # Inicia la conexión
                    self.start_node = item
                    self.start_node.setSelected(True)
                    self.sigConnectionStarted.emit()
                elif item != self.start_node:
                    # Completa la conexión
                    connection = Connection(self.start_node, item, self.connection_label)
                    self.addItem(connection)
                    # Permite seguir conectando desde el mismo nodo origen
                    self.start_node.setSelected(False)
                    self.start_node = None
                    self.sigConnectionCompleted.emit()
            else:
                # Clic en el área de dibujo, cancela la conexión
                self.resetConnectionMode()
                self.sigConnectionCancelled.emit()
        else:
            super().mousePressEvent(event)

    def resetConnectionMode(self):
        """Reinicia completamente el estado del modo de conexión."""
        if self.start_node:
            self.start_node.setSelected(False)
            self.start_node = None
        self.connecting_mode = False
        self.connection_label = ""
            
    def setConnectMode(self, enabled, label=""):
        self.connecting_mode = enabled
        self.connection_label = label
        if not enabled:
            self.resetConnectionMode()
            
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        # Fondo cuadriculado
        grid_size = 30
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        lines = []
        for x in range(left, int(rect.right()), grid_size):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), grid_size):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        painter.drawLines(lines)
        
class FlowchartView(QGraphicsView):
    """Clase para la vista del editor, maneja el zoom y el arrastre."""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.current_temp_line = None

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor)
        else:
            super().wheelEvent(event)

class FlowchartEditor(QMainWindow):
    """Ventana principal del editor de diagramas de flujo."""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.createExampleDiagram()
        
    def initUI(self):
        self.setWindowTitle('Editor de Diagramas de Flujo - Profesional')
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        self.createToolsPanel(main_layout)
        
        self.scene = FlowchartScene(self)
        self.scene.sigConnectionStarted.connect(self.onConnectionStarted)
        self.scene.sigConnectionCancelled.connect(self.onConnectionCancelled)
        self.scene.sigConnectionCompleted.connect(self.onConnectionCompleted)
        
        self.view = FlowchartView(self.scene)
        self.view.setMinimumSize(800, 600)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        
        main_layout.addWidget(self.view)
        
        self.createMenus()
        self.statusBar().showMessage('Listo - Presiona Enter o doble clic para editar, usa Ctrl+Rueda para hacer zoom.')
        
    def createToolsPanel(self, main_layout):
        tools_panel = QVBoxLayout()
        tools_widget = QWidget()
        tools_widget.setLayout(tools_panel)
        tools_widget.setMaximumWidth(220)
        tools_widget.setMinimumWidth(200)
        tools_widget.setStyleSheet("""
            QWidget { background-color: #f0f0f0; }
            QPushButton { padding: 8px; margin: 2px; font-weight: bold; border-radius: 5px; background-color: #e0e0e0; }
            QPushButton:hover { background-color: #d0d0d0; }
            QPushButton:pressed { background-color: #c0c0c0; }
            QLabel { font-weight: bold; color: #333; margin-top: 10px; }
            #title_label { font-size: 14px; padding: 10px; background-color: #333; color: white; }
            #info_label { background-color: #e8f4fd; padding: 10px; border-radius: 5px; font-size: 10px; }
        """)
        
        title_label = QLabel("🔧 HERRAMIENTAS")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        tools_panel.addWidget(title_label)
        
        tools_panel.addWidget(QLabel("📦 Tipos de Nodo:"))
        
        self.btn_process = QPushButton("🔄 Proceso")
        self.btn_process.clicked.connect(lambda: self.addNode("rectangle"))
        tools_panel.addWidget(self.btn_process)
        
        self.btn_decision = QPushButton("❓ Decisión")
        self.btn_decision.clicked.connect(lambda: self.addNode("diamond"))
        tools_panel.addWidget(self.btn_decision)
        
        self.btn_start_end = QPushButton("🎯 Inicio/Fin")
        self.btn_start_end.clicked.connect(lambda: self.addNode("rounded_rect"))
        tools_panel.addWidget(self.btn_start_end)
        
        tools_panel.addWidget(QLabel("🔗 Conexiones:"))
        
        self.btn_connect = QPushButton("🔗 Conectar Nodos")
        self.btn_connect.clicked.connect(self.toggleConnectMode)
        tools_panel.addWidget(self.btn_connect)
        
        self.connection_label_input = QLineEdit()
        self.connection_label_input.setPlaceholderText("Etiqueta (Ej: Sí, No)")
        self.connection_label_input.setToolTip("Texto para la conexión")
        tools_panel.addWidget(self.connection_label_input)
        
        tools_panel.addWidget(QLabel("🛠️ Edición:"))
        
        btn_delete = QPushButton("🗑️ Eliminar")
        btn_delete.clicked.connect(self.deleteSelected)
        tools_panel.addWidget(btn_delete)
        
        btn_clear = QPushButton("🧹 Limpiar Todo")
        btn_clear.clicked.connect(self.clearAll)
        tools_panel.addWidget(btn_clear)
        
        tools_panel.addWidget(QLabel("💾 Exportar:"))
        
        btn_export_png = QPushButton("🖼️ PNG")
        btn_export_png.clicked.connect(self.exportAsPNG)
        tools_panel.addWidget(btn_export_png)
        
        btn_export_pdf = QPushButton("📄 PDF")
        btn_export_pdf.clicked.connect(self.exportAsPDF)
        tools_panel.addWidget(btn_export_pdf)
        
        btn_print = QPushButton("🖨️ Imprimir")
        btn_print.clicked.connect(self.printDiagram)
        tools_panel.addWidget(btn_print)
        
        info_label = QLabel("💡 AYUDA:\n• Del: Eliminar\n• Enter: Editar texto\n• Doble clic: Editar\n• Ctrl+Rueda: Zoom")
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        tools_panel.addWidget(info_label)
        
        tools_panel.addStretch()
        main_layout.addWidget(tools_widget)
        
    def createMenus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Archivo')
        edit_menu = menubar.addMenu('Editar')
        insert_menu = menubar.addMenu('Insertar')
        
        file_menu.addAction(QAction('Nuevo', self, shortcut='Ctrl+N', triggered=self.clearAll))
        file_menu.addSeparator()
        file_menu.addAction(QAction('Guardar como PDF', self, shortcut='Ctrl+S', triggered=self.exportAsPDF))  # <--- Cambiado aquí
        file_menu.addAction(QAction('Exportar como PNG', self, shortcut='Ctrl+Shift+P', triggered=self.exportAsPNG))
        file_menu.addAction(QAction('Exportar como PDF', self, shortcut='Ctrl+Shift+D', triggered=self.exportAsPDF))
        file_menu.addSeparator()
        file_menu.addAction(QAction('Imprimir', self, shortcut='Ctrl+P', triggered=self.printDiagram))

        edit_menu.addAction(QAction('Eliminar', self, shortcut='Del', triggered=self.deleteSelected))
        
        insert_menu.addAction(QAction('Proceso', self, shortcut='Ctrl+1', triggered=lambda: self.addNode("rectangle")))
        insert_menu.addAction(QAction('Decisión', self, shortcut='Ctrl+2', triggered=lambda: self.addNode("diamond")))
        insert_menu.addAction(QAction('Inicio/Fin', self, shortcut='Ctrl+3', triggered=lambda: self.addNode("rounded_rect")))

    def onConnectionStarted(self):
        self.btn_connect.setText("❌ Cancelar")
        self.btn_connect.setStyleSheet("background-color: #ff9999; color: white;")
        self.statusBar().showMessage("Modo conexión: Click en nodo destino o en el área de dibujo para cancelar.")

    def onConnectionCancelled(self):
        self.btn_connect.setText("🔗 Conectar Nodos")
        self.btn_connect.setStyleSheet("")
        self.connection_label_input.clear()
        self.statusBar().showMessage("Modo conexión cancelado", 2000)

    def onConnectionCompleted(self):
        self.btn_connect.setText("❌ Cancelar")
        self.btn_connect.setStyleSheet("background-color: #ff9999; color: white;")
        label = self.connection_label_input.text()  # NO limpiar el campo
        # Mantener el modo conexión activo para conectar más nodos
        self.scene.setConnectMode(True, label)
        self.statusBar().showMessage("Conexión creada exitosamente. Haz clic en el siguiente nodo destino o en el área de dibujo para cancelar.", 4000)

    def addNode(self, node_type):
        text = {"rectangle": "Nuevo Proceso", "diamond": "¿Nueva Decisión?", "rounded_rect": "Inicio/Fin"}.get(node_type, "Nodo")
        node = FlowchartNode(text, node_type)
        center = self.view.mapToScene(self.view.rect().center())
        node.setPos(center)
        self.scene.addItem(node)
        node.setSelected(True)
        self.statusBar().showMessage(f"Nodo '{text}' agregado", 3000)
        
    def toggleConnectMode(self):
        is_active = not self.scene.connecting_mode
        label = self.connection_label_input.text()
        
        if not is_active:
            self.scene.setConnectMode(False)
            self.onConnectionCancelled()
        else:
            self.scene.setConnectMode(True, label)
            self.onConnectionStarted()
        
    def deleteSelected(self):
        selected_items = list(self.scene.selectedItems())
        if not selected_items:
            self.statusBar().showMessage("No hay elementos seleccionados para eliminar", 2000)
            return
            
        for item in selected_items:
            if isinstance(item, FlowchartNode):
                all_connections = item.connections[:] + item.input_connections[:]
                for connection in all_connections:
                    self.scene.removeItem(connection)
                    if connection.label_item:
                        self.scene.removeItem(connection.label_item)
            elif isinstance(item, Connection):
                item.start_node.removeConnection(item)
                item.end_node.removeConnection(item)
                if item.label_item:
                    self.scene.removeItem(item.label_item)
            elif isinstance(item, ConnectionLabel) and item.connection:
                item.connection.label_item = None
                
            self.scene.removeItem(item)

        self.statusBar().showMessage(f"{len(selected_items)} elemento(s) eliminado(s)", 2000)
            
    def clearAll(self):
        reply = QMessageBox.question(self, 'Confirmar', '¿Estás seguro de que quieres eliminar todo el diagrama?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.scene.clear()
            self.statusBar().showMessage("Diagrama limpiado", 2000)
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.deleteSelected()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_1:
            self.addNode("rectangle")
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_2:
            self.addNode("diamond")
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_3:
            self.addNode("rounded_rect")
        else:
            super().keyPressEvent(event)
            
    def getSceneRect(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isValid():
            return QRectF(0, 0, 800, 600)
        margin = 50
        return rect.adjusted(-margin, -margin, margin, margin)
    
    def exportAsPNG(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Guardar como PNG', 'diagrama.png', 'PNG Files (*.png)')
        if filename:
            self._exportAsImage(filename, 'PNG')
    
    def exportAsPDF(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Guardar como PDF', 'diagrama.pdf', 'PDF Files (*.pdf)')
        if filename:
            self._exportAsPdf(filename)
            
    def _exportAsImage(self, filename, format_type):
        try:
            source_rect = self.getSceneRect()
            image = QImage(source_rect.size().toSize() * 2, QImage.Format_ARGB32)
            image.fill(Qt.white)
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            self.scene.render(painter, QRectF(0, 0, image.width(), image.height()), source_rect)
            painter.end()
            
            success = image.save(filename, format_type, 95)
            if success:
                self.statusBar().showMessage(f"Exportado exitosamente: {filename}", 3000)
            else:
                QMessageBox.warning(self, 'Error', 'No se pudo guardar la imagen.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al exportar imagen: {e}')
            
    def _exportAsPdf(self, filename):
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            
            painter = QPainter(printer)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            source_rect = self.getSceneRect()
            scale_factor = min(printer.pageRect().width() / source_rect.width(), printer.pageRect().height() / source_rect.height())
            
            painter.scale(scale_factor, scale_factor)
            self.scene.render(painter)
            painter.end()

            self.statusBar().showMessage(f"PDF exportado exitosamente: {filename}", 3000)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al exportar PDF: {e}')
            
    def printDiagram(self):
        dialog = QPrintDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            printer = dialog.printer()
            painter = QPainter(printer)
            painter.setRenderHint(QPainter.Antialiasing)
            
            source_rect = self.getSceneRect()
            scale_factor = min(printer.pageRect().width() / source_rect.width(), printer.pageRect().height() / source_rect.height())

            painter.scale(scale_factor, scale_factor)
            self.scene.render(painter)
            painter.end()

    def createExampleDiagram(self):
        node1 = FlowchartNode("Inicio", "rounded_rect")
        node2 = FlowchartNode("¿Condición?", "diamond")
        node3 = FlowchartNode("Proceso Verdadero", "rectangle")
        node4 = FlowchartNode("Proceso Falso", "rectangle")
        node5 = FlowchartNode("Fin", "rounded_rect")
        
        node1.setPos(-200, -100)
        node2.setPos(0, -100)
        node3.setPos(-200, 100)
        node4.setPos(200, 100)
        node5.setPos(0, 300)
        
        self.scene.addItem(node1)
        self.scene.addItem(node2)
        self.scene.addItem(node3)
        self.scene.addItem(node4)
        self.scene.addItem(node5)
        
        connection1 = Connection(node1, node2)
        connection2 = Connection(node2, node3, "Sí")
        connection3 = Connection(node2, node4, "No")
        connection4 = Connection(node3, node5)
        connection5 = Connection(node4, node5)
        
        self.scene.addItem(connection1)
        self.scene.addItem(connection2)
        self.scene.addItem(connection3)
        self.scene.addItem(connection4)
        self.scene.addItem(connection5)
        
        self.view.fitInView(self.getSceneRect(), Qt.KeepAspectRatio)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = FlowchartEditor()
    editor.showMaximized()
    sys.exit(app.exec_())