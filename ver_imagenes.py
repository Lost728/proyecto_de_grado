import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

DB_NAME = "pruebas.db"
TABLE_NAME = "imagenes"

class VerImagenesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ver Imágenes desde la Base de Datos")
        self.setGeometry(250, 250, 500, 400)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.lista = QListWidget()
        self.lista.itemClicked.connect(self.mostrar_imagen)
        layout.addWidget(self.lista)

        self.label = QLabel("Selecciona una imagen de la lista")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.btn_recargar = QPushButton("Recargar lista")
        self.btn_recargar.clicked.connect(self.cargar_lista)
        layout.addWidget(self.btn_recargar)

        self.btn_cargar = QPushButton("Cargar nueva imagen")
        self.btn_cargar.clicked.connect(self.cargar_imagen)
        layout.addWidget(self.btn_cargar)

        self.cargar_lista()

    def cargar_lista(self):
        self.lista.clear()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"SELECT id_imagen, nombre FROM {TABLE_NAME}")
            for id_imagen, nombre in cursor.fetchall():
                self.lista.addItem(f"{id_imagen}: {nombre}")
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista: {e}")

    def mostrar_imagen(self, item):
        texto = item.text()
        id_imagen = texto.split(":")[0]
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"SELECT datos FROM {TABLE_NAME} WHERE id_imagen = ?", (id_imagen,))
            row = cursor.fetchone()
            conn.close()
            if row:
                datos = row[0]
                pixmap = QPixmap()
                pixmap.loadFromData(datos)
                self.label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
            else:
                self.label.setText("No se encontró la imagen.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo mostrar la imagen: {e}")

    def cargar_imagen(self):
        from PyQt5.QtWidgets import QFileDialog
        import os
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if not file_path:
            return
        nombre = os.path.basename(file_path)
        try:
            with open(file_path, "rb") as f:
                datos = f.read()
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {TABLE_NAME} (nombre, datos) VALUES (?, ?)", (nombre, datos))
            conn.commit()
            conn.close()
            self.cargar_lista()
            QMessageBox.information(self, "Éxito", f"Imagen '{nombre}' guardada en la base de datos.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la imagen: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VerImagenesWindow()
    window.show()
    sys.exit(app.exec_())
