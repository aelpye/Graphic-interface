import tkinter as tk
from tkinter import messagebox
import math

root = tk.Tk()
root.title("Калькулятор")
root.geometry("300x480")
root.configure(bg="#2B2B2B")
root.resizable(False, False)

# Цвета
BG        = "#2B2B2B"   # фон окна (графит)
NUM_BG    = "#444444"   # цифры
NUM_ACT   = "#5A5A5A"   # цифры при нажатии
OP_BG     = "#F5E6A8"   # операции — сливочно-жёлтый
OP_ACT    = "#FFEAA0"   # операции при нажатии
EQ_BG     = "#3E3A36"   # = — нейтральный шоколад
EQ_ACT    = "#4C4844"   # = при нажатии
GREY_BG   = "#5A5A5A"   # C, скобки
GREY_ACT  = "#6E6E6E"   # C, скобки при нажатии
CREAM     = "#F5E6A8"   # сливочный текст
DARK      = "#2B2B2B"   # тёмный текст на жёлтом

# Валидация ввода 
def is_valid(new_text):
    """Разрешаем только цифры, точку, операции, скобки и √."""
    if new_text == "":
        return True
    allowed = "0123456789.+-×÷()√"
    for ch in new_text:
        if ch not in allowed:
            return False
    if new_text.count(".") > 1:
        return False
    return True

vcmd = (root.register(is_valid), "%P")

entry = tk.Entry(
    root, font=("Segoe UI", 28), bg=BG, fg=CREAM,
    bd=0, justify="right", insertbackground=CREAM,
    validate="key", validatecommand=vcmd
)
entry.grid(row=0, column=0, columnspan=4, padx=15, pady=20, sticky="we")

# Вычисление 
def compute(expr):
    """Переводим × ÷ в * /, √x в число и считаем через eval."""
    expr = expr.replace("×", "*").replace("÷", "/")
    while "√" in expr:
        i = expr.index("√")
        j = i + 1
        num = ""
        while j < len(expr) and (expr[j].isdigit() or expr[j] == "."):
            num += expr[j]
            j += 1
        if num == "":
            raise ValueError("После √ должно быть число")
        value = float(num)
        if value < 0:
            raise ValueError("Корень из отрицательного числа")
        expr = expr[:i] + str(math.sqrt(value)) + expr[j:]
    return eval(expr)

# Нажатие кнопок 
def press(key):
    if key == "C":
        entry.delete(0, tk.END)
    elif key == "=":
        text = entry.get()
        if text == "":
            return
        try:
            res = compute(text)
            entry.delete(0, tk.END)
            if res == int(res):
                entry.insert(0, str(int(res)))
            else:
                entry.insert(0, str(res))
        except ZeroDivisionError:
            messagebox.showerror("Ошибка", "Деление на ноль!")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception:
            messagebox.showerror("Ошибка", "Некорректное выражение")
    else:
        entry.insert(tk.END, key)

# Кнопки: 5 рядов по 4 
buttons = [
    "C",  "(",  ")",  "√",
    "7",  "8",  "9",  "÷",
    "4",  "5",  "6",  "×",
    "1",  "2",  "3",  "-",
    "0",  ".",  "=",  "+",
]

row, col = 1, 0
for b in buttons:
    if b in "÷×-+√":
        bg, act, fg = OP_BG, OP_ACT, DARK
    elif b == "=":
        bg, act, fg = EQ_BG, EQ_ACT, CREAM
    elif b in "C()":
        bg, act, fg = GREY_BG, GREY_ACT, CREAM
    else:
        bg, act, fg = NUM_BG, NUM_ACT, CREAM

    btn = tk.Button(
        root, text=b, font=("Segoe UI", 16, "bold"),
        bg=bg, fg=fg, bd=0,
        activebackground=act, activeforeground=fg,
        command=lambda x=b: press(x)
    )
    btn.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

    col += 1
    if col > 3:
        col = 0
        row += 1

for i in range(4):
    root.columnconfigure(i, weight=1)
for i in range(6):
    root.rowconfigure(i, weight=1)

root.bind("<Return>", lambda e: press("="))
root.bind("<Escape>", lambda e: press("C"))

root.mainloop()