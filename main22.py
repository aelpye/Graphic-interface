import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QDialog, QLineEdit, QComboBox, QMessageBox, QHeaderView,
                             QFormLayout, QFrame)
from PyQt6.QtGui import QFont, QRegularExpressionValidator, QColor
from PyQt6.QtCore import Qt, QRegularExpression

# --- Импорты для графиков ---
import matplotlib
matplotlib.use('QtAgg') # Интеграция с PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

FILE = "patients.json"

# Цветовая палитра
BG        = "#1A1512"   # Фон
PANEL_BG  = "#2A2119"   # Панели
NUM_BG    = "#3A2E24"   # Поля ввода
CREAM     = "#F5E6A8"   # Текст
BTN_DARK  = "#4A3B2F"   # Шоколадные кнопки
BTN_HOVER = "#5C4A3D"   
BTN_LIGHT = "#F5E6A8"   
ERROR_RED = "#e06c75"

# Настройка шрифта для графиков (чтобы кириллица не превращалась в квадраты)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False




# Класс для отрисовки графиков

class StatsWindow(QWidget):
    def __init__(self, patients):
        super().__init__()
        self.setWindowTitle("Сводная статистика")
        self.resize(1000, 800)
        self.setStyleSheet(f"background-color: {BG};")
        
        layout = QVBoxLayout(self)
        
        # Создаем фигуру matplotlib
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.figure.patch.set_facecolor(BG) # Цвет фона фигуры
        
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.draw_plots(patients)

    def draw_plots(self, patients):
        self.figure.clear()
        
        # Разбиваем на 4 графика (сетка 2x2)
        ax1 = self.figure.add_subplot(221)
        ax2 = self.figure.add_subplot(222)
        ax3 = self.figure.add_subplot(223)
        ax4 = self.figure.add_subplot(224)
        
        # Общий стиль для всех графиков
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor(PANEL_BG)
            ax.tick_params(colors=CREAM, labelsize=9)
            ax.spines['bottom'].set_color(CREAM)
            ax.spines['top'].set_color(CREAM) 
            ax.spines['right'].set_color(CREAM)
            ax.spines['left'].set_color(CREAM)
            ax.title.set_color(CREAM)
            ax.xaxis.label.set_color(CREAM)
            ax.yaxis.label.set_color(CREAM)

        # Если нет данных, выводим заглушку
        if not patients:
            ax1.text(0.5, 0.5, "Нет данных для статистики", 
                     ha='center', va='center', color=CREAM, fontsize=14)
            self.canvas.draw()
            return

        # 1. Распределение по полу
        sexes = [p["sex"] for p in patients]
        counts = [sexes.count("М"), sexes.count("Ж"), sexes.count("X")]
        labels = ["М", "Ж", "X"]
        colors = [BTN_LIGHT, BTN_DARK, "#6B5A4B"]
        
        # Фильтруем нулевые значения для круговой диаграммы
        filtered = [(l, c, col) for l, c, col in zip(labels, counts, colors) if c > 0]
        if filtered:
            l_f, c_f, col_f = zip(*filtered)
            ax1.pie(c_f, labels=l_f, colors=col_f, autopct='%1.0f%%', 
                    textprops={'color': CREAM, 'fontsize': 10})
        ax1.set_title("Распределение по полу")

        # 2. Распределение по возрасту (гистограмма)
        ages = [p["age"] for p in patients]
        ax2.hist(ages, bins=10, color=BTN_LIGHT, edgecolor=PANEL_BG)
        ax2.set_title("Распределение по возрасту")
        ax2.set_xlabel("Возраст, лет")
        ax2.set_ylabel("Количество")
        ax2.grid(axis='y', color=CREAM, alpha=0.2)

        # 3. Распределение ИМТ с учётом пола
        for sex, color, label in [("М", BTN_LIGHT, "Мужчины"), ("Ж", BTN_DARK, "Женщины")]:
            bmis = [p["weight"] / (p["height"]/100)**2 for p in patients if p["sex"] == sex]
            if bmis:
                ax3.hist(bmis, bins=10, alpha=0.7, color=color, label=label, edgecolor=PANEL_BG)
        ax3.set_title("Распределение ИМТ по полу")
        ax3.set_xlabel("ИМТ")
        ax3.set_ylabel("Количество")
        ax3.legend(facecolor=PANEL_BG, edgecolor=CREAM, labelcolor=CREAM)

        # 4. Зависимость ИМТ от возраста
        m_ages = [p["age"] for p in patients if p["sex"] == "М"]
        m_bmis = [p["weight"] / (p["height"]/100)**2 for p in patients if p["sex"] == "М"]
        f_ages = [p["age"] for p in patients if p["sex"] == "Ж"]
        f_bmis = [p["weight"] / (p["height"]/100)**2 for p in patients if p["sex"] == "Ж"]
        
        ax4.scatter(m_ages, m_bmis, color=BTN_LIGHT, label="М", s=50)
        ax4.scatter(f_ages, f_bmis, color=BTN_DARK, label="Ж", s=50)
        ax4.set_title("Зависимость ИМТ от возраста")
        ax4.set_xlabel("Возраст, лет")
        ax4.set_ylabel("ИМТ")
        ax4.legend(facecolor=PANEL_BG, edgecolor=CREAM, labelcolor=CREAM)
        ax4.grid(color=CREAM, alpha=0.2)

        self.figure.tight_layout()
        self.canvas.draw()



# Диалог добавления/редактирования

class Dialog(QDialog):
    def __init__(self, parent=None, patient=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить" if patient is None else "Редактировать")
        self.setFixedSize(420, 550)
        self.setStyleSheet(f"background-color: {BG}; color: {CREAM};")
        self.patient_data = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.fields = {
            "surname": QLineEdit(), "name": QLineEdit(), "patronymic": QLineEdit(),
            "age": QLineEdit(), "sex": QComboBox(), "height": QLineEdit(), "weight": QLineEdit(),
        }
        self.fields["sex"].addItems(["М", "Ж", "X"])

        name_validator = QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яЁё\s\-]*$"), self)
        patr_validator = QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яЁё\-]*$"), self)
        digit_validator = QRegularExpressionValidator(QRegularExpression(r"^\d*$"), self)
        weight_validator = QRegularExpressionValidator(QRegularExpression(r"^\d*[\.,]?\d*$"), self)

        self.fields["surname"].setValidator(name_validator)
        self.fields["name"].setValidator(name_validator)
        self.fields["patronymic"].setValidator(patr_validator)
        self.fields["age"].setValidator(digit_validator)
        self.fields["height"].setValidator(digit_validator)
        self.fields["weight"].setValidator(weight_validator)

        input_style = f"""
            QLineEdit, QComboBox {{
                background-color: {NUM_BG}; color: {CREAM}; 
                border: 1px solid #555; padding: 6px; border-radius: 4px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background-color: {NUM_BG}; color: {CREAM}; }}
        """
        for w in self.fields.values():
            w.setStyleSheet(input_style)
            w.setFont(QFont("Arial", 11))

        form.addRow("Фамилия *:", self.fields["surname"])
        form.addRow("Имя *:", self.fields["name"])
        form.addRow("Отчество:", self.fields["patronymic"])
        form.addRow("Возраст *:", self.fields["age"])
        form.addRow("Пол *:", self.fields["sex"])
        form.addRow("Рост (см) *:", self.fields["height"])
        form.addRow("Вес (кг) *:", self.fields["weight"])
        
        layout.addLayout(form)
        layout.addSpacing(10)

        self.bmi_label = QLabel("ИМТ: —")
        self.bmi_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.bmi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.bmi_label)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {ERROR_RED};")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        layout.addStretch()

        if patient:
            self.fields["surname"].setText(patient["surname"])
            self.fields["name"].setText(patient["name"])
            self.fields["patronymic"].setText(patient.get("patronymic", ""))
            self.fields["age"].setText(str(patient["age"]))
            self.fields["sex"].setCurrentText(patient["sex"])
            self.fields["height"].setText(str(patient["height"]))
            self.fields["weight"].setText(str(patient["weight"]))
            self.update_bmi()

        self.fields["height"].textChanged.connect(self.update_bmi)
        self.fields["weight"].textChanged.connect(self.update_bmi)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.setStyleSheet(f"""
            QPushButton {{ background-color: {BTN_LIGHT}; color: {BG}; font-weight: bold; padding: 10px; border-radius: 6px; }}
            QPushButton:hover {{ background-color: #FFEAA0; }}
        """)
        btn_save.clicked.connect(self.submit)
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{ background-color: {PANEL_BG}; color: {CREAM}; padding: 10px; border-radius: 6px; }}
            QPushButton:hover {{ background-color: {BTN_DARK}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def update_bmi(self):
        try:
            h = float(self.fields["height"].text())
            w = float(self.fields["weight"].text().replace(",", "."))
            if h > 0:
                v = w / (h / 100) ** 2
                self.bmi_label.setText(f"ИМТ: {v:.1f}")
                return
        except ValueError:
            pass
        self.bmi_label.setText("ИМТ: —")

    def submit(self):
        surname = self.fields["surname"].text().strip()
        name = self.fields["name"].text().strip()
        patr = self.fields["patronymic"].text().strip()
        age_s = self.fields["age"].text().strip()
        sex = self.fields["sex"].currentText()
        height_s = self.fields["height"].text().strip()
        weight_s = self.fields["weight"].text().strip().replace(",", ".")

        if not surname or not name: return self.show_error("Фамилия и имя обязательны")
        if not age_s or not (0 <= int(age_s) <= 125): return self.show_error("Возраст: 0–125")
        if not height_s or not (30 <= int(height_s) <= 275): return self.show_error("Рост: 30–275")
        try:
            weight = float(weight_s)
            if not (1 <= weight <= 640): raise ValueError
        except ValueError:
            return self.show_error("Вес: 1–640")

        self.patient_data = {
            "surname": surname, "name": name, "patronymic": patr,
            "age": int(age_s), "sex": sex, "height": int(height_s), "weight": weight,
        }
        self.accept()

    def show_error(self, msg):
        self.error_label.setText(msg)


# Главное окно

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Пациенты — учёт и отчёт")
        self.resize(1100, 650)
        self.setStyleSheet(f"background-color: {BG}; color: {CREAM};")

        self.patients = []
        self.load_data()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Левая панель
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {PANEL_BG};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 30, 15, 15)

        title = QLabel("Действия")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(20)

        sidebar_layout.addWidget(self.create_button("Добавить", self.add_patient, BTN_LIGHT, BG))
        sidebar_layout.addWidget(self.create_button("Редактировать", self.edit_patient))
        sidebar_layout.addWidget(self.create_button("Удалить", self.delete_patient))
        sidebar_layout.addWidget(self.create_button("Статистика", self.show_stats, BTN_LIGHT, BG))
        sidebar_layout.addWidget(self.create_button("Сохранить", self.save_data))
        sidebar_layout.addStretch()

        # Правая панель (Таблица)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)

        table_title = QLabel("Список пациентов")
        table_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ФИО", "Возраст", "Пол", "Рост", "Вес", "ИМТ"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {NUM_BG}; color: {CREAM}; border: none;
                gridline-color: {PANEL_BG}; selection-background-color: {BTN_DARK};
                selection-color: {BTN_LIGHT};
            }}
            QHeaderView::section {{
                background-color: {PANEL_BG}; color: {CREAM}; padding: 8px; border: none; font-weight: bold;
            }}
        """)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        right_layout.addWidget(self.table)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(right_panel)

        self.refresh_table()

    def create_button(self, text, cmd, bg=BTN_DARK, fg=CREAM):
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {bg}; color: {fg}; padding: 12px; border-radius: 6px; border: none; }}
            QPushButton:hover {{ background-color: {BTN_HOVER}; color: {CREAM}; }}
        """)
        btn.clicked.connect(cmd)
        return btn

    def load_data(self):
        if os.path.exists(FILE):
            with open(FILE, "r", encoding="utf-8") as f:
                self.patients = json.load(f)

    def save_data(self):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(self.patients, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "Сохранено", "Данные записаны в " + FILE)

    def refresh_table(self):
        self.table.setRowCount(len(self.patients))
        for row, p in enumerate(self.patients):
            full_name = f"{p['surname']} {p['name']} {p.get('patronymic', '')}".strip()
            bmi = p["weight"] / (p["height"]/100)**2
            
            self.table.setItem(row, 0, QTableWidgetItem(full_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(p["age"])))
            self.table.setItem(row, 2, QTableWidgetItem(p["sex"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(p["height"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(p["weight"])))
            self.table.setItem(row, 5, QTableWidgetItem(f"{bmi:.1f}"))
            
            for col in range(6):
                item = self.table.item(row, col)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Arial", 11))

    def add_patient(self):
        dialog = Dialog(self)
        if dialog.exec():
            self.patients.append(dialog.patient_data)
            self.save_data()
            self.refresh_table()

    def edit_patient(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Подсказка", "Выберите пациента в таблице")
            return
        dialog = Dialog(self, self.patients[row])
        if dialog.exec():
            self.patients[row] = dialog.patient_data
            self.save_data()
            self.refresh_table()

    def delete_patient(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Подсказка", "Выберите пациента в таблице")
            return
        reply = QMessageBox.question(self, "Удаление", "Удалить выбранного пациента?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.patients[row]
            self.save_data()
            self.refresh_table()

    def show_stats(self):
        if not self.patients:
            QMessageBox.warning(self, "Внимание", "Сначала добавьте хотя бы одного пациента.")
            return
        # Открываем окно со статистикой (сохраняем ссылку, чтобы окно не закрылось сразу)
        self.stats_window = StatsWindow(self.patients)
        self.stats_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 11))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())