import sys
import sqlite3
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QComboBox, QDateEdit, QMessageBox, QGroupBox, QGridLayout,
    QSplitter, QScrollArea, QFrame, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import seaborn as sns
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar estilo de matplotlib
plt.style.use('default')
sns.set_palette("husl")

def obtener_db_path():
    """Obtiene la ruta de la base de datos de forma robusta"""
    try:
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            db_path = os.path.join(exe_dir, "pruebas.db")
            if os.path.exists(db_path):
                return db_path
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
                return os.path.join(base_path, "pruebas.db")
        else:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "pruebas.db"))
    except Exception as e:
        logging.error(f"Error obteniendo ruta de DB: {e}")
        return "pruebas.db"

def crear_tablas_si_no_existen():
    """Crea las tablas necesarias si no existen"""
    try:
        conn = sqlite3.connect(obtener_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_producto TEXT NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                cantidad REAL NOT NULL,
                "fecha_movimiento" DATETIME NOT NULL,
                observaciones TEXT,
                usuario TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                codigo TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                presentacion TEXT,
                linea TEXT,
                precio REAL DEFAULT 0.0
            )
        ''')
        
        # Crear índices para mejorar rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_inventario("fecha_movimiento")')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos_inventario(tipo_movimiento)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimientos_codigo ON movimientos_inventario(codigo_producto)')
        
        conn.commit()
        conn.close()
        logging.info("Tablas y índices verificados/creados correctamente")
    except Exception as e:
        logging.error(f"Error creando tablas: {e}")

class EstadisticasVentas(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = obtener_db_path()
        self.df_ventas = pd.DataFrame()
        
        # Crear tablas si no existen
        crear_tablas_si_no_existen()
        
        self.setGeometry(50, 20, 1700, 1200)
        self.init_ui()
        
        # Timer para actualización automática cada 5 minutos
        self.timer = QTimer()
        self.timer.timeout.connect(self.cargar_estadisticas)
        self.timer.start(300000)  # 5 minutos
        
        # Cargar datos iniciales
        self.cargar_estadisticas()

    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle('Estadísticas de Ventas - Dashboard')
        
        # Aplicar tema
        self.aplicar_tema()
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal con splitter
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Título principal sin emoji
        titulo = QLabel('Dashboard de Estadísticas de Ventas')
        titulo.setFont(QFont("Arial", 18, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(titulo)
        
    # Panel de controles (botones)
        self.crear_panel_controles(main_layout)

    # Panel de filtros
        self.crear_panel_filtros(main_layout)

    # Splitter para dividir contenido
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

    # Panel de resumen estadístico
        self.crear_panel_resumen(splitter)

    # Panel de gráficos
        self.crear_panel_graficos(splitter)

    # Configurar proporciones del splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    def aplicar_tema(self):
        """Aplica un tema moderno a la aplicación"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QComboBox, QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

    def crear_panel_filtros(self, layout):
        """Crea el panel de filtros"""
        filtros_group = QGroupBox("Filtros de Búsqueda")
        filtros_layout = QHBoxLayout()
        filtros_group.setLayout(filtros_layout)
        
        # Selector de período
        filtros_layout.addWidget(QLabel('Período:'))
        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(['Día', 'Semana', 'Mes', 'Año', 'Personalizado', 'Todo'])
        self.combo_periodo.setCurrentText('Mes')
        self.combo_periodo.currentTextChanged.connect(self.on_periodo_changed)
        filtros_layout.addWidget(self.combo_periodo)
        
        filtros_layout.addWidget(QLabel('Tipo:'))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(['Ventas', 'Compras', 'Todos los movimientos'])
        self.combo_tipo.currentTextChanged.connect(self.cargar_estadisticas)
        filtros_layout.addWidget(self.combo_tipo)
        
        # Fechas
        filtros_layout.addWidget(QLabel('Desde:'))
        self.date_inicio = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.dateChanged.connect(self.cargar_estadisticas)
        filtros_layout.addWidget(self.date_inicio)
        
        filtros_layout.addWidget(QLabel('Hasta:'))
        self.date_fin = QDateEdit(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.dateChanged.connect(self.cargar_estadisticas)
        filtros_layout.addWidget(self.date_fin)
        
        # Botón actualizar manual
        btn_actualizar = QPushButton('Actualizar')
        btn_actualizar.clicked.connect(self.cargar_estadisticas)
        filtros_layout.addWidget(btn_actualizar)
        
        filtros_layout.addStretch()
        layout.addWidget(filtros_group)

    def crear_panel_resumen(self, parent):
        """Crea el panel de resumen estadístico"""
        resumen_group = QGroupBox("Resumen Estadístico")
        resumen_layout = QGridLayout()
        resumen_group.setLayout(resumen_layout)
        
        # Crear labels para estadísticas
        self.stats_labels = {}
        stats_info = [
            ('total_movimientos', 'Total Movimientos:', 0, 0),
            ('total_productos', 'Productos Vendidos:', 0, 1),
            ('producto_top', 'Producto Top:', 1, 0),
            ('valor_promedio', 'Valor Promedio:', 1, 1),
            ('ventas_dia', 'Ventas Hoy:', 2, 0),
            ('tendencia', 'Tendencia:', 2, 1)
        ]
        
        for key, texto, fila, columna in stats_info:
            label_titulo = QLabel(texto)
            label_titulo.setFont(QFont("Arial", 10, QFont.Bold))
            label_valor = QLabel('Cargando...')
            label_valor.setFont(QFont("Arial", 12))
            label_valor.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            resumen_layout.addWidget(label_titulo, fila*2, columna)
            resumen_layout.addWidget(label_valor, fila*2+1, columna)
            
            self.stats_labels[key] = label_valor
        
        parent.addWidget(resumen_group)

    def crear_panel_graficos(self, parent):
        """Crea el panel de gráficos"""
        graficos_widget = QWidget()
        graficos_layout = QVBoxLayout()
        graficos_widget.setLayout(graficos_layout)
        
        # Crear figura con subplots
        self.figure = Figure(figsize=(14, 10), dpi=100)
        self.figure.patch.set_facecolor('white')
        self.canvas = FigureCanvas(self.figure)
        
        # Área de scroll para el canvas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.canvas)
        
        graficos_layout.addWidget(scroll_area)
        parent.addWidget(graficos_widget)

    def crear_panel_controles(self, layout):
        """Crea el panel de controles de gráficos"""
        controles_group = QGroupBox("Controles de Visualización")
        controles_layout = QHBoxLayout()
        controles_group.setLayout(controles_layout)
        
        # Botones para diferentes vistas

        botones_config = [
            ('Ventas por Tiempo', self.mostrar_ventas_tiempo),
            ('Top Productos', self.mostrar_top_productos),
            ('Productos Menos Populares', self.mostrar_productos_menos_populares),
            ('Tendencias', self.mostrar_tendencias),
            ('Análisis Detallado', self.mostrar_analisis_detallado),
            ('Exportar Datos', self.exportar_datos),
            #('Imprimir Reporte', self.imprimir_reporte)
        ]

        for texto, funcion in botones_config:
            btn = QPushButton(texto)
            btn.clicked.connect(funcion)
            controles_layout.addWidget(btn)

        # --- Botón para ir a Ventas Admin ---
        btn_ventas_admin = QPushButton('Ir a Ventas Admin')
        btn_ventas_admin.setStyleSheet('background-color: #27ae60; color: white; font-weight: bold;')
        btn_ventas_admin.clicked.connect(self.ir_a_ventas_admin)
        controles_layout.addWidget(btn_ventas_admin)

        # --- Botón para volver a Venta Registro ---
        btn_volver_registro = QPushButton('Volver a Registro de Ventas')
        btn_volver_registro.setStyleSheet('background-color: #e67e22; color: white; font-weight: bold;')
        btn_volver_registro.clicked.connect(self.volver_a_venta_registro)
        controles_layout.addWidget(btn_volver_registro)

        # --- Botón para ir a Menú Principal ---
        btn_menu = QPushButton('Menú Principal')
        btn_menu.setStyleSheet('background-color: #f1c40f; color: black; font-weight: bold;')
        btn_menu.clicked.connect(self.ir_a_menu_principal)
        controles_layout.addWidget(btn_menu)

        layout.addWidget(controles_group)

    def ir_a_ventas_admin(self):
        try:
            from ventas_admin import VentasWindow
            self.nueva_ventana = VentasWindow()
            self.nueva_ventana.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo abrir Ventas Admin:\n{e}')

    def volver_a_venta_registro(self):
        try:
            from venta_registro import LibroDiarioVentas
            self.nueva_ventana = LibroDiarioVentas()
            self.nueva_ventana.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo volver a Registro de Ventas:\n{e}')

    def ir_a_menu_principal(self):
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

    def mostrar_productos_menos_populares(self):
        """Muestra los productos menos vendidos de menor a mayor"""
        try:
            if self.df_ventas.empty:
                self.limpiar_graficos()
                return
            
            self.figure.clear()
            
            # Bottom 10 productos (excluyendo los que nunca se vendieron)
            if 'nombre' not in self.df_ventas.columns or 'cantidad' not in self.df_ventas.columns:
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No hay datos de productos/cantidades', ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            productos_vendidos = self.df_ventas.groupby('nombre')['cantidad'].sum()
            menos_populares = productos_vendidos[productos_vendidos > 0].nsmallest(10)
            
            ax = self.figure.add_subplot(111)
            if menos_populares.empty:
                ax.text(0.5, 0.5, 'No hay productos con ventas bajas', ha='center', va='center', fontsize=14)
            else:
                try:
                    bars = ax.barh(range(len(menos_populares)), menos_populares.values, color=sns.color_palette("crest", len(menos_populares)))
                except Exception:
                    bars = ax.barh(range(len(menos_populares)), menos_populares.values, color='gray')
                
                ax.set_yticks(range(len(menos_populares)))
                ax.set_yticklabels(menos_populares.index)
                ax.set_xlabel('Cantidad Vendida')
                ax.set_title('Top 10 Productos Menos Populares', fontsize=16, fontweight='bold')
                
                # No invertir el eje Y, así se muestra de menor a mayor (menos vendido arriba)
                
                # Agregar valores en las barras
                for i, (bar, valor) in enumerate(zip(bars, menos_populares.values)):
                    ax.text(valor + max(menos_populares.values)*0.01 if max(menos_populares.values) > 0 else 0.1, 
                            i, f'{valor:.0f}', va='center', fontsize=10, fontweight='bold')
                
                ax.grid(True, alpha=0.3, axis='x')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logging.error(f"Error mostrando productos menos populares: {e}")
            QMessageBox.warning(self, 'Error', f'Error generando gráfico: {e}')

    def on_periodo_changed(self):
        """Maneja el cambio de período"""
        periodo = self.combo_periodo.currentText()
        hoy = QDate.currentDate()
        
        if periodo == 'Día':
            self.date_inicio.setDate(hoy)
            self.date_fin.setDate(hoy)
        elif periodo == 'Semana':
            inicio_semana = hoy.addDays(-hoy.dayOfWeek() + 1)  # Lunes
            self.date_inicio.setDate(inicio_semana)
            self.date_fin.setDate(inicio_semana.addDays(6))
        elif periodo == 'Mes':
            self.date_inicio.setDate(QDate(hoy.year(), hoy.month(), 1))
            self.date_fin.setDate(hoy)
        elif periodo == 'Año':
            self.date_inicio.setDate(QDate(hoy.year(), 1, 1))
            self.date_fin.setDate(hoy)
        elif periodo == 'Todo':
            self.date_inicio.setDate(QDate(2020, 1, 1))
            self.date_fin.setDate(hoy)
        
        self.cargar_estadisticas()

    def cargar_datos_ventas(self):
        """Carga los datos de ventas desde la base de datos"""
        try:
            if not os.path.exists(self.db_path):
                logging.warning(f"Base de datos no encontrada: {self.db_path}")
                return pd.DataFrame()
            
            conn = sqlite3.connect(self.db_path)
            
            # Determinar tipo de movimiento a consultar
            tipo_filtro = ""
            tipo_seleccionado = self.combo_tipo.currentText()
            if tipo_seleccionado == 'Ventas':
                tipo_filtro = "AND mi.tipo_movimiento = 'venta'"
            elif tipo_seleccionado == 'Compras':
                tipo_filtro = "AND mi.tipo_movimiento = 'compra'"
            
            # Obtener fechas en formato correcto
            fecha_inicio = self.date_inicio.date().toPyDate().strftime('%Y-%m-%d')
            fecha_fin = self.date_fin.date().toPyDate().strftime('%Y-%m-%d')
            
            query = f'''
                SELECT
                    mi.id_movimiento,
                    mi.codigo_producto,
                    COALESCE(p.nombre, 'Producto Desconocido') as nombre,
                    COALESCE(p.precio, 0) as precio_unitario,
                    mi.cantidad,
                    mi.tipo_movimiento,
                    mi."fecha_movimiento" as fecha_movimiento,
                    COALESCE(mi.usuario, 'Sistema') as usuario,
                    COALESCE(mi.observaciones, '') as observaciones,
                    (mi.cantidad * COALESCE(p.precio, 0)) as valor_total
                FROM movimientos_inventario mi
                LEFT JOIN productos p ON mi.codigo_producto = p.codigo
                WHERE DATE(mi."fecha_movimiento") BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
                {tipo_filtro}
                ORDER BY mi."fecha_movimiento" DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                # Convertir fecha a datetime - manejar diferentes formatos
                try:
                    df['fecha_movimiento'] = pd.to_datetime(df['fecha_movimiento'], errors='coerce')
                except:
                    # Si falla, intentar con formato específico
                    df['fecha_movimiento'] = pd.to_datetime(df['fecha_movimiento'], 
                                                           format='%Y-%m-%d %H:%M:%S', errors='coerce')
                
                # Eliminar filas con fechas inválidas
                df = df.dropna(subset=['fecha_movimiento'])
                
                # Limpiar valores numéricos
                df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0)
                df['precio_unitario'] = pd.to_numeric(df['precio_unitario'], errors='coerce').fillna(0)
                df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce').fillna(0)
            
            logging.info(f"Cargados {len(df)} registros de ventas")
            return df
            
        except Exception as e:
            logging.error(f"Error cargando datos de ventas: {e}")
            QMessageBox.critical(self, 'Error', f'Error cargando datos: {e}')
            return pd.DataFrame()

    def cargar_estadisticas(self):
        """Carga y actualiza todas las estadísticas"""
        try:
            # Cargar datos
            self.df_ventas = self.cargar_datos_ventas()
            
            if self.df_ventas.empty:
                self.actualizar_stats_vacias()
                self.limpiar_graficos()
                return
            
            # Calcular estadísticas
            self.calcular_estadisticas()
            
            # Actualizar gráficos por defecto
            self.mostrar_ventas_tiempo()
            
        except Exception as e:
            logging.error(f"Error en cargar_estadisticas: {e}")
            QMessageBox.critical(self, 'Error', f'Error actualizando estadísticas: {e}')

    def calcular_estadisticas(self):
        """Calcula las estadísticas principales"""
        try:
            df = self.df_ventas
            
            # Validar que tenemos datos
            if df.empty:
                self.actualizar_stats_vacias()
                return
            
            # Estadísticas básicas
            total_movimientos = len(df)
            total_productos = df['cantidad'].sum()
            
            # Producto más vendido
            try:
                productos_vendidos = df.groupby('nombre')['cantidad'].sum()
                if not productos_vendidos.empty:
                    producto_top = productos_vendidos.idxmax()
                    cantidad_top = productos_vendidos.max()
                    producto_top_texto = f"{producto_top} ({cantidad_top:.0f} unidades)"
                else:
                    producto_top_texto = "N/A"
            except Exception as e:
                logging.warning(f"Error calculando producto top: {e}")
                producto_top_texto = "N/A"
            
            # Valor promedio (si hay precios)
            try:
                valor_promedio = df['valor_total'].mean() if 'valor_total' in df.columns else 0
            except Exception as e:
                logging.warning(f"Error calculando valor promedio: {e}")
                valor_promedio = 0
            
            # Ventas de hoy
            try:
                hoy = pd.Timestamp.now().date()
                ventas_hoy = len(df[df['fecha_movimiento'].dt.date == hoy])
            except Exception as e:
                logging.warning(f"Error calculando ventas de hoy: {e}")
                ventas_hoy = 0
            
            # Tendencia (comparar con período anterior)
            tendencia = self.calcular_tendencia(df)
            
            # Actualizar labels de forma segura
            try:
                self.stats_labels['total_movimientos'].setText(f"{total_movimientos:,}")
                self.stats_labels['total_productos'].setText(f"{total_productos:,.0f}")
                self.stats_labels['producto_top'].setText(producto_top_texto)
                self.stats_labels['valor_promedio'].setText(f"{valor_promedio:,.2f} Bs.")
                self.stats_labels['ventas_dia'].setText(f"{ventas_hoy}")
                self.stats_labels['tendencia'].setText(tendencia)
            except Exception as e:
                logging.error(f"Error actualizando labels: {e}")
            
        except Exception as e:
            logging.error(f"Error calculando estadísticas: {e}")
            self.actualizar_stats_vacias()

    def calcular_tendencia(self, df):
        """Calcula la tendencia de ventas"""
        try:
            if df.empty or len(df) < 2:
                return "Sin datos suficientes"
            
            # Agrupar por día y calcular promedio de los últimos días
            df_dias = df.groupby(df['fecha_movimiento'].dt.date)['cantidad'].sum()
            
            if len(df_dias) < 2:
                return "Sin datos suficientes"
            
            # Calcular tendencia simple (últimos vs anteriores)
            mitad = max(1, len(df_dias) // 2)
            periodo_reciente = df_dias.iloc[-mitad:].mean()
            periodo_anterior = df_dias.iloc[:mitad].mean()
            
            if periodo_anterior == 0:
                return "📈 Crecimiento"
            
            cambio = ((periodo_reciente - periodo_anterior) / periodo_anterior) * 100
            
            if cambio > 5:
                return f"📈 +{cambio:.1f}%"
            elif cambio < -5:
                return f"📉 {cambio:.1f}%"
            else:
                return f"➡️ {cambio:.1f}%"
                
        except Exception as e:
            logging.error(f"Error calculando tendencia: {e}")
            return "Error en cálculo"

    def actualizar_stats_vacias(self):
        """Actualiza las estadísticas cuando no hay datos"""
        try:
            for label in self.stats_labels.values():
                label.setText("Sin datos")
        except Exception as e:
            logging.error(f"Error actualizando stats vacías: {e}")

    def limpiar_graficos(self):
        """Limpia los gráficos cuando no hay datos"""
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No hay datos para mostrar\nSeleccione un período diferente', 
                    ha='center', va='center', fontsize=16, color='gray')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
        except Exception as e:
            logging.error(f"Error limpiando gráficos: {e}")

    def mostrar_ventas_tiempo(self):
        """Muestra gráfico de ventas por tiempo"""
        try:
            if self.df_ventas.empty:
                self.limpiar_graficos()
                return
            
            self.figure.clear()
            
            # Crear subplots con manejo de errores
            try:
                gs = self.figure.add_gridspec(3, 2, hspace=0.5, wspace=0.3)
            except Exception as e:
                logging.error(f"Error creando gridspec: {e}")
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Error configurando gráficos', ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return

            try:
                # Gráfico 1: Ventas por día (arriba, ocupa toda la fila)
                ax1 = self.figure.add_subplot(gs[0, :])
                df_dias = self.df_ventas.groupby(self.df_ventas['fecha_movimiento'].dt.date)['cantidad'].sum()
                
                if not df_dias.empty:
                    ax1.plot(df_dias.index, df_dias.values, marker='o', linewidth=2, markersize=4)
                    ax1.set_title('Cantidad Vendida por Día', fontsize=14, fontweight='bold')
                    ax1.set_xlabel('Fecha')
                    ax1.set_ylabel('Cantidad')
                    ax1.grid(True, alpha=0.3)
                    ax1.tick_params(axis='x', rotation=45)
                else:
                    ax1.text(0.5, 0.5, 'Sin datos por día', ha='center', va='center')
            except Exception as e:
                logging.error(f"Error en gráfico de días: {e}")

            try:
                # Gráfico 2: Distribución por tipo de movimiento
                ax2 = self.figure.add_subplot(gs[2, 0])
                tipo_counts = self.df_ventas['tipo_movimiento'].value_counts()
                
                if not tipo_counts.empty:
                    try:
                        colors = sns.color_palette("Set3", len(tipo_counts))
                    except:
                        colors = ['skyblue', 'lightcoral', 'lightgreen', 'gold'][:len(tipo_counts)]
                    
                    ax2.pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%', colors=colors)
                    ax2.set_title('Distribución por Tipo', fontsize=12, fontweight='bold')
                else:
                    ax2.text(0.5, 0.5, 'Sin datos de tipos', ha='center', va='center')
            except Exception as e:
                logging.error(f"Error en gráfico de tipos: {e}")

            try:
                # Gráfico 3: Ventas por hora del día
                ax3 = self.figure.add_subplot(gs[2, 1])
                
                # Verificar que tenemos fecha_movimiento válida
                if 'fecha_movimiento' in self.df_ventas.columns and not self.df_ventas['fecha_movimiento'].isna().all():
                    self.df_ventas['hora'] = self.df_ventas['fecha_movimiento'].dt.hour
                    ventas_hora = self.df_ventas.groupby('hora')['cantidad'].sum()
                    
                    if not ventas_hora.empty:
                        ax3.bar(ventas_hora.index, ventas_hora.values, alpha=0.7, color='skyblue')
                        ax3.set_title('Ventas por Hora del Día', fontsize=12, fontweight='bold')
                        ax3.set_xlabel('Hora')
                        ax3.set_ylabel('Cantidad')
                        ax3.grid(True, alpha=0.3)
                    else:
                        ax3.text(0.5, 0.5, 'Sin datos por hora', ha='center', va='center')
                else:
                    ax3.text(0.5, 0.5, 'Sin datos de fechas válidas', ha='center', va='center')
            except Exception as e:
                logging.error(f"Error en gráfico de horas: {e}")

            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logging.error(f"Error mostrando ventas por tiempo: {e}")
            QMessageBox.warning(self, 'Error', f'Error generando gráfico: {e}')

    def mostrar_top_productos(self):
        """Muestra los productos más vendidos de mayor a menor"""
        try:
            if self.df_ventas.empty:
                self.limpiar_graficos()
                return

            self.figure.clear()

            # Verificar que tenemos las columnas necesarias
            if 'nombre' not in self.df_ventas.columns or 'cantidad' not in self.df_ventas.columns:
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No hay datos de productos/cantidades disponibles', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return

            # Top 10 productos de mayor a menor
            top_productos = self.df_ventas.groupby('nombre')['cantidad'].sum().sort_values(ascending=False).head(10)

            if top_productos.empty:
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No hay productos para mostrar', ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return

            ax = self.figure.add_subplot(111)

            try:
                colors = sns.color_palette("viridis", len(top_productos))
            except:
                colors = ['skyblue'] * len(top_productos)

            bars = ax.barh(range(len(top_productos)), top_productos.values, color=colors)
            ax.set_yticks(range(len(top_productos)))
            ax.set_yticklabels(top_productos.index)
            ax.set_xlabel('Cantidad Vendida')
            ax.set_title('Top 10 Productos Más Vendidos', fontsize=16, fontweight='bold')

            # Mostrar de mayor a menor (más vendido arriba)
            ax.invert_yaxis()

            # Agregar valores en las barras
            for i, (bar, valor) in enumerate(zip(bars, top_productos.values)):
                try:
                    ax.text(valor + valor*0.01, i, f'{valor:.0f}', 
                           va='center', fontsize=10, fontweight='bold')
                except:
                    pass  # Si falla la adición de texto, continúa sin error

            ax.grid(True, alpha=0.3, axis='x')
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            logging.error(f"Error mostrando top productos: {e}")
            QMessageBox.warning(self, 'Error', f'Error generando gráfico: {e}')

    def mostrar_tendencias(self):
        """Muestra análisis de tendencias"""
        try:
            if self.df_ventas.empty:
                self.limpiar_graficos()
                return
            
            self.figure.clear()
            
            # Crear subplots para diferentes análisis
            try:
                gs = self.figure.add_gridspec(2, 2, hspace=0.4, wspace=0.3)
            except Exception as e:
                logging.error(f"Error creando gridspec para tendencias: {e}")
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Error configurando gráficos de tendencias', ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            try:
                # Tendencia semanal
                ax1 = self.figure.add_subplot(gs[0, :])
                
                # Verificar que tenemos fechas válidas
                if 'fecha_movimiento' in self.df_ventas.columns and not self.df_ventas['fecha_movimiento'].isna().all():
                    self.df_ventas['semana'] = self.df_ventas['fecha_movimiento'].dt.isocalendar().week
                    semanas = self.df_ventas.groupby('semana')['cantidad'].sum()
                    
                    if not semanas.empty:
                        ax1.plot(semanas.index, semanas.values, marker='o', linewidth=3, markersize=6)
                        ax1.set_title('Tendencia de Ventas por Semana', fontsize=14, fontweight='bold')
                        ax1.set_xlabel('Semana del Año')
                        ax1.set_ylabel('Cantidad Total')
                        ax1.grid(True, alpha=0.3)
                    else:
                        ax1.text(0.5, 0.5, 'Sin datos por semana', ha='center', va='center')
                else:
                    ax1.text(0.5, 0.5, 'Sin datos de fechas válidas', ha='center', va='center')
            except Exception as e:
                logging.error(f"Error en tendencia semanal: {e}")
            
            try:
                # Ventas por día de la semana
                ax2 = self.figure.add_subplot(gs[1, 0])
                dias_semana = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
                
                if 'fecha_movimiento' in self.df_ventas.columns and not self.df_ventas['fecha_movimiento'].isna().all():
                    self.df_ventas['dia_semana'] = self.df_ventas['fecha_movimiento'].dt.dayofweek
                    ventas_dia_sem = self.df_ventas.groupby('dia_semana')['cantidad'].sum()
                    
                    try:
                        colors = sns.color_palette("coolwarm", 7)
                    except:
                        colors = ['skyblue'] * 7
                    
                    bars = ax2.bar(range(7), [ventas_dia_sem.get(i, 0) for i in range(7)], color=colors)
                    ax2.set_xticks(range(7))
                    ax2.set_xticklabels(dias_semana)
                    ax2.set_title('Ventas por Día de la Semana', fontsize=12, fontweight='bold')
                    ax2.set_ylabel('Cantidad')
                else:
                    ax2.text(0.5, 0.5, 'Sin datos de fechas', ha='center', va='center')
            except Exception as e:
                logging.error(f"Error en ventas por día de semana: {e}")
            
            try:
                # Tendencia mensual
                ax3 = self.figure.add_subplot(gs[1, 1])
                
                if 'fecha_movimiento' in self.df_ventas.columns and not self.df_ventas['fecha_movimiento'].isna().all():
                    self.df_ventas['mes'] = self.df_ventas['fecha_movimiento'].dt.month
                    ventas_mes = self.df_ventas.groupby('mes')['cantidad'].sum()
                    
                    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                    
                    if not ventas_mes.empty:
                        bars = ax3.bar(ventas_mes.index, ventas_mes.values, alpha=0.8, color='coral')
                        ax3.set_title('Ventas por Mes', fontsize=12, fontweight='bold')
                        ax3.set_xlabel('Mes')
                        ax3.set_ylabel('Cantidad')
                        
                        # Configurar etiquetas del eje x de forma segura
                        meses_presentes = [meses[i-1] for i in ventas_mes.index if 1 <= i <= 12]
                        ax3.set_xticks(ventas_mes.index)
                        ax3.set_xticklabels(meses_presentes, rotation=45)
                    else:
                        ax3.text(0.5, 0.5, 'Sin datos por mes', ha='center', va='center')
                else:
                    ax3.text(0.5, 0.5, 'Sin datos de fechas', ha='center', va='center')
            except Exception as e:
                logging.error(f"Error en tendencia mensual: {e}")
            
            self.canvas.draw()
            
        except Exception as e:
            logging.error(f"Error mostrando tendencias: {e}")
            QMessageBox.warning(self, 'Error', f'Error generando análisis: {e}')

    def mostrar_analisis_detallado(self):
        """Muestra un análisis detallado con múltiples métricas"""
        try:
            if self.df_ventas.empty:
                QMessageBox.information(self, 'Sin datos', 'No hay datos para analizar.')
                return
            
            # Crear ventana de diálogo con análisis detallado
            analisis = []
            df = self.df_ventas
            
            # Estadísticas básicas
            analisis.append("📊 ANÁLISIS DETALLADO DE VENTAS")
            analisis.append("=" * 50)
            analisis.append(f"Período analizado: {self.date_inicio.date().toPyDate()} a {self.date_fin.date().toPyDate()}")
            analisis.append(f"Total de registros: {len(df):,}")
            analisis.append(f"Total productos vendidos: {df['cantidad'].sum():,.0f}")
            
            if 'valor_total' in df.columns and df['valor_total'].sum() > 0:
                analisis.append(f"Valor total de ventas: {df['valor_total'].sum():,.2f} Bs.")
                analisis.append(f"Valor promedio por venta: {df['valor_total'].mean():,.2f} Bs.")
            
            analisis.append("")
            
            # Top 5 productos (con manejo de errores)
            try:
                if 'nombre' in df.columns and 'cantidad' in df.columns:
                    analisis.append("🏆 TOP 5 PRODUCTOS MÁS VENDIDOS:")
                    top_5 = df.groupby('nombre')['cantidad'].sum().nlargest(5)
                    for i, (producto, cantidad) in enumerate(top_5.items(), 1):
                        analisis.append(f"{i}. {producto}: {cantidad:.0f} unidades")
                else:
                    analisis.append("🏆 TOP PRODUCTOS: Datos no disponibles")
            except Exception as e:
                logging.error(f"Error calculando top productos: {e}")
                analisis.append("🏆 TOP PRODUCTOS: Error en cálculo")
            
            analisis.append("")
            
            # Análisis por días (con manejo de errores)
            try:
                if 'fecha_movimiento' in df.columns and not df['fecha_movimiento'].isna().all():
                    analisis.append("📅 ANÁLISIS POR DÍAS:")
                    df_dias = df.groupby(df['fecha_movimiento'].dt.date)['cantidad'].sum()
                    
                    if not df_dias.empty:
                        analisis.append(f"Día con más ventas: {df_dias.idxmax()} ({df_dias.max():.0f} unidades)")
                        analisis.append(f"Día con menos ventas: {df_dias.idxmin()} ({df_dias.min():.0f} unidades)")
                        analisis.append(f"Promedio diario: {df_dias.mean():.1f} unidades")
                    else:
                        analisis.append("Sin datos suficientes por días")
                else:
                    analisis.append("📅 ANÁLISIS POR DÍAS: Datos de fechas no válidos")
            except Exception as e:
                logging.error(f"Error en análisis por días: {e}")
                analisis.append("📅 ANÁLISIS POR DÍAS: Error en cálculo")
            
            # Mostrar en mensaje
            mensaje_completo = "\n".join(analisis)
            QMessageBox.information(self, 'Análisis Detallado', mensaje_completo)
            
        except Exception as e:
            logging.error(f"Error en análisis detallado: {e}")
            QMessageBox.critical(self, 'Error', f'Error generando análisis: {e}')

    def exportar_datos(self):
        """Exporta los datos actuales a Excel"""
        try:
            if self.df_ventas.empty:
                QMessageBox.warning(self, 'Sin datos', 'No hay datos para exportar.')
                return
            
            from PyQt5.QtWidgets import QFileDialog
            
            # Obtener ruta de guardado
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"estadisticas_ventas_{fecha_actual}.xlsx"
            
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Estadísticas",
                nombre_archivo,
                "Archivos Excel (*.xlsx);;Todos los archivos (*)"
            )
            
            if not path:
                return
            
            # Preparar datos para exportación
            df_export = self.df_ventas.copy()
            
            # Formatear fechas de forma segura
            if 'fecha_movimiento' in df_export.columns:
                try:
                    df_export['fecha_movimiento'] = df_export['fecha_movimiento'].dt.strftime('%d/%m/%Y %H:%M')
                except:
                    # Si falla el formateo, mantener como está
                    pass
            
            # Crear resumen estadístico
            resumen = {
                'Métrica': [
                    'Total de Movimientos',
                    'Total Productos Vendidos',
                    'Período de Análisis (Inicio)',
                    'Período de Análisis (Fin)',
                    'Fecha de Exportación'
                ],
                'Valor': [
                    len(df_export),
                    df_export['cantidad'].sum() if 'cantidad' in df_export.columns else 0,
                    self.date_inicio.date().toPyDate().strftime('%d/%m/%Y'),
                    self.date_fin.date().toPyDate().strftime('%d/%m/%Y'),
                    datetime.now().strftime('%d/%m/%Y %H:%M')
                ]
            }
            
            df_resumen = pd.DataFrame(resumen)
            
            # Top productos (con manejo de errores)
            try:
                if 'nombre' in self.df_ventas.columns and 'cantidad' in self.df_ventas.columns:
                    top_productos = self.df_ventas.groupby('nombre').agg({
                        'cantidad': 'sum',
                        'valor_total': 'sum' if 'valor_total' in self.df_ventas.columns else 'count'
                    }).round(2)
                    top_productos = top_productos.sort_values('cantidad', ascending=False).head(20)
                else:
                    # Crear DataFrame vacío si no hay datos
                    top_productos = pd.DataFrame({'cantidad': [], 'valor_total': []})
            except Exception as e:
                logging.error(f"Error creando top productos: {e}")
                top_productos = pd.DataFrame({'cantidad': [], 'valor_total': []})
            
            # Exportar con múltiples hojas
            try:
                with pd.ExcelWriter(path, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Datos Detallados', index=False)
                    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                    
                    if not top_productos.empty:
                        top_productos.to_excel(writer, sheet_name='Top Productos')
                    
                    # Formatear hojas de forma segura
                    try:
                        for sheet_name in writer.sheets:
                            worksheet = writer.sheets[sheet_name]
                            for column_cells in worksheet.columns:
                                try:
                                    length = max(len(str(cell.value or "")) for cell in column_cells)
                                    worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
                                except:
                                    pass  # Si falla el ajuste de ancho, continúa
                    except Exception as e:
                        logging.warning(f"Error formateando Excel: {e}")
                
                QMessageBox.information(self, 'Exportación Exitosa', 
                                      f'Datos exportados exitosamente a:\n{path}')
            except Exception as e:
                raise Exception(f"Error escribiendo archivo Excel: {e}")
            
        except Exception as e:
            logging.error(f"Error exportando datos: {e}")
            QMessageBox.critical(self, 'Error', f'Error al exportar datos:\n{e}')

    def imprimir_reporte(self):
        """Genera e imprime un reporte de estadísticas"""
        try:
            if self.df_ventas.empty:
                QMessageBox.warning(self, 'Sin datos', 'No hay datos para imprimir.')
                return
            
            try:
                from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
                from PyQt5.QtGui import QPainter, QTextDocument
            except ImportError:
                QMessageBox.warning(self, 'Error', 'Módulo de impresión no disponible.')
                return
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageOrientation(QPrinter.Portrait)
            
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir Estadísticas")
            
            if dialog.exec_() == QPrintDialog.Accepted:
                # Crear documento HTML para impresión
                html_content = self.generar_reporte_html()
                
                document = QTextDocument()
                document.setHtml(html_content)
                document.print_(printer)
                
                QMessageBox.information(self, 'Impresión', 'Reporte enviado a la impresora.')
        
        except Exception as e:
            logging.error(f"Error imprimiendo: {e}")
            QMessageBox.critical(self, 'Error', f'Error al imprimir:\n{e}')

    def generar_reporte_html(self):
        """Genera el contenido HTML del reporte"""
        try:
            df = self.df_ventas
            
            # Calcular estadísticas de forma segura
            total_movimientos = len(df)
            total_productos = df['cantidad'].sum() if 'cantidad' in df.columns else 0
            periodo_inicio = self.date_inicio.date().toPyDate().strftime('%d/%m/%Y')
            periodo_fin = self.date_fin.date().toPyDate().strftime('%d/%m/%Y')
            
            # Top 5 productos con manejo de errores
            top_5_html = ""
            try:
                if 'nombre' in df.columns and 'cantidad' in df.columns:
                    top_5 = df.groupby('nombre')['cantidad'].sum().nlargest(5)
                    for i, (producto, cantidad) in enumerate(top_5.items(), 1):
                        top_5_html += f"<tr><td>{i}</td><td>{producto}</td><td>{cantidad:.0f}</td></tr>"
                else:
                    top_5_html = "<tr><td colspan='3'>No hay datos de productos disponibles</td></tr>"
            except Exception as e:
                logging.error(f"Error generando top 5 para reporte: {e}")
                top_5_html = "<tr><td colspan='3'>Error generando datos</td></tr>"
            
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; text-align: center; }}
                    h2 {{ color: #34495e; border-bottom: 2px solid #3498db; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ border: 1px solid #bdc3c7; padding: 8px; text-align: left; }}
                    th {{ background-color: #ecf0f1; font-weight: bold; }}
                    .stat-box {{ background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; }}
                </style>
            </head>
            <body>
                <h1>📊 Reporte de Estadísticas de Ventas</h1>
                
                <div class="stat-box">
                    <strong>Período de Análisis:</strong> {periodo_inicio} - {periodo_fin}<br>
                    <strong>Fecha de Reporte:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
                    <strong>Tipo de Análisis:</strong> {self.combo_tipo.currentText()}
                </div>
                
                <h2>Resumen General</h2>
                <table>
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Total de Movimientos</td><td>{total_movimientos:,}</td></tr>
                    <tr><td>Total Productos Vendidos</td><td>{total_productos:,.0f}</td></tr>
                    <tr><td>Valor total de ventas</td><td>{df['valor_total'].sum():,.2f} Bs.</td></tr>
                    <tr><td>Valor promedio por venta</td><td>{df['valor_total'].mean():,.2f} Bs.</td></tr>
                </table>
                
                <h2>Top 5 Productos Más Vendidos</h2>
                <table>
                    <tr><th>Posición</th><th>Producto</th><th>Cantidad</th></tr>
                    {top_5_html}
                </table>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logging.error(f"Error generando reporte HTML: {e}")
            return "<html><body><h1>Error generando reporte</h1></body></html>"

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana"""
        try:
            # Detener el timer
            if hasattr(self, 'timer'):
                self.timer.stop()
            
            # Limpiar recursos
            if hasattr(self, 'figure'):
                self.figure.clear()
            
            event.accept()
            
        except Exception as e:
            logging.error(f"Error cerrando aplicación: {e}")
            event.accept()

def main():
    """Función principal"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Estadísticas de Ventas")
        app.setApplicationVersion("2.0")
        
        # Verificar dependencias
        try:
            import matplotlib
            import pandas
            import numpy
        except ImportError as e:
            QMessageBox.critical(None, "Error de Dependencias", 
                               f"Faltan librerías necesarias:\n{e}\n\n"
                               "Instale con: pip install matplotlib pandas numpy seaborn PyQt5")
            sys.exit(1)
        
        # Verificar base de datos
        db_path = obtener_db_path()
        if not os.path.exists(db_path):
            respuesta = QMessageBox.question(
                None,
                "Base de datos no encontrada",
                f"No se encontró la base de datos en:\n{db_path}\n\n"
                "¿Desea continuar? Se creará una nueva base de datos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if respuesta == QMessageBox.No:
                sys.exit(0)
        
        # Crear y mostrar ventana
        window = EstadisticasVentas()
        window.showMaximized()
        
        logging.info("Aplicación de estadísticas iniciada correctamente")
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"Error en main: {e}")
        if 'app' in locals():
            QMessageBox.critical(None, "Error Fatal", f"Error al iniciar la aplicación:\n{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()