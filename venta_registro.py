import subprocess
import sys
import sqlite3
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter
from datetime import datetime, timedelta
import logging

# Configurar logging para debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Días de la semana en español
DIAS_ES = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

def obtener_db_path():
    """Obtiene la ruta de la base de datos de forma más robusta"""
    try:
        if getattr(sys, 'frozen', False):
            # Carpeta donde está el ejecutable
            exe_dir = os.path.dirname(sys.executable)
            db_path = os.path.join(exe_dir, "pruebas.db")
            if os.path.exists(db_path):
                return db_path
            # Si no está, busca en la carpeta temporal de PyInstaller
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
                return os.path.join(base_path, "pruebas.db")
        else:
            # En desarrollo, busca en la carpeta original
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "pruebas.db"))
    except Exception as e:
        logging.error(f"Error obteniendo ruta de DB: {e}")
        return "pruebas.db"  # Fallback

def crear_tablas_si_no_existen():
    """Crea las tablas necesarias si no existen"""
    try:
        conn = sqlite3.connect(obtener_db_path())
        cursor = conn.cursor()
        
        # Crear tabla movimientos_inventario si no existe
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
        
        # Crear tabla productos si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                codigo TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                presentacion TEXT,
                linea TEXT,
                precio REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Tablas verificadas/creadas correctamente")
    except Exception as e:
        logging.error(f"Error creando tablas: {e}")

class LibroDiarioVentas(QMainWindow):
    def __init__(self):
        super().__init__()
        self.movimientos = []
        self.orden_col = 0
        self.orden_asc = True
        
        # Crear tablas si no existen
        crear_tablas_si_no_existen()
        
        self.init_ui()
        self.cargar_movimientos()

    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("Libro Diario de Ventas")
        self.setGeometry(100, 100, 1200, 600)  # Ventana más grande

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Título
        label = QLabel("Libro Diario de Ventas")
        label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #2c3e50;")
        main_layout.addWidget(label)

        # Barra de herramientas de búsqueda
        toolbar = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por fecha (YYYY-MM-DD), mes (YYYY-MM), año (YYYY) o rango (YYYY-MM-DD a YYYY-MM-DD)")
        self.input_busqueda.returnPressed.connect(self.buscar_movimientos)
        self.input_busqueda.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 3px;")
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar_movimientos)
        btn_buscar.setStyleSheet("background-color: #3498db; color: white; padding: 5px 10px; border: none; border-radius: 3px;")
        
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.clicked.connect(self.limpiar_busqueda)
        btn_limpiar.setStyleSheet("background-color: #95a5a6; color: white; padding: 5px 10px; border: none; border-radius: 3px;")
        
        toolbar.addWidget(self.input_busqueda)
        toolbar.addWidget(btn_buscar)
        toolbar.addWidget(btn_limpiar)
        main_layout.addLayout(toolbar)

        # Botones de filtro rápido
        filtros_layout = QHBoxLayout()
        
        filtros = [
            ("Hoy", 'dia'),
            ("Esta Semana", 'semana'),
            ("Este Mes", 'mes'),
            ("Este Año", 'anio'),
            ("Semana Pasada", 'semana_pasada'),
            ("Mes Pasado", 'mes_pasado'),
            ("Año Pasado", 'anio_pasado')
        ]
        
        for texto, periodo in filtros:
            btn = QPushButton(texto)
            btn.clicked.connect(lambda checked, p=periodo: self.filtrar_por_periodo(p))
            btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 3px 8px; margin: 2px; border: none; border-radius: 3px;")
            filtros_layout.addWidget(btn)
        
        main_layout.addLayout(filtros_layout)

        # Tabla para mostrar movimientos de inventario
        self.crear_tabla()
        main_layout.addWidget(self.tabla)

        # Botones de acción
        botones_layout = QHBoxLayout()
        
        btn_exportar_excel = QPushButton("Exportar a Excel")
        btn_exportar_excel.clicked.connect(self.exportar_excel)
        btn_exportar_excel.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 12px; border: none; border-radius: 3px;")
        
        #btn_imprimir = QPushButton("Imprimir")
        #btn_imprimir.clicked.connect(self.imprimir_tabla)
        #btn_imprimir.setStyleSheet("background-color: #f39c12; color: white; padding: 8px 12px; border: none; border-radius: 3px;")
        
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(self.volver_a_ventas_admin)
        btn_volver.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px 12px; border: none; border-radius: 3px;")

        btn_estadisticas = QPushButton("Ver Estadísticas")
        btn_estadisticas.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 8px 12px; border: none; border-radius: 3px;")
        btn_estadisticas.clicked.connect(self.abrir_estadisticas)
        
        botones_layout.addWidget(btn_exportar_excel)
        #botones_layout.addWidget(btn_imprimir)
        botones_layout.addWidget(btn_estadisticas)
        botones_layout.addStretch()  # Espacio flexible
        botones_layout.addWidget(btn_volver)
        
        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; padding: 8px 12px; border: none; border-radius: 3px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        botones_layout.addWidget(btn_menu)

        main_layout.addLayout(botones_layout)

    def abrir_estadisticas(self):
        """Abre la ventana de estadísticas (estadistica.py) en el mismo proceso"""
        print("[DEBUG] Botón Ver Estadísticas presionado. Se intentará abrir la ventana de estadísticas.")
        try:
            from estadistica import EstadisticasVentas
            self.ventana_estadisticas = EstadisticasVentas()
            self.ventana_estadisticas.showMaximized()
            self.close()
        except Exception as e:
            import traceback
            print(f"[ERROR] No se pudo abrir la ventana de estadísticas: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(self, "Error", f"No se pudo abrir la ventana de estadísticas: {e}")

    def crear_tabla(self):
        """Crea y configura la tabla"""
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Código", "Producto", "Tipo", "Cantidad", "Fecha", "Observaciones", "Usuario"
        ])
        
        # Configuración de la tabla
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setFont(QFont("Arial", 10))
        self.tabla.horizontalHeader().setFont(QFont("Arial", 11, QFont.Bold))
        
        # Configurar ancho de columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Producto
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Tipo
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # Observaciones
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Usuario
        
        # Estilo de la tabla
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: 1px solid #2c3e50;
                font-weight: bold;
            }
        """)

    def limpiar_busqueda(self):
        """Limpia el campo de búsqueda y recarga todos los movimientos"""
        self.input_busqueda.clear()
        self.cargar_movimientos()

    def cargar_movimientos(self, filtro_sql=None, params=None):
        """Carga los movimientos desde la base de datos"""
        self.tabla.setRowCount(0)
        conn = None
        
        try:
            conn = sqlite3.connect(obtener_db_path())
            cursor = conn.cursor()
            
            base_query = """
                SELECT 
                    mi.id_movimiento, 
                    mi.codigo_producto, 
                    COALESCE(p.nombre, 'Sin nombre'), 
                    mi.tipo_movimiento, 
                    mi.cantidad, 
                    mi."fecha_movimiento", 
                    COALESCE(mi.observaciones, ''), 
                    COALESCE(mi.usuario, '')
                FROM movimientos_inventario mi
                LEFT JOIN productos p ON mi.codigo_producto = p.codigo
            """
            
            if filtro_sql:
                # Reemplazar mi."fecha movimiento" por "fecha movimiento" en el filtro
                filtro_sql = filtro_sql.replace('mi."fecha_movimiento"', '"fecha_movimiento"')
                filtro_sql = filtro_sql.replace('mi.codigo_producto', 'codigo_producto')
                filtro_sql = filtro_sql.replace('mi.tipo_movimiento', 'tipo_movimiento')
                filtro_sql = filtro_sql.replace('mi.usuario', 'usuario')
                filtro_sql = filtro_sql.replace('mi.observaciones', 'observaciones')
                query = f"{base_query} WHERE {filtro_sql} ORDER BY mi.id_movimiento DESC"
                cursor.execute(query, params or [])
            else:
                query = f"{base_query} ORDER BY mi.id_movimiento DESC"
                cursor.execute(query)
            
            movimientos = cursor.fetchall()
            self.movimientos = movimientos

            # Poblar la tabla
            for row_num, row_data in enumerate(movimientos):
                self.tabla.insertRow(row_num)
                for col_num, data in enumerate(row_data):
                    valor = str(data) if data is not None else ""
                    
                    # Formatear fecha si es necesario
                    if col_num == 5 and valor:  # Columna de fecha
                        try:
                            # Intentar parsear y formatear la fecha
                            dt = datetime.strptime(valor.split('.')[0], "%Y-%m-%d %H:%M:%S")
                            valor = dt.strftime("%d/%m/%Y %H:%M")
                        except:
                            pass  # Mantener el valor original si no se puede parsear
                    
                    item = QTableWidgetItem(valor)
                    
                    # Alineación según el tipo de dato
                    if col_num in [0, 4]:  # ID y cantidad
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    elif col_num == 5:  # Fecha
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    
                    self.tabla.setItem(row_num, col_num, item)
            
            # Mostrar información del resultado
            self.setWindowTitle(f"Libro Diario de Ventas - {len(movimientos)} registros")
            
        except sqlite3.Error as e:
            logging.error(f"Error de base de datos: {e}")
            self.mostrar_error_tabla(f"Error de base de datos: {e}")
        except Exception as e:
            logging.error(f"Error inesperado al cargar movimientos: {e}")
            self.mostrar_error_tabla(f"Error al cargar movimientos: {e}")
        finally:
            if conn:
                conn.close()

    def mostrar_error_tabla(self, mensaje):
        """Muestra un mensaje de error en la tabla"""
        self.tabla.setRowCount(1)
        self.tabla.setColumnCount(1)
        self.tabla.setHorizontalHeaderLabels(["Error"])
        self.tabla.setItem(0, 0, QTableWidgetItem(mensaje))

    def buscar_movimientos(self):
        """Busca movimientos según el texto ingresado"""
        texto = self.input_busqueda.text().strip()
        if not texto:
            self.cargar_movimientos()
            return

        filtro_sql = None
        params = []
        
        try:
            # Buscar por rango de fechas (formato: YYYY-MM-DD a YYYY-MM-DD)
            if ' a ' in texto.lower():
                partes = texto.lower().split(' a ')
                if len(partes) == 2:
                    fecha_ini = partes[0].strip()
                    fecha_fin = partes[1].strip()
                    filtro_sql = 'date("fecha_movimiento") BETWEEN ? AND ?'
                    params = [fecha_ini, fecha_fin]
            # Buscar por fecha exacta (YYYY-MM-DD)
            elif len(texto) == 10 and texto.count('-') == 2:
                filtro_sql = 'date("fecha_movimiento") = ?'
                params = [texto]
            # Buscar por mes (YYYY-MM)
            elif len(texto) == 7 and texto.count('-') == 1:
                filtro_sql = 'strftime("%Y-%m", "fecha_movimiento") = ?'
                params = [texto]
            # Buscar por año (YYYY)
            elif len(texto) == 4 and texto.isdigit():
                filtro_sql = 'strftime("%Y", "fecha_movimiento") = ?'
                params = [texto]
            # Buscar por código de producto, nombre, tipo de movimiento o usuario
            else:
                filtro_sql = '''(codigo_producto LIKE ? 
                               OR p.nombre LIKE ? 
                               OR tipo_movimiento LIKE ? 
                               OR usuario LIKE ?
                               OR observaciones LIKE ?)'''
                param_busqueda = f"%{texto}%"
                params = [param_busqueda] * 5
                
        except Exception as e:
            logging.error(f"Error en búsqueda: {e}")
            QMessageBox.warning(self, "Error de búsqueda", f"Error al procesar la búsqueda: {e}")
            return
            
        self.cargar_movimientos(filtro_sql, params)

    def filtrar_por_periodo(self, periodo):
        """Filtra los movimientos por período de tiempo"""
        try:
            hoy = datetime.now().date()
            
            if periodo == 'dia':
                fecha = hoy.strftime('%Y-%m-%d')
                filtro_sql = 'date("fecha_movimiento") = ?'
                params = [fecha]
                
            elif periodo == 'semana':
                # Inicio de la semana (lunes)
                inicio = hoy - timedelta(days=hoy.weekday())
                fin = inicio + timedelta(days=6)
                filtro_sql = 'date("fecha_movimiento") BETWEEN ? AND ?'
                params = [inicio.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')]
                
            elif periodo == 'mes':
                mes = hoy.strftime('%Y-%m')
                filtro_sql = 'strftime("%Y-%m", "fecha_movimiento") = ?'
                params = [mes]
                
            elif periodo == 'anio':
                anio = hoy.strftime('%Y')
                filtro_sql = 'strftime("%Y", "fecha_movimiento") = ?'
                params = [anio]
                
            elif periodo == 'semana_pasada':
                # Semana pasada (lunes a domingo)
                inicio = hoy - timedelta(days=hoy.weekday() + 7)
                fin = inicio + timedelta(days=6)
                filtro_sql = 'date("fecha_movimiento") BETWEEN ? AND ?'
                params = [inicio.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')]
                
            elif periodo == 'mes_pasado':
                # Primer día del mes pasado
                primer_dia_mes_actual = hoy.replace(day=1)
                ultimo_dia_mes_pasado = primer_dia_mes_actual - timedelta(days=1)
                mes_pasado = ultimo_dia_mes_pasado.strftime('%Y-%m')
                filtro_sql = 'strftime("%Y-%m", "fecha_movimiento") = ?'
                params = [mes_pasado]
                
            elif periodo == 'anio_pasado':
                anio_pasado = str(hoy.year - 1)
                filtro_sql = 'strftime("%Y", "fecha_movimiento") = ?'
                params = [anio_pasado]
            else:
                return
                
            self.cargar_movimientos(filtro_sql, params)
            
        except Exception as e:
            logging.error(f"Error al filtrar por período {periodo}: {e}")
            QMessageBox.warning(self, "Error", f"Error al filtrar por período: {e}")

    def exportar_excel(self):
        """Exporta los movimientos actuales a Excel"""
        if not self.movimientos:
            QMessageBox.warning(self, "Sin datos", "No hay datos para exportar.")
            return
            
        try:
            # Obtener ruta de guardado
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"movimientos_inventario_{fecha_actual}.xlsx"
            path, _ = QFileDialog.getSaveFileName(
                self, 
                "Guardar como Excel", 
                nombre_archivo, 
                "Archivos Excel (*.xlsx);;Todos los archivos (*)"
            )
            
            if not path:
                return
                
            # Preparar datos para DataFrame
            columnas = [
                "ID Movimiento", "Código Producto", "Nombre Producto", 
                "Tipo Movimiento", "Cantidad", "Fecha Movimiento", 
                "Observaciones", "Usuario"
            ]
            
            # Procesar datos
            datos = []
            for row in self.movimientos:
                fila_procesada = list(row)
                # Formatear fecha si es necesario
                if fila_procesada[5]:  # Fecha
                    try:
                        dt = datetime.strptime(str(fila_procesada[5]).split('.')[0], "%Y-%m-%d %H:%M:%S")
                        fila_procesada[5] = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        pass
                datos.append(fila_procesada)
            
            # Crear DataFrame y exportar
            df = pd.DataFrame(datos, columns=columnas)
            
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Movimientos', index=False)
                
                # Formatear el archivo Excel
                workbook = writer.book
                worksheet = writer.sheets['Movimientos']
                
                # Ajustar ancho de columnas
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value or "")) for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
            
            QMessageBox.information(self, "Exportado", f"Archivo guardado exitosamente en:\n{path}")
            
        except Exception as e:
            logging.error(f"Error al exportar a Excel: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo exportar a Excel:\n{e}")

    def imprimir_tabla(self):
        """Imprime la tabla actual"""
        try:
            if not self.movimientos:
                QMessageBox.warning(self, "Sin datos", "No hay datos para imprimir.")
                return
                
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageOrientation(QPrinter.Landscape)  # Horizontal para mejor visualización
            
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir Movimientos")
            
            if dialog.exec_() == QPrintDialog.Accepted:
                painter = QPainter(printer)
                
                try:
                    # Renderizar la tabla
                    self.tabla.render(painter)
                finally:
                    painter.end()
                    
                QMessageBox.information(self, "Impresión", "Documento enviado a la impresora.")
                
        except Exception as e:
            logging.error(f"Error al imprimir: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo imprimir:\n{e}")

    def volver_a_ventas_admin(self):
        """Regresa al módulo de administración de ventas (flujo Qt)"""
        print("[DEBUG] Botón Volver presionado. Se mostrará VentasWindow y se cerrará esta ventana.")
        try:
            from ventas_admin import VentasWindow
            self.ventana_admin = VentasWindow()
            self.ventana_admin.showMaximized()
            self.close()
        except Exception as e:
            import traceback
            logging.error(f"Error al volver a ventas_admin: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(self, "Error", f"No se pudo mostrar VentasWindow: {e}")

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

def abrir_aplicacion(nombre_py):
    """
    Abre el archivo .exe si existe, si no, ejecuta el .py en un nuevo proceso.
    Busca en múltiples ubicaciones posibles.
    """
    try:
        rutas_busqueda = []
        
        # Agregar rutas de búsqueda
        if hasattr(sys, '_MEIPASS'):
            rutas_busqueda.append(sys._MEIPASS)
        
        if getattr(sys, 'frozen', False):
            rutas_busqueda.append(os.path.dirname(sys.executable))
        
        rutas_busqueda.append(os.path.dirname(os.path.abspath(__file__)))
        rutas_busqueda.append(os.getcwd())

        exe_name = nombre_py.replace('.py', '.exe')

        # Buscar el archivo en las rutas
        for base_path in rutas_busqueda:
            exe_path = os.path.join(base_path, exe_name)
            py_path = os.path.join(base_path, nombre_py)
            
            # Intentar ejecutar .exe primero
            if os.path.exists(exe_path):
                try:
                    if sys.platform == "win32":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.Popen([exe_path], startupinfo=startupinfo, cwd=base_path)
                    else:
                        subprocess.Popen([exe_path], cwd=base_path)
                    logging.info(f"Ejecutado: {exe_path}")
                    return
                except Exception as e:
                    logging.error(f"Error ejecutando {exe_path}: {e}")
                    continue
            
            # Intentar ejecutar .py
            elif os.path.exists(py_path):
                try:
                    if sys.platform == "win32":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.Popen([sys.executable, py_path], startupinfo=startupinfo, cwd=base_path)
                    else:
                        subprocess.Popen([sys.executable, py_path], cwd=base_path)
                    logging.info(f"Ejecutado: {py_path}")
                    return
                except Exception as e:
                    logging.error(f"Error ejecutando {py_path}: {e}")
                    continue

        # Si no se encontró ningún archivo
        QMessageBox.warning(None, "⚠️ Archivo no encontrado",
                            f"No se encontró el archivo:\n{exe_name} ni {nombre_py}\n\n"
                            f"Rutas buscadas:\n" + "\n".join(rutas_busqueda))
                            
    except Exception as e:
        logging.error(f"Error general en abrir_aplicacion: {e}")
        QMessageBox.critical(None, "❌ Error", f"Error al abrir la aplicación:\n{e}")

def main():
    """Función principal"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Libro Diario de Ventas")
        app.setApplicationVersion("2.0")
        
        # Verificar si existe la base de datos
        db_path = obtener_db_path()
        if not os.path.exists(db_path):
            respuesta = QMessageBox.question(
                None, 
                "Base de datos no encontrada",
                f"No se encontró la base de datos en:\n{db_path}\n\n¿Desea continuar? Se creará una nueva base de datos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if respuesta == QMessageBox.No:
                sys.exit(0)
        
        window = LibroDiarioVentas()
        window.showMaximized()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"Error en main: {e}")
        if 'app' in locals():
            QMessageBox.critical(None, "Error Fatal", f"Error al iniciar la aplicación:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()