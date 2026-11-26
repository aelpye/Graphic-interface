import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QMessageBox, QFrame)
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt

# Интеграция с matplotlib 
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Импорт твоего модуля 
from fastq_parser import FastqParser, plot_per_base_quality, plot_per_base_content, plot_length_distribution

# Палитра 
BG        = "#1A1512"   
PANEL_BG  = "#2A2119"   
CREAM     = "#F5E6A8"   
BTN_DARK  = "#4A3B2F"   
BTN_HOVER = "#5C4A3D"   
BTN_LIGHT = "#F5E6A8"   

# Настройка шрифта для графиков
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']

class FastqWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Урезанный FastQC — Анализ качества")
        self.resize(1100, 850)
        self.setStyleSheet(f"background-color: {BG}; color: {CREAM};")
        self.setAcceptDrops(True) # Включаем Drag-and-Drop

        self.current_file = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Верхняя панель: Заголовок и кнопки 
        top_panel = QHBoxLayout()
        
        title = QLabel("FastQC Viewer")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        top_panel.addWidget(title)
        
        top_panel.addStretch()

        self.btn_open = QPushButton("Выбрать FASTQ файл")
        self.btn_open.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_open.setStyleSheet(f"""
            QPushButton {{ background-color: {BTN_LIGHT}; color: {BG}; padding: 10px 20px; border-radius: 6px; }}
            QPushButton:hover {{ background-color: #FFEAA0; }}
        """)
        self.btn_open.clicked.connect(self.open_file_dialog)
        top_panel.addWidget(self.btn_open)

        layout.addLayout(top_panel)

        # Статус (куда перетаскивать файл)         
        self.status_label = QLabel("Перетащите файл сюда или нажмите кнопку")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {PANEL_BG};
                border: 2px dashed {CREAM};
                border-radius: 10px;
                padding: 30px;
                color: {CREAM};
            }}
        """)
        layout.addWidget(self.status_label)

        # Место для графиков
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.figure.patch.set_facecolor(BG)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.hide() # Скрываем, пока файл не загружен
        layout.addWidget(self.canvas)

    
    # Логика Drag-and-Drop
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.status_label.setStyleSheet(f"QLabel {{ background-color: {BTN_DARK}; border: 2px dashed {BTN_LIGHT}; border-radius: 10px; padding: 30px; color: {CREAM}; }}")

    def dragLeaveEvent(self, event):
        self.status_label.setStyleSheet(f"QLabel {{ background-color: {PANEL_BG}; border: 2px dashed {CREAM}; border-radius: 10px; padding: 30px; color: {CREAM}; }}")

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.process_file(files[0])
        self.dragLeaveEvent(event)

    
    # Обработка файла
    
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл FASTQ", "", 
            "FASTQ Files (*.fastq *.fq *.fastq.gz *.fq.gz);;All Files (*)"
        )
        if file_path:
            self.process_file(file_path)

    def process_file(self, path):
        if not (path.endswith(".fastq") or path.endswith(".fq") or path.endswith(".gz")):
            QMessageBox.warning(self, "Ошибка", "Выберите файл формата .fastq, .fq или .gz")
            return

        self.current_file = path
        self.status_label.setText(f"Загрузка файла:\n{os.path.basename(path)}...")
        QApplication.processEvents() # Обновляем интерфейс, пока идет чтение

        # Проверяем, сжат ли файл
        compressed = path.endswith(".gz")

        try:
            # Создаем фабрику парсеров (как в твоем коде, каждый график требует новый парсер)
            def parser_factory():
                return FastqParser(path, compressed=compressed)

            # Отрисовка графиков
            self.figure.clear()
            
            # Настраиваем 3 графика в столбик
            ax1 = self.figure.add_subplot(311)
            ax2 = self.figure.add_subplot(312)
            ax3 = self.figure.add_subplot(313)
            
            # Стилизация осей под нашу темную тему
            for ax in [ax1, ax2, ax3]:
                ax.set_facecolor(PANEL_BG)
                ax.tick_params(colors=CREAM, labelsize=9)
                for spine in ax.spines.values():
                    spine.set_color(CREAM)
                ax.title.set_color(CREAM)
                ax.xaxis.label.set_color(CREAM)
                ax.yaxis.label.set_color(CREAM)
                ax.legend(facecolor=PANEL_BG, edgecolor=CREAM, labelcolor=CREAM)
                ax.grid(color=CREAM, alpha=0.1)

            # Вызываем твои функции для отрисовки на конкретных осях (ax)
            plot_per_base_quality(parser_factory(), ax=ax1)
            plot_per_base_content(parser_factory(), ax=ax2)
            plot_length_distribution(parser_factory(), ax=ax3)

            self.figure.tight_layout()
            self.canvas.draw()
            
            # Прячем статусную панель и показываем графики
            self.status_label.hide()
            self.canvas.show()

        except Exception as e:
            self.status_label.show()
            self.canvas.hide()
            self.status_label.setText("Ошибка при чтении файла.\nПеретащите другой файл.")
            QMessageBox.critical(self, "Ошибка парсинга", f"Не удалось прочитать файл:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 11))
    window = FastqWindow()
    window.show()
    sys.exit(app.exec())