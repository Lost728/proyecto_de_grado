import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFileDialog, QTextEdit, QMessageBox,
    QComboBox, QInputDialog, QTableWidget, QTableWidgetItem,
    QSplitter, QTabWidget, QGroupBox, QFormLayout, QSpinBox,
    QCheckBox, QHeaderView, QMenu, QAction, QToolBar, QStatusBar,
    QMainWindow, QProgressBar, QDialog, QDialogButtonBox
)
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot

class DatabaseThread(QThread):
    """Hilo para operaciones de base de datos que pueden tomar tiempo"""
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, cursor, query, params=None):
        super().__init__()
        self.cursor = cursor
        self.query = query
        self.params = params or []
    
    def run(self):
        try:
            if self.params:
                self.cursor.execute(self.query, self.params)
            else:
                self.cursor.execute(self.query)
            result = self.cursor.fetchall()
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class QueryDialog(QDialog):
    """Diálogo para ejecutar consultas SQL personalizadas"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ejecutar Consulta SQL")
        self.setGeometry(200, 200, 600, 400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Editor de consultas
        self.query_editor = QTextEdit()
        self.query_editor.setPlaceholderText("Escribe tu consulta SQL aquí...")
        self.query_editor.setFont(QFont("Consolas", 11))
        layout.addWidget(QLabel("Consulta SQL:"))
        layout.addWidget(self.query_editor)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_query(self):
        return self.query_editor.toPlainText().strip()

class DBManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor Avanzado de Base de Datos SQLite")
        self.setGeometry(100, 100, 1200, 800)
        
        # Variables de estado
        self.conn = None
        self.cursor = None
        self.current_db_path = ""
        
        # Configurar tema oscuro
        self.set_dark_theme()
        
        # Inicializar UI
        self.init_ui()
        self.init_menu_bar()
        self.init_status_bar()
        
        # Timer para auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        
    def set_dark_theme(self):
        """Configura un tema oscuro moderno y elegante"""
        dark_palette = QPalette()
        
        # Colores principales
        window_color = QColor(45, 45, 48)
        base_color = QColor(37, 37, 38)
        alternate_base_color = QColor(60, 60, 60)
        text_color = QColor(220, 220, 220)
        button_color = QColor(65, 65, 68)
        highlight_color = QColor(0, 120, 215)
        
        dark_palette.setColor(QPalette.Window, window_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, base_color)
        dark_palette.setColor(QPalette.AlternateBase, alternate_base_color)
        dark_palette.setColor(QPalette.ToolTipBase, base_color)
        dark_palette.setColor(QPalette.ToolTipText, text_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Button, button_color)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, highlight_color)
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        
        QApplication.setPalette(dark_palette)
        
        # Estilos CSS modernos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D30;
                color: #DCDCDC;
            }
            QWidget {
                background-color: #2D2D30;
                color: #DCDCDC;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }
            QLabel {
                color: #DCDCDC;
                font-weight: 500;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #414144;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #383838;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #0078D4;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A4A4D, stop:1 #414144);
                border: 1px solid #5A5A5A;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A5A5D, stop:1 #515154);
                border: 1px solid #6A6A6A;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3A3A3D, stop:1 #313134);
            }
            QPushButton:disabled {
                background-color: #2D2D30;
                color: #666666;
                border: 1px solid #444444;
            }
            QPushButton.success {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45A049);
                border: 1px solid #4CAF50;
            }
            QPushButton.primary {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078D4, stop:1 #106EBE);
                border: 1px solid #0078D4;
            }
            QPushButton.warning {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9800, stop:1 #F57C00);
                border: 1px solid #FF9800;
            }
            QPushButton.danger {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F44336, stop:1 #D32F2F);
                border: 1px solid #F44336;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #252526;
                color: #DCDCDC;
                border: 2px solid #414144;
                border-radius: 4px;
                padding: 6px;
                selection-background-color: #0078D4;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #0078D4;
            }
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
            QTableWidget {
                background-color: #252526;
                alternate-background-color: #2D2D30;
                gridline-color: #414144;
                border: 1px solid #414144;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #414144;
            }
            QTableWidget::item:selected {
                background-color: #0078D4;
                color: white;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A4A4D, stop:1 #414144);
                color: #DCDCDC;
                padding: 8px;
                border: 1px solid #5A5A5A;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #414144;
                background-color: #2D2D30;
            }
            QTabBar::tab {
                background-color: #383838;
                border: 1px solid #414144;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078D4;
                color: white;
            }
            QStatusBar {
                background-color: #007ACC;
                color: white;
                border-top: 1px solid #414144;
            }
            QProgressBar {
                border: 1px solid #414144;
                border-radius: 4px;
                text-align: center;
                background-color: #252526;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
        """)

    def init_menu_bar(self):
        """Inicializa la barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('Archivo')
        
        new_action = QAction('Nueva BD', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.crear_nueva_db)
        file_menu.addAction(new_action)
        
        open_action = QAction('Abrir BD', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.cargar_db)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('Exportar datos', self)
        export_action.triggered.connect(self.exportar_datos)
        file_menu.addAction(export_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('Herramientas')
        
        query_action = QAction('Ejecutar consulta SQL', self)
        query_action.setShortcut('Ctrl+Q')
        query_action.triggered.connect(self.abrir_editor_consultas)
        tools_menu.addAction(query_action)
        
        vacuum_action = QAction('Optimizar BD (VACUUM)', self)
        vacuum_action.triggered.connect(self.vacuum_database)
        tools_menu.addAction(vacuum_action)

    def init_status_bar(self):
        """Inicializa la barra de estado"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Listo")
        
        # Agregar indicadores a la barra de estado
        self.db_status_label = QLabel("Sin BD")
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def init_ui(self):
        """Inicializa la interfaz de usuario principal"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Crear pestañas
        self.tab_widget = QTabWidget()
        
        # Pestaña de gestión de BD
        db_tab = self.create_database_tab()
        self.tab_widget.addTab(db_tab, "Base de Datos")
        
        # Pestaña de visualización de datos
        data_tab = self.create_data_tab()
        self.tab_widget.addTab(data_tab, "Datos")
        
        # Pestaña de consultas
        query_tab = self.create_query_tab()
        self.tab_widget.addTab(query_tab, "Consultas")
        
        main_layout.addWidget(self.tab_widget)

    def create_database_tab(self):
        """Crea la pestaña de gestión de base de datos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de archivo de BD
        file_group = QGroupBox("Archivo de Base de Datos")
        file_layout = QVBoxLayout(file_group)
        
        file_controls = QHBoxLayout()
        self.txt_db = QLineEdit()
        self.txt_db.setReadOnly(True)
        self.txt_db.setPlaceholderText("Ningún archivo cargado...")
        
        btn_cargar = QPushButton("Cargar BD")
        btn_cargar.setProperty("class", "success")
        btn_cargar.clicked.connect(self.cargar_db)
        
        btn_nueva = QPushButton("Nueva BD")
        btn_nueva.setProperty("class", "primary")
        btn_nueva.clicked.connect(self.crear_nueva_db)
        
        btn_exportar_bd = QPushButton("📤 Exportar BD")
        menu_exportar = QMenu(btn_exportar_bd)
        
        accion_copiar = QAction("📁 Copiar archivo .db", self)
        accion_copiar.triggered.connect(self.exportar_como)
        menu_exportar.addAction(accion_copiar)
        
        accion_excel = QAction("📊 Exportar a Excel", self)
        accion_excel.triggered.connect(self.exportar_excel)
        menu_exportar.addAction(accion_excel)
        
        accion_pdf = QAction("📄 Exportar a PDF", self)
        accion_pdf.triggered.connect(self.exportar_pdf)
        menu_exportar.addAction(accion_pdf)
        
        accion_sql = QAction("📝 Exportar a SQL", self)
        accion_sql.triggered.connect(self.exportar_como)
        menu_exportar.addAction(accion_sql)
        
        btn_exportar_bd.setMenu(menu_exportar)
        file_controls.addWidget(btn_exportar_bd)
        
        file_controls.addWidget(QLabel("Archivo:"))
        file_controls.addWidget(self.txt_db)
        file_controls.addWidget(btn_cargar)
        file_controls.addWidget(btn_nueva)
        
        file_layout.addLayout(file_controls)
        
        # Grupo de creación de tablas
        create_group = QGroupBox("Crear Nueva Tabla")
        create_layout = QFormLayout(create_group)
        
        self.txt_nueva_tabla = QLineEdit()
        self.txt_nueva_tabla.setPlaceholderText("nombre_tabla")
        
        self.txt_columnas = QTextEdit()
        self.txt_columnas.setPlaceholderText(
            "Ejemplo:\n"
            "id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "nombre TEXT NOT NULL,\n"
            "edad INTEGER,\n"
            "email TEXT UNIQUE"
        )
        self.txt_columnas.setMaximumHeight(120)
        
        btn_crear_tabla = QPushButton("Crear Tabla")
        btn_crear_tabla.setProperty("class", "primary")
        btn_crear_tabla.clicked.connect(self.crear_tabla)
        
        create_layout.addRow("Nombre:", self.txt_nueva_tabla)
        create_layout.addRow("Columnas:", self.txt_columnas)
        create_layout.addRow("", btn_crear_tabla)
        
        # Grupo de gestión de tablas
        manage_group = QGroupBox("Gestión de Tablas")
        manage_layout = QVBoxLayout(manage_group)
        
        table_controls = QHBoxLayout()
        self.combo_tablas = QComboBox()
        self.combo_tablas.setMinimumWidth(200)
        
        btn_refrescar = QPushButton("🔄 Refrescar")
        btn_refrescar.clicked.connect(self.listar_tablas)
        
        btn_info = QPushButton("ℹ Info")
        btn_info.setProperty("class", "primary")
        btn_info.clicked.connect(self.mostrar_info_tabla)
        
        btn_modificar = QPushButton("✏ Modificar")
        btn_modificar.setProperty("class", "warning")
        btn_modificar.clicked.connect(self.modificar_tabla)
        
        btn_eliminar = QPushButton("🗑 Eliminar")
        btn_eliminar.setProperty("class", "danger")
        btn_eliminar.clicked.connect(self.eliminar_tabla)
        
        table_controls.addWidget(QLabel("Tabla:"))
        table_controls.addWidget(self.combo_tablas)
        table_controls.addWidget(btn_refrescar)
        table_controls.addWidget(btn_info)
        table_controls.addWidget(btn_modificar)
        table_controls.addWidget(btn_eliminar)
        table_controls.addStretch()
        
        manage_layout.addLayout(table_controls)
        
        layout.addWidget(file_group)
        layout.addWidget(create_group)
        layout.addWidget(manage_group)
        layout.addStretch()
        
        return tab
    
    def exportar_como(self):
        if not self.current_db_path:
            QMessageBox.warning(self, "Sin Base de Datos", "Primero debes cargar o crear una base de datos.")
            return
        
        nombre = os.path.basename(self.current_db_path)
        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar Base de Datos", nombre, "Bases de datos SQLite (*.db *.sqlite)"
        )
        if destino:
            try:
                import shutil
                shutil.copy2(self.current_db_path, destino)
                QMessageBox.information(self, "Éxito", f"Base de datos exportada a:\n{destino}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar la base de datos:\n{e}")

    def exportar_excel(self):
        if not self.conn:
            QMessageBox.warning(self, "Sin conexión", "Primero debes cargar una base de datos.")
            return
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar a Excel", "datos.xlsx", "Archivos Excel (*.xlsx)"
        )
        
        if archivo:
            try:
                import pandas as pd
                with pd.ExcelWriter(archivo, engine='xlsxwriter') as writer:
                    self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tablas = [row[0] for row in self.cursor.fetchall()]
                    for tabla in tablas:
                        df = pd.read_sql_query(f"SELECT * FROM {tabla};", self.conn)
                        df.to_excel(writer, sheet_name=tabla, index=False)
            
                QMessageBox.information(self, "Éxito", f"Datos exportados a Excel:\n{archivo}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar a Excel:\n{e}")

    def exportar_pdf(self):
        #Esto exporta una base de datos cargada a PDF
        if not self.conn:
            QMessageBox("Error", "Sin conexión", "Carga una base de datos primero.")
            return
        
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", "datos.pdf", "Archivos PDF (*.pdf)"
        )
        if archivo:
            try:
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.lib.styles import getSampleStyleSheet
                
                doc = SimpleDocTemplate(archivo, pagesize=landscape(letter))
                elementos = []
                estilos = getSampleStyleSheet()
                
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tablas = [row[0] for row in self.cursor.fetchall()]
                for tabla in tablas:
                    self.cursor.execute(f"PRAGMA table_info({tabla});")
                    columnas = [col[1] for col in self.cursor.fetchall()]
                    
                    self.cursor.execute(f"SELECT * FROM {tabla};")
                    filas = self.cursor.fetchall()
                    
                    elementos.append(Paragraph(f"Tabla: {tabla}", estilos['Heading2']))
                    datos = [ columnas ] + filas
                    tabla_pdf = Table(datos, repeatRows=1)
                    tabla_pdf.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elementos.append(tabla_pdf)
                    elementos.append(PageBreak())
                    
                doc.build(elementos)
                QMessageBox.information(self, "Éxito", f"Datos exportados a PDF:\n{archivo}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar a PDF:\n{e}")

    def create_data_tab(self):
        """Crea la pestaña de visualización de datos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controles superiores
        controls_layout = QHBoxLayout()
        
        self.combo_tablas_data = QComboBox()
        self.combo_tablas_data.currentTextChanged.connect(self.cargar_datos_tabla)
        
        btn_ver_datos = QPushButton("📊 Ver Datos")
        btn_ver_datos.setProperty("class", "primary")
        btn_ver_datos.clicked.connect(self.cargar_datos_tabla)
        
        btn_agregar_fila = QPushButton("➕ Agregar")
        btn_agregar_fila.setProperty("class", "success")
        btn_agregar_fila.clicked.connect(self.agregar_fila)
        
        btn_eliminar_fila = QPushButton("➖ Eliminar")
        btn_eliminar_fila.setProperty("class", "danger")
        btn_eliminar_fila.clicked.connect(self.eliminar_fila)
        
        btn_guardar_cambios = QPushButton("💾 Guardar")
        btn_guardar_cambios.setProperty("class", "success")
        btn_guardar_cambios.clicked.connect(self.guardar_cambios)
        
        controls_layout.addWidget(QLabel("Tabla:"))
        controls_layout.addWidget(self.combo_tablas_data)
        controls_layout.addWidget(btn_ver_datos)
        controls_layout.addWidget(btn_agregar_fila)
        controls_layout.addWidget(btn_eliminar_fila)
        controls_layout.addWidget(btn_guardar_cambios)
        controls_layout.addStretch()
        
        # Tabla de datos
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.table_widget)
        
        return tab
    
    def mostrar_info_tabla_data(self):
        """Muestra información de la tabla en la pestaña de datos"""
        tabla = self.combo_tablas_data.currentText()
        if not tabla:
            QMessageBox.warning(self, "Sin selección", "Selecciona una tabla.")
            return
        
        try:
            
            # Obtener información de columnas
            self.cursor.execute(f"PRAGMA table_info({tabla});")
            columnas_info = self.cursor.fetchall()
        
            # Obtener conteo de registros
            self.cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
            total_filas = self.cursor.fetchone()[0]
        
            # Obtener tamaño aproximado de la tabla
            self.cursor.execute(f"SELECT SUM(pgsize) FROM dbstat WHERE name='{tabla}';")
            tamaño_bytes = self.cursor.fetchone()[0] or 0
            tamaño_kb = tamaño_bytes / 1024
        
            # Construir mensaje de información
            info = f"📊 Información de la tabla: {tabla}\n"
            info += "═" * 50 + "\n"
            info += f"• Total de registros: {total_filas:,}\n"
            info += f"• Tamaño aproximado: {tamaño_kb:,.2f} KB\n\n"
            info += "🔷 Estructura de columnas:\n"
        
            for col in columnas_info:
                nombre = col[1]
                tipo = col[2]
                pk = "🔑 PRIMARY KEY" if col[5] else ""
                not_null = "NOT NULL" if col[3] else ""
                default = f"DEFAULT {col[4]}" if col[4] else ""
            
                info += f"\n┌ {nombre}\n"
                info += f"├ Tipo: {tipo}\n"
                if pk: info += f"├ {pk}\n"
                if not_null: info += f"├ {not_null}\n"
                if default: info += f"├ {default}\n"
        
            # Mostrar diálogo con la información
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Información de tabla: {tabla}")
            dialog.setMinimumWidth(500)
        
            layout = QVBoxLayout()
        
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 10))
            text_edit.setText(info)
        
            btn_cerrar = QPushButton("Cerrar")
            btn_cerrar.clicked.connect(dialog.close)
        
            layout.addWidget(text_edit)
            layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)
        
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener información de la tabla:\n{e}")

    def create_query_tab(self):
        """Crea la pestaña de consultas SQL"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Editor de consultas
        query_group = QGroupBox("Editor de Consultas SQL")
        query_layout = QVBoxLayout(query_group)
        
        self.query_editor = QTextEdit()
        self.query_editor.setPlaceholderText(
            "Escribe tu consulta SQL aquí...\n\n"
            "Ejemplos:\n"
            "SELECT * FROM tabla_nombre;\n"
            "INSERT INTO tabla_nombre (columna1, columna2) VALUES ('valor1', 'valor2');\n"
            "UPDATE tabla_nombre SET columna1 = 'nuevo_valor' WHERE id = 1;"
        )
        self.query_editor.setFont(QFont("Consolas", 10))
        self.query_editor.setMinimumHeight(150)
        
        query_controls = QHBoxLayout()
        btn_ejecutar = QPushButton("▶ Ejecutar")
        btn_ejecutar.setProperty("class", "success")
        btn_ejecutar.clicked.connect(self.ejecutar_consulta)
        
        btn_limpiar = QPushButton("🧹 Limpiar")
        btn_limpiar.clicked.connect(self.query_editor.clear)
        
        btn_guardar_consulta = QPushButton("💾 Guardar")
        btn_guardar_consulta.clicked.connect(self.guardar_consulta)
        
        query_controls.addWidget(btn_ejecutar)
        query_controls.addWidget(btn_limpiar)
        query_controls.addWidget(btn_guardar_consulta)
        query_controls.addStretch()
        
        query_layout.addWidget(self.query_editor)
        query_layout.addLayout(query_controls)
        
        # Resultados
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        
        results_layout.addWidget(self.results_table)
        
        # Splitter para dividir editor y resultados
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(query_group)
        splitter.addWidget(results_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab

    def crear_nueva_db(self):
        """Crea una nueva base de datos"""
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Crear nueva base de datos",
            "",
            "Bases de datos SQLite (*.db *.sqlite)"
        )
        
        if ruta:
            try:
                if self.conn:
                    self.conn.close()
                
                # Crear nueva base de datos
                self.conn = sqlite3.connect(ruta)
                self.cursor = self.conn.cursor()
                self.current_db_path = ruta
                self.txt_db.setText(ruta)
                
                self.listar_tablas()
                self.db_status_label.setText(f"BD: {os.path.basename(ruta)}")
                self.status_bar.showMessage("Nueva base de datos creada exitosamente")
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Nueva base de datos creada: {os.path.basename(ruta)}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo crear la base de datos:\n{e}"
                )

    def cargar_db(self):
        """Carga una base de datos existente"""
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir base de datos",
            "",
            "Bases de datos (*.db *.sqlite);;Todos los archivos (*)"
        )
        
        if ruta:
            try:
                if self.conn:
                    self.conn.close()
                
                self.conn = sqlite3.connect(ruta)
                self.cursor = self.conn.cursor()
                self.current_db_path = ruta
                self.txt_db.setText(ruta)
                
                self.listar_tablas()
                self.db_status_label.setText(f"BD: {os.path.basename(ruta)}")
                self.status_bar.showMessage("Base de datos cargada exitosamente")
                
                # Habilitar auto-refresh cada 30 segundos
                self.refresh_timer.start(30000)
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo cargar la base de datos:\n{e}"
                )

    def listar_tablas(self):
        if not self.cursor:
            return
        
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY 'name';")
            tablas = [filas[0] for filas in self.cursor.fetchall()]
            
            #esto guarda la seleccion
            tabla_actual_1 = self.combo_tablas.currentText()
            tabla_actual_2 = self.combo_tablas_data.currentText()
            
            #Actualiza combos
            self.combo_tablas.blockSignals(True)
            self.combo_tablas.clear()
            self.combo_tablas.addItems(tablas)
            if tabla_actual_1 in tablas:
                self.combo_tablas.setCurrentText(tabla_actual_1)
            self.combo_tablas.blockSignals(False)
            
            self.combo_tablas_data.blockSignals(True)
            self.combo_tablas_data.clear()
            self.combo_tablas_data.addItems(tablas)
            if tabla_actual_2 in tablas:
                self.combo_tablas_data.setCurrentText(tabla_actual_2)
            self.combo_tablas_data.blockSignals(False)
            
            self.status_bar.showMessage(f"{len(tablas)} tablas encontradas")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron listar las tablas:\n{e}")

    def crear_tabla(self):
        """Crea una nueva tabla con validación mejorada"""
        if not self.cursor:
            QMessageBox.warning(self, "Sin conexión", "Primero debes cargar o crear una base de datos.")
            return
            
        nombre = self.txt_nueva_tabla.text().strip()
        columnas = self.txt_columnas.toPlainText().strip()
        
        if not nombre or not columnas:
            QMessageBox.warning(self, "Campos vacíos", "Completa todos los campos.")
            return
        
        # Validar nombre de tabla
        if not nombre.replace("_", "").replace("-", "").isalnum():
            QMessageBox.warning(
                self,
                "Nombre inválido",
                "El nombre de la tabla solo puede contener letras, números, guiones y guiones bajos."
            )
            return
            
        try:
            # Verificar si la tabla ya existe
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (nombre,)
            )
            if self.cursor.fetchone():
                QMessageBox.warning(self, "Tabla existe", f"La tabla '{nombre}' ya existe.")
                return
            
            # Crear tabla
            query = f"CREATE TABLE {nombre} ({columnas})"
            self.cursor.execute(query)
            self.conn.commit()
            
            self.listar_tablas()
            self.txt_nueva_tabla.clear()
            self.txt_columnas.clear()
            
            QMessageBox.information(self, "Éxito", f"Tabla '{nombre}' creada exitosamente.")
            self.status_bar.showMessage(f"Tabla '{nombre}' creada")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear tabla:\n{e}")

    def mostrar_info_tabla(self):
        """Muestra información detallada de una tabla"""
        tabla = self.combo_tablas.currentText()
        if not tabla:
            QMessageBox.warning(self, "Sin selección", "Selecciona una tabla.")
            return
            
        try:
            # Obtener información de columnas
            self.cursor.execute(f"PRAGMA table_info({tabla});")
            columnas = self.cursor.fetchall()
        
            # Obtener datos de la tabla
            self.cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
            total_filas = self.cursor.fetchone()[0]
        
            # Crear mensaje de información - CORRECCIÓN AQUÍ
            info = f"Tabla: {tabla}\n"
            info += f"Total de filas: {total_filas}\n\n"
            info += "Columnas:\n"
            info += "-" * 50 + "\n"
        
            for col in columnas:
                pk = "(PRIMARY KEY)" if col[5] else ""
                not_null = "NOT NULL" if col[3] else ""
                default = f"DEFAULT {col[4]}" if col[4] else ""
                info += f"{col[1]}: {col[2]} {pk} {not_null} {default}\n"
            
            QMessageBox.information(self, "Información de Tabla", info)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al obtener información:\n{e}")

    def modificar_tabla(self):
        """Abre opciones para modificar tabla"""
        tabla = self.combo_tablas.currentText()
        if not tabla:
            QMessageBox.warning(self, "Sin selección", "Selecciona una tabla.")
            return
            
        opciones = ["Renombrar tabla", "Añadir columna", "Ver estructura"]
        opcion, ok = QInputDialog.getItem(
            self, "Modificar tabla", f"¿Qué deseas hacer con '{tabla}'?", opciones, editable=False
        )
        
        if ok and opcion:
            try:
                if opcion == "Renombrar tabla":
                    nuevo_nombre, ok_nombre = QInputDialog.getText(
                        self, "Renombrar tabla", f"Nuevo nombre para '{tabla}':"
                    )
                    if ok_nombre and nuevo_nombre:
                        # Validar nombre
                        if not nuevo_nombre.replace("_", "").replace("-", "").isalnum():
                            QMessageBox.warning(self, "Nombre inválido", "Nombre no válido.")
                            return
                            
                        self.cursor.execute(f"ALTER TABLE {tabla} RENAME TO {nuevo_nombre};")
                        self.conn.commit()
                        self.listar_tablas()
                        QMessageBox.information(self, "Éxito", f"Tabla renombrada a '{nuevo_nombre}'.")
                        
                elif opcion == "Añadir columna":
                    columna_def, ok_col = QInputDialog.getText(
                        self, "Añadir columna", 
                        "Definición de columna (ej: edad INTEGER):"
                    )
                    if ok_col and columna_def:
                        self.cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna_def};")
                        self.conn.commit()
                        QMessageBox.information(self, "Éxito", "Columna añadida correctamente.")
                        
                elif opcion == "Ver estructura":
                    self.mostrar_info_tabla()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error en la operación:\n{e}")

    def eliminar_tabla(self):
        """Elimina una tabla con confirmación"""
        tabla = self.combo_tablas.currentText()
        if not tabla:
            QMessageBox.warning(self, "Sin selección", "Selecciona una tabla.")
            return
            
        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación", 
            f"¿Estás seguro de eliminar la tabla '{tabla}'?\n\nEsta acción NO se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirmacion == QMessageBox.Yes:
            try:
                self.cursor.execute(f"DROP TABLE {tabla};")
                self.conn.commit()
                self.listar_tablas()
                QMessageBox.information(self, "Éxito", f"Tabla '{tabla}' eliminada.")
                self.status_bar.showMessage(f"Tabla '{tabla}' eliminada")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar tabla:\n{e}")

    def cargar_datos_tabla(self):
        """Carga los datos de la tabla seleccionada en el widget de tabla"""
        tabla = self.combo_tablas_data.currentText()
        if not tabla or not self.cursor:
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            return
            
        try:
            # Obtener información de columnas
            self.cursor.execute(f"PRAGMA table_info({tabla});")
            columnas_info = self.cursor.fetchall()
            columnas = [col[1] for col in columnas_info]
            
            # Obtener datos
            self.cursor.execute(f"SELECT * FROM {tabla};")
            datos = self.cursor.fetchall()
            
            # Configurar tabla
            self.table_widget.setRowCount(len(datos))
            self.table_widget.setColumnCount(len(columnas))
            self.table_widget.setHorizontalHeaderLabels(columnas)
            
            # Llenar datos
            for i, fila in enumerate(datos):
                for j, valor in enumerate(fila):
                    item = QTableWidgetItem(str(valor) if valor is not None else "")
                    self.table_widget.setItem(i, j, item)
            
            # Ajustar columnas
            self.table_widget.resizeColumnsToContents()
            
            self.status_bar.showMessage(f"Cargados {len(datos)} registros de '{tabla}'")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos:\n{e}")

    def agregar_fila(self):
        """Agrega una nueva fila vacía a la tabla"""
        tabla = self.combo_tablas_data.currentText()
        if not tabla:
            QMessageBox.warning(self, "Sin tabla", "Selecciona una tabla primero.")
            return
            
        try:
            # Obtener columnas
            self.cursor.execute(f"PRAGMA table_info({tabla});")
            columnas_info = self.cursor.fetchall()
            
            # Crear diálogo para nuevos datos
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Agregar registro a {tabla}")
            dialog.setModal(True)
            layout = QFormLayout(dialog)
            
            campos = {}
            for col_info in columnas_info:
                col_name = col_info[1]
                col_type = col_info[2]
                es_pk = col_info[5]  # Es primary key
                
                if es_pk and 'AUTOINCREMENT' in col_type.upper():
                    # Campo autoincremental, no permitir edición
                    campo = QLineEdit()
                    campo.setText("(Auto)")
                    campo.setReadOnly(True)
                else:
                    campo = QLineEdit()
                    campo.setPlaceholderText(f"Tipo: {col_type}")
                
                campos[col_name] = (campo, es_pk and 'AUTOINCREMENT' in col_type.upper())
                layout.addRow(f"{col_name}:", campo)
            
            # Botones
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            
            if dialog.exec_() == QDialog.Accepted:
                # Construir query INSERT
                columnas_insert = []
                valores_insert = []
                
                for col_name, (campo, es_auto) in campos.items():
                    if not es_auto:  # No incluir campos autoincrementales
                        columnas_insert.append(col_name)
                        valor = campo.text().strip()
                        valores_insert.append(valor if valor else None)
                
                if columnas_insert:
                    cols_str = ', '.join(columnas_insert)
                    placeholders = ', '.join(['?' for _ in valores_insert])
                    query = f"INSERT INTO {tabla} ({cols_str}) VALUES ({placeholders})"
                    
                    self.cursor.execute(query, valores_insert)
                    self.conn.commit()
                    
                    self.cargar_datos_tabla()  # Recargar datos
                    QMessageBox.information(self, "Éxito", "Registro agregado correctamente.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al agregar registro:\n{e}")

    def eliminar_fila(self):
        """Elimina la fila seleccionada"""
        fila_actual = self.table_widget.currentRow()
        if fila_actual < 0:
            QMessageBox.warning(self, "Sin selección", "Selecciona una fila para eliminar.")
            return
            
        tabla = self.combo_tablas_data.currentText()
        if not tabla:
            return
            
        try:
            # Obtener la primary key
            self.cursor.execute(f"PRAGMA table_info({tabla});")
            columnas_info = self.cursor.fetchall()
            pk_column = None
            
            for col_info in columnas_info:
                if col_info[5]:  # Es primary key
                    pk_column = col_info[1]
                    break
            
            if not pk_column:
                QMessageBox.warning(self, "Sin Primary Key", "No se puede eliminar: la tabla no tiene primary key.")
                return
            
            # Obtener valor de la primary key de la fila seleccionada
            pk_item = self.table_widget.item(fila_actual, 0)  # Asumimos que PK está en primera columna
            if not pk_item:
                QMessageBox.warning(self, "Error", "No se puede obtener el ID del registro.")
                return
                
            pk_value = pk_item.text()
            
            # Confirmar eliminación
            confirmacion = QMessageBox.question(
                self, "Confirmar eliminación",
                f"¿Eliminar el registro con {pk_column} = {pk_value}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirmacion == QMessageBox.Yes:
                self.cursor.execute(f"DELETE FROM {tabla} WHERE {pk_column} = ?", (pk_value,))
                self.conn.commit()
                self.cargar_datos_tabla()
                QMessageBox.information(self, "Éxito", "Registro eliminado.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar registro:\n{e}")

    def guardar_cambios(self):
        """Guarda los cambios realizados en la tabla"""
        tabla = self.combo_tablas_data.currentText()
        if not tabla:
            return
            
        try:
            # Por simplicidad, recargamos los datos
            # En una implementación más avanzada, se trackearían los cambios específicos
            self.conn.commit()
            QMessageBox.information(self, "Guardado", "Cambios guardados correctamente.")
            self.status_bar.showMessage("Cambios guardados")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar cambios:\n{e}")

    def mostrar_menu_contextual(self, position):
        """Muestra menú contextual en la tabla de datos"""
        if self.table_widget.itemAt(position) is None:
            return
            
        menu = QMenu(self)
        
        editar_action = QAction("Editar celda", self)
        editar_action.triggered.connect(self.editar_celda)
        menu.addAction(editar_action)
        
        menu.addSeparator()
        
        copiar_action = QAction("Copiar valor", self)
        copiar_action.triggered.connect(self.copiar_celda)
        menu.addAction(copiar_action)
        
        menu.exec_(self.table_widget.mapToGlobal(position))

    def editar_celda(self):
        """Permite editar una celda específica"""
        item_actual = self.table_widget.currentItem()
        if item_actual:
            item_actual.setFlags(item_actual.flags() | Qt.ItemIsEditable)
            self.table_widget.editItem(item_actual)

    def copiar_celda(self):
        """Copia el valor de la celda al portapapeles"""
        item_actual = self.table_widget.currentItem()
        if item_actual:
            QApplication.clipboard().setText(item_actual.text())
            self.status_bar.showMessage("Valor copiado al portapapeles", 2000)

    def ejecutar_consulta(self):
        """Ejecuta la consulta SQL del editor"""
        consulta = self.query_editor.toPlainText().strip()
        if not consulta:
            QMessageBox.warning(self, "Consulta vacía", "Escribe una consulta SQL.")
            return
            
        if not self.cursor:
            QMessageBox.warning(self, "Sin conexión", "Carga una base de datos primero.")
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Modo indeterminado

            # Ejecutar consulta
            self.cursor.execute(consulta)

            # Si es una consulta SELECT, mostrar resultados
            if consulta.upper().strip().startswith('SELECT'):
                resultados = self.cursor.fetchall()

                if resultados:
                    # Obtener nombres de columnas
                    columnas = [description[0] for description in self.cursor.description]

                    # Configurar tabla de resultados
                    self.results_table.setRowCount(len(resultados))
                    self.results_table.setColumnCount(len(columnas))
                    self.results_table.setHorizontalHeaderLabels(columnas)

                    # Llenar datos
                    for i, fila in enumerate(resultados):
                        for j, valor in enumerate(fila):
                            item = QTableWidgetItem(str(valor) if valor is not None else "")
                            self.results_table.setItem(i, j, item)

                    self.results_table.resizeColumnsToContents()
                    self.status_bar.showMessage(f"Consulta ejecutada: {len(resultados)} filas")
                else:
                    self.results_table.setRowCount(0)
                    self.status_bar.showMessage("Consulta ejecutada: sin resultados")
            else:
                # Para INSERT, UPDATE, DELETE, etc.
                self.conn.commit()
                filas_afectadas = self.cursor.rowcount
                self.results_table.setRowCount(0)
                self.status_bar.showMessage(f"Consulta ejecutada: {filas_afectadas} filas afectadas")
                
                # Actualizar listas de tablas si fue DDL
                if any(palabra in consulta.upper() for palabra in ['CREATE', 'DROP', 'ALTER']):
                    self.listar_tablas()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error en consulta", f"Error al ejecutar consulta:\n{e}")
            self.status_bar.showMessage("Error en consulta")
        finally:
            self.progress_bar.setVisible(False)

    def guardar_consulta(self):
        """Guarda la consulta actual en un archivo"""
        consulta = self.query_editor.toPlainText().strip()
        if not consulta:
            QMessageBox.warning(self, "Sin consulta", "No hay consulta para guardar.")
            return
            
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar consulta", "", "Archivos SQL (*.sql);;Archivos de texto (*.txt)"
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write(consulta)
                QMessageBox.information(self, "Guardado", f"Consulta guardada en {archivo}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar archivo:\n{e}")

    def abrir_editor_consultas(self):
        """Abre el diálogo del editor de consultas"""
        dialog = QueryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            consulta = dialog.get_query()
            if consulta:
                self.query_editor.setPlainText(consulta)
                self.tab_widget.setCurrentIndex(2)  # Cambiar a pestaña de consultas

    def exportar_datos(self):
        """Exporta datos de una tabla a CSV"""
        if not self.cursor:
            QMessageBox.warning(self, "Sin conexión", "Carga una base de datos primero.")
            return
        
        # Elegir tabla
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [fila[0] for fila in self.cursor.fetchall()]
        if not tablas:
            QMessageBox.information(self, "Sin tablas", "No hay tablas en la base de datos.")
            return
        
        tabla, ok = QInputDialog.getItem(self, "Seleccionar tabla", "Elige una tabla para exportar:", tablas, editable=False)
        if not ok or not tabla:
            return
        
        #elegir formato de exportación
        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "guardar como",
            f"{tabla}",
            "Archivos CSV (*.csv);;Archivos Excel (*.xlsx);;Archivos PDF (*.pdf);;Todos los archivos (*)"
        )
        if not archivo:
            return
        
        try:
            
            #-----CSV Export-----
            if archivo.lower().endswith(".csv"):
                import csv
                self.cursor.execute(f"SELECT * FROM {tabla};")
                datos = self.cursor.fetchall()
                
                self.cursor.execute(f"PRAGMA table_info({tabla});")
                columnas = [col[1] for col in self.cursor.fetchall()]
                
                with open(archivo, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer .writerow(columnas)  # Escribir encabezados
                    writer.writerows(datos)  # Escribir datos
                    
            #-----Excel Export-----
            elif archivo.lower().endswith(".xlsx"):
                from reportlab import colors
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
                
                #obtener datos y cabeceras
                self.cursor.execute(f"SELECT * FROM {tabla};")
                datos = self.cursor.fetchall()
                
                self.cursor.execute(f"PRAGMA table_info({tabla});")
                columnas = [col[1] for col in self.cursor.fetchall()]
                
                #contruir PDF
                pdf = SimpleDocTemplate(archivo, pagesize=landscape(letter))
                tabla_pdf = Table([columnas] + datos, repeatRows=1)
                
                estilo = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])
                
                tabla_pdf.setStyle(estilo)
                pdf.build([tabla_pdf])
                
            else:
                QMessageBox.warning(self, "Formato no soportado", "Elige .csv, xlsx o .pdf para exportar.")
                return
            QMessageBox.information(self, "Exportación exitosa", f"Datos exportados a {archivo} correctamente.")
            self.status_bar.showMessage(f"Datos exportados a {archivo}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar datos:\n{e}")

    def vacuum_database(self):
        """Optimiza la base de datos usando VACUUM"""
        if not self.cursor:
            QMessageBox.warning(self, "Sin conexión", "Carga una base de datos primero.")
            return
            
        confirmacion = QMessageBox.question(
            self, "Optimizar BD", 
            "¿Deseas optimizar la base de datos?\n\nEsto puede tomar tiempo en bases de datos grandes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirmacion == QMessageBox.Yes:
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                self.status_bar.showMessage("Optimizando base de datos...")
                
                self.cursor.execute("VACUUM;")
                
                QMessageBox.information(self, "Completado", "Base de datos optimizada correctamente.")
                self.status_bar.showMessage("Base de datos optimizada")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al optimizar:\n{e}")
            finally:
                self.progress_bar.setVisible(False)

    def auto_refresh(self):
        """Actualización automática de la lista de tablas"""
        if self.cursor:
            self.listar_tablas()

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        
        self.refresh_timer.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Editor SQLite Avanzado")
    app.setApplicationVersion("2.0")
    
    # Configurar icono de la aplicación (opcional)
    # app.setWindowIcon(QIcon("icono.png"))
    
    ventana = DBManager()
    ventana.showMaximized()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()