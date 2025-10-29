import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt

class HistorialProducto(QWidget):
    def __init__(self, codigo_producto):
        super().__init__()
        self.setWindowTitle(f"Historial de Movimientos - {codigo_producto}")
        self.resize(900, 500)
        self.db_path = "pruebas.db"
        self.codigo_producto = codigo_producto

        # Fondo con imagen 'mar' desde la base de datos (estilo devoluciones.py)
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QLabel, QGraphicsBlurEffect
        def obtener_pixmap_fondo():
            try:
                conn = sqlite3.connect(self.db_path)
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

        layout = QVBoxLayout(self)

        # Título y botones con estilo moderno
        top_layout = QHBoxLayout()
        lbl_titulo = QLabel(f"Historial de Movimientos - {codigo_producto}")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #AEEFFF; background: rgba(106,27,154,0.45); padding: 10px 18px; border-radius: 10px;")
        top_layout.addWidget(lbl_titulo)
        top_layout.addStretch()
        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #4AD0FF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_volver.clicked.connect(self.volver_a_reporte_prod)
        top_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #AEEFFF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        top_layout.addWidget(btn_menu)

        layout.addLayout(top_layout)

        # Tabla de historial con estilo moderno
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID Movimiento", "Código Producto", "Tipo Movimiento", "Cantidad", "Fecha Movimiento", "Observaciones", "Usuario"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget { background: transparent; color: #E3F6FF; border: none; font-size: 15px; }
            QTableWidget::item { background: transparent; color: #E3F6FF; }
            QTableWidget::item:selected { background: rgba(74,208,255,0.18); color: #AEEFFF; }
            QHeaderView::section { background: rgba(106,27,154,0.45); color: #AEEFFF; border: none; padding: 8px; font-size: 16px; font-weight: bold; }
        """)
        layout.addWidget(self.tabla)
    def resizeEvent(self, event):
        # Ajustar el pixmap de fondo cuando la ventana cambie de tamaño
        if hasattr(self, 'bg_label'):
            pixmap = self.bg_label.pixmap()
            if pixmap:
                self.bg_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        return super().resizeEvent(event)

        # Título y botón volver
        top_layout = QHBoxLayout()
        lbl_titulo = QLabel(f"Historial de Movimientos - {codigo_producto}")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #AEEFFF; background: rgba(106,27,154,0.45); padding: 10px 18px; border-radius: 10px;")
        top_layout.addWidget(lbl_titulo)
        top_layout.addStretch()
        btn_volver = QPushButton("Volver")
        btn_volver.setStyleSheet("background-color: #4AD0FF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_volver.clicked.connect(self.volver_a_reporte_prod)
        top_layout.addWidget(btn_volver)

        btn_menu = QPushButton("Menú Principal")
        btn_menu.setStyleSheet("background-color: #AEEFFF; color: #311b92; font-weight: bold; padding: 8px 15px; border-radius: 10px; font-size: 15px;")
        btn_menu.clicked.connect(self.ir_menu_principal)
        top_layout.addWidget(btn_menu)

        layout.addLayout(top_layout)

        # Tabla de historial (coincide con la estructura de movimientos_inventario)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID Movimiento", "Código Producto", "Tipo Movimiento", "Cantidad", "Fecha Movimiento", "Observaciones", "Usuario"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget { background: transparent; color: #E3F6FF; border: none; font-size: 15px; }
            QTableWidget::item { background: transparent; color: #E3F6FF; }
            QTableWidget::item:selected { background: rgba(74,208,255,0.18); color: #AEEFFF; }
            QHeaderView::section { background: rgba(106,27,154,0.45); color: #AEEFFF; border: none; padding: 8px; font-size: 16px; font-weight: bold; }
        """)
        layout.addWidget(self.tabla)

        self.cargar_historial()

    def volver_a_reporte_prod(self):
        self.close()

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

    def cargar_historial(self):
        self.tabla.setRowCount(0)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_movimiento, codigo_producto, tipo_movimiento, cantidad, fecha_movimiento, observaciones, usuario
                FROM movimientos_inventario
                WHERE codigo_producto = ?
                ORDER BY fecha_movimiento DESC
            """, (self.codigo_producto,))
            movimientos = cursor.fetchall()
            conn.close()
            for row_num, (id_mov, cod_prod, tipo, cantidad, fecha, obs, usuario) in enumerate(movimientos):
                self.tabla.insertRow(row_num)
                self.tabla.setItem(row_num, 0, QTableWidgetItem(str(id_mov)))
                self.tabla.setItem(row_num, 1, QTableWidgetItem(str(cod_prod)))
                self.tabla.setItem(row_num, 2, QTableWidgetItem(str(tipo)))
                self.tabla.setItem(row_num, 3, QTableWidgetItem(str(cantidad)))
                self.tabla.setItem(row_num, 4, QTableWidgetItem(str(fecha)))
                self.tabla.setItem(row_num, 5, QTableWidgetItem(str(obs) if obs else ""))
                self.tabla.setItem(row_num, 6, QTableWidgetItem(str(usuario)))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el historial: {e}")

if __name__ == "__main__":
    import sys
    codigo = sys.argv[1] if len(sys.argv) > 1 else "P001"
    app = QApplication(sys.argv)
    ventana = HistorialProducto(codigo)
    ventana.showMaximized()
    sys.exit(app.exec_())