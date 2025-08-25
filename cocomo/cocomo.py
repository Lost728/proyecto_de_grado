import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QTabWidget, 
                             QTextEdit, QDoubleSpinBox, QSpinBox, QMessageBox)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt

class MinecraftCOCOMOApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora COCOMO - Minecraft Edition")
        self.setWindowIcon(QIcon("creeper_icon.png"))  # Necesitarías tener un icono
        self.setMinimumSize(900, 700)
        
        # Crear pestañas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Crear las diferentes pestañas
        self.create_intro_tab()
        self.create_params_tab()
        self.create_calculation_tab()
        self.create_results_tab()
        
        # Variables para almacenar resultados
        self.pf_nominal = 0
        self.pf_real = 0
        self.esfuerzo = 0
        self.duracion_semanas = 0
        self.costo = 0
        
    def create_intro_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Calculadora COCOMO - Minecraft Edition")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4CAF50;")
        layout.addWidget(title)
        
        # Imagen Minecraft (simulada con un widget)
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setText("⚒️ [Imagen de Minecraft] ⚒️")
        img_label.setFont(QFont("Arial", 24))
        img_label.setStyleSheet("background-color: #8B4513; color: #FFD700; padding: 20px;")
        layout.addWidget(img_label)
        
        # Descripción
        desc = QLabel(
            "Esta herramienta calcula el esfuerzo, duración y costo de proyectos de software\n"
            "usando el modelo COCOMO, con una analogía de construcción en Minecraft.\n\n"
            "¿Construirás una cabaña simple (orgánico), un castillo (semi-acoplado)\n"
            "o una ciudad flotante con granjas automáticas (empotrado)?\n\n"
            "¡Selecciona el tipo de proyecto y completa los parámetros para calcular!"
        )
        desc.setFont(QFont("Arial", 12))
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Tipos de proyectos en Minecraft
        projects_group = QGroupBox("Tipos de Proyectos en Minecraft")
        projects_layout = QGridLayout()
        
        # Proyecto orgánico
        org_label = QLabel("⚔️ Orgánico: Cabana de madera\n- <50k bloques\n- Terreno plano\n- Sin redstone")
        org_label.setFont(QFont("Arial", 10))
        projects_layout.addWidget(org_label, 0, 0)
        
        # Proyecto semi-acoplado
        semi_label = QLabel("🏰 Semi-Acoplado: Castillo medieval\n- <300k bloques\n- Redstone básico\n- Terreno montañoso")
        semi_label.setFont(QFont("Arial", 10))
        projects_layout.addWidget(semi_label, 0, 1)
        
        # Proyecto empotrado
        emb_label = QLabel("🌌 Empotrado: Ciudad flotante con granjas automáticas\n- >300k bloques\n- Redstone complejo\n- Mods avanzados\n- En el Nether")
        emb_label.setFont(QFont("Arial", 10))
        projects_layout.addWidget(emb_label, 0, 2)
        
        projects_group.setLayout(projects_layout)
        layout.addWidget(projects_group)
        
        # Botón para continuar
        next_btn = QPushButton("Comenzar Cálculos →")
        next_btn.setFont(QFont("Arial", 12, QFont.Bold))
        next_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        next_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        layout.addWidget(next_btn)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Introducción")
    
    def create_params_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Parámetros del Proyecto")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grupo para parámetros de puntos de función
        pf_group = QGroupBox("Puntos de Función (Bloques en Minecraft)")
        pf_layout = QGridLayout()
        
        pf_layout.addWidget(QLabel("Número de entradas: -elemento interactivos-"), 0, 0)
        self.entradas = QSpinBox()
        self.entradas.setRange(0, 100)
        self.entradas.setValue(12)
        pf_layout.addWidget(self.entradas, 0, 1)
        
        pf_layout.addWidget(QLabel("Número de salidas: -resultado de los elemntos interactivos-"), 1, 0)
        self.salidas = QSpinBox()
        self.salidas.setRange(0, 100)
        self.salidas.setValue(14)
        pf_layout.addWidget(self.salidas, 1, 1)
        
        pf_layout.addWidget(QLabel("Número de peticiones: -procesos internos entre entrada y salida-"), 2, 0)
        self.peticiones = QSpinBox()
        self.peticiones.setRange(0, 100)
        self.peticiones.setValue(11)
        pf_layout.addWidget(self.peticiones, 2, 1)
        
        pf_layout.addWidget(QLabel("Número de archivos: -son la tablas de la BD-"), 3, 0)
        self.archivos = QSpinBox()
        self.archivos.setRange(0, 100)
        self.archivos.setValue(16)
        pf_layout.addWidget(self.archivos, 3, 1)
        
        pf_layout.addWidget(QLabel("Número de interfaces:"), 4, 0)
        self.interfaces = QSpinBox()
        self.interfaces.setRange(0, 100)
        self.interfaces.setValue(0)
        pf_layout.addWidget(self.interfaces, 4, 1)
        
        pf_group.setLayout(pf_layout)
        layout.addWidget(pf_group)
        
        # Grupo para factores de ajuste
        fa_group = QGroupBox("Factores de Ajuste (Complejidad en Minecraft)")
        fa_layout = QGridLayout()
        
        questions = [
            "1. ¿Requiere copias de seguridad?",
            "2. ¿Requiere comunicación de datos?",
            "3. ¿Existen funciones distribuidas?",
            "4. ¿Es crítico el funcionamiento?",
            "5. ¿Entorno operativo complejo?",
            "6. ¿Entrada de datos interactivos?",
            "7. ¿Entrada en múltiples pantallas?",
            "8. ¿Actualización interactiva de archivos?",
            "9. ¿Complejidad en E/S?",
            "10. ¿Complejidad de procesamiento?",
            "11. ¿Diseño para reutilización?",
            "12. ¿Incluye conversión e instalación?",
            "13. ¿Soporte para múltiples instalaciones?",
            "14. ¿Facilitación para cambios?"
        ]
        
        self.fa_values = []
        for i, question in enumerate(questions):
            fa_layout.addWidget(QLabel(question), i, 0)
            spinbox = QSpinBox()
            spinbox.setRange(1, 5)
            spinbox.setValue(4 if i < 4 else 3)
            fa_layout.addWidget(spinbox, i, 1)
            self.fa_values.append(spinbox)
        
        fa_group.setLayout(fa_layout)
        layout.addWidget(fa_group)
        
        # Grupo para parámetros adicionales
        params_group = QGroupBox("Parámetros Adicionales")
        params_layout = QGridLayout()
        
        params_layout.addWidget(QLabel("Tipo de proyecto:"), 0, 0)
        self.tipo_proyecto = QComboBox()
        self.tipo_proyecto.addItems(["Orgánico (Cabaña)", "Semi-Acoplado (Castillo)", "Empotrado (Ciudad flotante)"])
        params_layout.addWidget(self.tipo_proyecto, 0, 1)
        
        params_layout.addWidget(QLabel("% Reutilización:"), 1, 0)
        self.reutilizacion = QDoubleSpinBox()
        self.reutilizacion.setRange(0, 100)
        self.reutilizacion.setValue(35)
        self.reutilizacion.setSuffix("%")
        params_layout.addWidget(self.reutilizacion, 1, 1)
        
        params_layout.addWidget(QLabel("Productividad:"), 2, 0)
        self.productividad = QDoubleSpinBox()
        self.productividad.setRange(0.1, 10)
        self.productividad.setValue(2)
        self.productividad.setSuffix(" PF/hora")
        params_layout.addWidget(self.productividad, 2, 1)
        
        params_layout.addWidget(QLabel("Sueldo mínimo:"), 3, 0)
        self.sueldo_min = QDoubleSpinBox()
        self.sueldo_min.setRange(0, 10000)
        self.sueldo_min.setValue(3500)
        self.sueldo_min.setPrefix("$")
        params_layout.addWidget(self.sueldo_min, 3, 1)
        
        params_layout.addWidget(QLabel("Sueldo más probable:"), 4, 0)
        self.sueldo_mp = QDoubleSpinBox()
        self.sueldo_mp.setRange(0, 10000)
        self.sueldo_mp.setValue(6500)
        self.sueldo_mp.setPrefix("$")
        params_layout.addWidget(self.sueldo_mp, 4, 1)
        
        params_layout.addWidget(QLabel("Sueldo máximo:"), 5, 0)
        self.sueldo_max = QDoubleSpinBox()
        self.sueldo_max.setRange(0, 10000)
        self.sueldo_max.setValue(7000)
        self.sueldo_max.setPrefix("$")
        params_layout.addWidget(self.sueldo_max, 5, 1)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Volver")
        back_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        back_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        btn_layout.addWidget(back_btn)
        
        calc_btn = QPushButton("Calcular Proyecto")
        calc_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        calc_btn.clicked.connect(self.calculate_cocomo)
        btn_layout.addWidget(calc_btn)
        
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Parámetros")
    
    def create_calculation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Cálculos COCOMO")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grupo para cálculos intermedios
        calc_group = QGroupBox("Proceso de Cálculo")
        calc_layout = QVBoxLayout()
        
        self.calc_text = QTextEdit()
        self.calc_text.setReadOnly(True)
        self.calc_text.setFont(QFont("Courier New", 10))
        self.calc_text.setStyleSheet("background-color: #f0f0f0;")
        calc_layout.addWidget(self.calc_text)
        
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)
        
        # Grupo para resultados intermedios
        results_group = QGroupBox("Resultados Intermedios")
        results_layout = QGridLayout()
        
        results_layout.addWidget(QLabel("PF Nominal:"), 0, 0)
        self.pf_nominal_label = QLabel("0")
        results_layout.addWidget(self.pf_nominal_label, 0, 1)
        
        results_layout.addWidget(QLabel("Promedio Factores de Ajuste:"), 1, 0)
        self.fa_prom_label = QLabel("0")
        results_layout.addWidget(self.fa_prom_label, 1, 1)
        
        results_layout.addWidget(QLabel("PF Ajustado:"), 2, 0)
        self.pf_ajust_label = QLabel("0")
        results_layout.addWidget(self.pf_ajust_label, 2, 1)
        
        results_layout.addWidget(QLabel("PF Real:"), 3, 0)
        self.pf_real_label = QLabel("0")
        results_layout.addWidget(self.pf_real_label, 3, 1)
        
        results_layout.addWidget(QLabel("Tipo de Proyecto:"), 4, 0)
        self.tipo_label = QLabel("")
        results_layout.addWidget(self.tipo_label, 4, 1)
        
        results_layout.addWidget(QLabel("Coeficientes (a, b, c, d):"), 5, 0)
        self.coef_label = QLabel("")
        results_layout.addWidget(self.coef_label, 5, 1)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Ajustar Parámetros")
        back_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        back_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        btn_layout.addWidget(back_btn)
        
        next_btn = QPushButton("Ver Resultados Finales →")
        next_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        next_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
        btn_layout.addWidget(next_btn)
        
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Cálculos")
    
    def create_results_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Resultados Finales")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grupo para resultados principales
        results_group = QGroupBox("Resultados COCOMO")
        results_layout = QGridLayout()
        
        results_layout.addWidget(QLabel("Esfuerzo estimado:"), 0, 0)
        self.esfuerzo_label = QLabel("0")
        self.esfuerzo_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        results_layout.addWidget(self.esfuerzo_label, 0, 1)
        
        results_layout.addWidget(QLabel("Duración del proyecto:"), 1, 0)
        self.duracion_label = QLabel("0 semanas (0 meses)")
        self.duracion_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        results_layout.addWidget(self.duracion_label, 1, 1)
        
        results_layout.addWidget(QLabel("Costo del proyecto:"), 2, 0)
        self.costo_label = QLabel("$0")
        self.costo_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        results_layout.addWidget(self.costo_label, 2, 1)
        
        results_layout.addWidget(QLabel("Costo por PF:"), 3, 0)
        self.costo_pf_label = QLabel("$0")
        results_layout.addWidget(self.costo_pf_label, 3, 1)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Grupo para analogía Minecraft
        mc_group = QGroupBox("Equivalente en Minecraft")
        mc_layout = QVBoxLayout()
        
        self.mc_analogy = QTextEdit()
        self.mc_analogy.setReadOnly(True)
        self.mc_analogy.setFont(QFont("Arial", 11))
        self.mc_analogy.setStyleSheet("background-color: #E8F5E9;")
        mc_layout.addWidget(self.mc_analogy)
        
        mc_group.setLayout(mc_layout)
        layout.addWidget(mc_group)
        
        # Grupo para resumen
        summary_group = QGroupBox("Resumen del Proyecto")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Arial", 10))
        self.summary_text.setStyleSheet("background-color: #FFFDE7;")
        summary_layout.addWidget(self.summary_text)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        restart_btn = QPushButton("Reiniciar Cálculos")
        restart_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        restart_btn.clicked.connect(self.restart)
        btn_layout.addWidget(restart_btn)
        
        export_btn = QPushButton("Exportar Resultados")
        export_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 8px;")
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Resultados")
    
    def calculate_cocomo(self):
        try:
            # Calcular puntos de función nominales
            self.pf_nominal = (
                self.entradas.value() * 4 +  # Peso medio para entradas
                self.salidas.value() * 5 +   # Peso medio para salidas
                self.peticiones.value() * 4 + # Peso medio para peticiones
                self.archivos.value() * 10 +  # Peso medio para archivos
                self.interfaces.value() * 7   # Peso simple para interfaces
            )
            
            # Calcular promedio de factores de ajuste
            total_fa = sum(spinbox.value() for spinbox in self.fa_values)
            fa_prom = total_fa / len(self.fa_values)
            
            # Calcular PF ajustado
            pf_ajustado = self.pf_nominal * (0.65 + 0.01 * fa_prom)
            
            # Calcular PF reales con reutilización
            reutilizacion = self.reutilizacion.value() / 100.0
            self.pf_real = pf_ajustado * (1 - reutilizacion)
            
            # Obtener coeficientes según tipo de proyecto
            tipo_index = self.tipo_proyecto.currentIndex()
            if tipo_index == 0:  # Orgánico
                a, b, c, d = 2.4, 1.05, 2.5, 0.38
                tipo = "Orgánico (Cabaña)"
            elif tipo_index == 1:  # Semi-acoplado
                a, b, c, d = 3.0, 1.12, 2.5, 0.35
                tipo = "Semi-Acoplado (Castillo)"
            else:  # Empotrado
                a, b, c, d = 3.6, 1.20, 2.5, 0.32
                tipo = "Empotrado (Ciudad flotante)"
            
            # Calcular esfuerzo
            self.esfuerzo = a * (self.pf_real ** b)
            
            # Calcular duración en semanas
            self.duracion_semanas = c * (self.esfuerzo ** d)
            duracion_meses = self.duracion_semanas / 4.33  # Aproximación de semanas por mes
            
            # Calcular costos
            ve = (self.sueldo_min.value() + 4 * self.sueldo_mp.value() + self.sueldo_max.value()) / 6
            costo_pf = ve / self.productividad.value()
            self.costo = costo_pf * self.pf_real
            
            # Actualizar pestaña de cálculos
            self.calc_text.clear()
            self.calc_text.append("=== CÁLCULO DE PUNTOS DE FUNCIÓN ===")
            self.calc_text.append(f"Entradas: {self.entradas.value()} x 4 = {self.entradas.value() * 4}")
            self.calc_text.append(f"Salidas: {self.salidas.value()} x 5 = {self.salidas.value() * 5}")
            self.calc_text.append(f"Peticiones: {self.peticiones.value()} x 4 = {self.peticiones.value() * 4}")
            self.calc_text.append(f"Archivos: {self.archivos.value()} x 10 = {self.archivos.value() * 10}")
            self.calc_text.append(f"Interfaces: {self.interfaces.value()} x 7 = {self.interfaces.value() * 7}")
            self.calc_text.append(f"\nPF Nominal: {self.pf_nominal:.2f}")
            
            self.calc_text.append("\n=== FACTORES DE AJUSTE ===")
            self.calc_text.append(f"Total factores: {total_fa}")
            self.calc_text.append(f"Promedio FA: {fa_prom:.4f}")
            self.calc_text.append(f"PF Ajustado: {pf_ajustado:.2f}")
            self.calc_text.append(f"Reutilización: {self.reutilizacion.value()}%")
            self.calc_text.append(f"PF Real: {self.pf_real:.2f}")
            
            self.calc_text.append("\n=== CÁLCULO COCOMO ===")
            self.calc_text.append(f"Tipo de proyecto: {tipo}")
            self.calc_text.append(f"Coeficientes: a={a}, b={b}, c={c}, d={d}")
            self.calc_text.append(f"Esfuerzo = {a} * ({self.pf_real:.2f})^{b:.2f} = {self.esfuerzo:.2f} horas-persona")
            self.calc_text.append(f"Duración = {c} * ({self.esfuerzo:.2f})^{d:.2f} = {self.duracion_semanas:.2f} semanas")
            
            self.calc_text.append("\n=== CÁLCULO DE COSTOS ===")
            self.calc_text.append(f"VE = ({self.sueldo_min.value()} + 4*{self.sueldo_mp.value()} + {self.sueldo_max.value()})/6 = {ve:.2f}")
            self.calc_text.append(f"Costo por PF = {ve:.2f} / {self.productividad.value()} = {costo_pf:.2f}")
            self.calc_text.append(f"Costo total = {costo_pf:.2f} * {self.pf_real:.2f} = ${self.costo:.2f}")
            
            # Actualizar etiquetas de resultados intermedios
            self.pf_nominal_label.setText(f"{self.pf_nominal:.2f}")
            self.fa_prom_label.setText(f"{fa_prom:.4f}")
            self.pf_ajust_label.setText(f"{pf_ajustado:.2f}")
            self.pf_real_label.setText(f"{self.pf_real:.2f}")
            self.tipo_label.setText(tipo)
            self.coef_label.setText(f"a={a}, b={b}, c={c}, d={d}")
            
            # Actualizar resultados finales
            self.esfuerzo_label.setText(f"{self.esfuerzo:.2f} horas-persona")
            self.duracion_label.setText(f"{self.duracion_semanas:.2f} semanas ({duracion_meses:.1f} meses)")
            self.costo_label.setText(f"${self.costo:,.2f}")
            self.costo_pf_label.setText(f"${costo_pf:.2f}")
            
            # Crear analogía de Minecraft
            self.create_minecraft_analogy(tipo_index, self.pf_real, self.esfuerzo, duracion_meses, self.costo)
            
            # Crear resumen
            self.create_summary()
            
            # Cambiar a pestaña de cálculos
            self.tabs.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "Error de cálculo", f"Ocurrió un error durante los cálculos:\n{str(e)}")
    
    def create_minecraft_analogy(self, tipo, pf_real, esfuerzo, duracion_meses, costo):
        analogy_text = ""
        
        if tipo == 0:  # Orgánico
            analogy_text = (
                "🏠 Proyecto: Cabaña de Madera (Orgánico)\n\n"
                f"🔨 Bloques necesarios: {int(pf_real)} bloques\n"
                f"⏱️ Tiempo estimado: {int(esfuerzo/10)} minutos de juego\n"
                f"📅 Duración: {duracion_meses:.1f} meses (equivalente a {int(duracion_meses*4)} sesiones de Minecraft)\n\n"
                "Recursos necesarios:\n"
                "- Madera: 5 stacks\n"
                "- Piedra: 2 stacks\n"
                "- Cristal: 1 stack\n"
                "- Puertas y trampillas: 10 unidades\n\n"
                f"💎 Costo en esmeraldas: {int(costo/100)} esmeraldas\n"
                "👍 Dificultad: Fácil - Ideal para principiantes"
            )
        elif tipo == 1:  # Semi-acoplado
            analogy_text = (
                "🏰 Proyecto: Castillo Medieval (Semi-Acoplado)\n\n"
                f"🔨 Bloques necesarios: {int(pf_real)} bloques\n"
                f"⏱️ Tiempo estimado: {int(esfuerzo/8)} minutos de juego\n"
                f"📅 Duración: {duracion_meses:.1f} meses (equivalente a {int(duracion_meses*4)} sesiones de Minecraft)\n\n"
                "Recursos necesarios:\n"
                "- Piedra: 20 stacks\n"
                "- Madera oscura: 10 stacks\n"
                "- Hierro: 5 stacks\n"
                "- Redstone: 2 stacks\n"
                "- Antorchas: 1 stack\n\n"
                f"💎 Costo en esmeraldas: {int(costo/100)} esmeraldas\n"
                "👍 Dificultad: Media - Requiere planificación"
            )
        else:  # Empotrado
            analogy_text = (
                "🌌 Proyecto: Ciudad Flotante con Granjas (Empotrado)\n\n"
                f"🔨 Bloques necesarios: {int(pf_real)} bloques\n"
                f"⏱️ Tiempo estimado: {int(esfuerzo/5)} minutos de juego\n"
                f"📅 Duración: {duracion_meses:.1f} meses (equivalente a {int(duracion_meses*4)} sesiones de Minecraft)\n\n"
                "Recursos necesarios:\n"
                "- Obsidiana: 30 stacks\n"
                "- Cristal: 20 stacks\n"
                "- Redstone: 10 stacks\n"
                "- Slime blocks: 5 stacks\n"
                "- Mods avanzados: 3\n\n"
                f"💎 Costo en esmeraldas: {int(costo/100)} esmeraldas\n"
                "👍 Dificultad: Difícil - Solo para expertos"
            )
        
        self.mc_analogy.setText(analogy_text)
    
    def create_summary(self):
        summary = (
            "RESUMEN DEL PROYECTO\n\n"
            f"Tipo de proyecto: {self.tipo_proyecto.currentText()}\n"
            f"Puntos de Función Nominales: {self.pf_nominal:.2f}\n"
            f"Puntos de Función Reales: {self.pf_real:.2f}\n"
            f"Esfuerzo estimado: {self.esfuerzo:.2f} horas-persona\n"
            f"Duración estimada: {self.duracion_semanas:.2f} semanas\n"
            f"Costo total estimado: ${self.costo:,.2f}\n\n"
            "RECOMENDACIONES:\n"
        )
        
        if self.tipo_proyecto.currentIndex() == 0:
            summary += (
                "- Este proyecto es relativamente simple\n"
                "- Se recomienda un equipo pequeño (2-3 personas)\n"
                "- El riesgo es bajo, se puede completar fácilmente"
            )
        elif self.tipo_proyecto.currentIndex() == 1:
            summary += (
                "- Este proyecto tiene complejidad media\n"
                "- Se recomienda un equipo de 4-6 personas\n"
                "- Es importante realizar revisiones periódicas\n"
                "- Asignar recursos adicionales para partes complejas"
            )
        else:
            summary += (
                "- Este proyecto es altamente complejo\n"
                "- Se requiere un equipo experimentado de 7+ personas\n"
                "- Implementar metodologías ágiles con sprints cortos\n"
                "- Realizar prototipos para partes críticas\n"
                "- Asignar un 20% adicional para imprevistos"
            )
        
        self.summary_text.setText(summary)
    
    def restart(self):
        # Resetear valores
        self.entradas.setValue(12)
        self.salidas.setValue(14)
        self.peticiones.setValue(11)
        self.archivos.setValue(16)
        self.interfaces.setValue(0)
        
        for spinbox in self.fa_values:
            spinbox.setValue(4 if self.fa_values.index(spinbox) < 4 else 3)
        
        self.tipo_proyecto.setCurrentIndex(1)
        self.reutilizacion.setValue(35)
        self.productividad.setValue(2)
        self.sueldo_min.setValue(3500)
        self.sueldo_mp.setValue(6500)
        self.sueldo_max.setValue(7000)
        
        # Regresar a la primera pestaña
        self.tabs.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Estilo para la aplicación
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F5F5F5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #BDBDBD;
            border-radius: 5px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        QTextEdit {
            background-color: white;
            border: 1px solid #BDBDBD;
            border-radius: 3px;
        }
        QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: white;
            border: 1px solid #BDBDBD;
            border-radius: 3px;
            padding: 2px;
        }
    """)
    
    window = MinecraftCOCOMOApp()
    window.showMaximized()
    sys.exit(app.exec_())