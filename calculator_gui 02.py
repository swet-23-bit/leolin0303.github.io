import tkinter as tk
import math

# ----- 計算功能 -----
def on_click(value):
    if value in ["π", "e", "^", "√", "log", "ln", "sin", "cos", "tan"]:
        value = {
            "π": str(math.pi),
            "e": str(math.e),
            "^": "**",
            "√": "math.sqrt(",
            "log": "math.log10(",
            "ln": "math.log(",
            "sin": "math.sin(math.radians(",
            "cos": "math.cos(math.radians(",
            "tan": "math.tan(math.radians("
        }[value]
    display.insert(tk.END, value)

def clear_display():
    display.delete(0, tk.END)

def calculate(event=None):  # 支援鍵盤按 Enter
    try:
        expr = display.get()
        result = eval(expr)
        display.delete(0, tk.END)
        display.insert(0, str(result))
        add_to_history(f"{expr} = {result}")
    except:
        display.delete(0, tk.END)
        display.insert(0, "Error")

# ----- 歷史紀錄功能 -----
def add_to_history(entry):
    history_list.insert(tk.END, entry)
    history_list.see(tk.END)

def on_history_click(event):
    selected = history_list.curselection()
    if selected:
        expr = history_list.get(selected[0]).split("=")[0].strip()
        display.delete(0, tk.END)
        display.insert(0, expr)

# ----- 主視窗 -----
window = tk.Tk()
window.title("SmartCalc - Dark Mode with History")
window.geometry("700x600")
window.resizable(False, False)
window.configure(bg="#2c2c2c")

# ----- 顯示欄 -----
display = tk.Entry(window, font=("Arial", 24), bg="#1e1e1e", fg="white",
                   insertbackground="white", borderwidth=2, relief="solid", justify="right")
display.pack(padx=10, pady=20, ipady=10, fill="x")
display.focus_set()

# ----- 框架分區 -----
main_frame = tk.Frame(window, bg="#2c2c2c")
main_frame.pack(fill="both", expand=True)

button_frame = tk.Frame(main_frame, bg="#2c2c2c")
button_frame.pack(side="left", padx=10, expand=True)

# ----- 按鈕配置 -----
buttons = [
    ["7", "8", "9", "/", "π"],
    ["4", "5", "6", "*", "^"],
    ["1", "2", "3", "-", "√"],
    ["0", ".", "(", ")", "+"],
    ["e", "log", "ln", "C", "="],
    ["sin", "cos", "tan"]# ✅ 新增括號列


]

for row in buttons:
    row_frame = tk.Frame(button_frame, bg="#2c2c2c")
    row_frame.pack(expand=True, fill="both", pady=5)
    for btn_text in row:
        btn = tk.Button(
            row_frame, text=btn_text, font=("Arial", 18),
            bg="#3a3a3a", fg="white", activebackground="#555",
            width=5, height=2, borderwidth=0
        )
        if btn_text == "C":
            btn.config(bg="#d32f2f", command=clear_display)
        elif btn_text == "=":
            btn.config(bg="#f57c00", command=calculate)
        else:
            btn.config(command=lambda val=btn_text: on_click(val))
        btn.pack(side="left", expand=True, fill="both", padx=3)

# ----- 歷史紀錄面板 -----
history_frame = tk.Frame(main_frame, bg="#1e1e1e", width=200)
history_frame.pack(side="right", fill="y", padx=5, pady=5)

tk.Label(history_frame, text="History", font=("Arial", 16),
         bg="#1e1e1e", fg="white").pack(pady=5)

history_list = tk.Listbox(history_frame, font=("Arial", 12),
                          bg="#2c2c2c", fg="white", height=25,
                          selectbackground="#444")
history_list.pack(side="left", fill="both", expand=True, padx=5)
history_list.bind("<<ListboxSelect>>", on_history_click)

# ----- 鍵盤綁定 -----
window.bind("<Return>", calculate)
window.bind("<Escape>", lambda event: clear_display())

# ----- 執行主程式 -----
window.mainloop()

