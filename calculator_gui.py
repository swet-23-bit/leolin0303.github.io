import tkinter as tk

def on_click(value):
    current = display.get()
    display.delete(0, tk.END)
    display.insert(0, current + value)

def clear_display():
    display.delete(0, tk.END)

def calculate():
    try:
        result = eval(display.get())
        display.delete(0, tk.END)
        display.insert(0, str(result))
    except:
        display.delete(0, tk.END)
        display.insert(0, "Error")

# 建立主視窗
window = tk.Tk()
window.title("SmartCalc - Multi-Function Calculator")
window.geometry("320x400")
window.resizable(False, False)

# 顯示欄
display = tk.Entry(window, font=("Arial", 24), borderwidth=2, relief="solid", justify="right")
display.pack(padx=10, pady=20, ipady=10, fill="x")

# 按鈕設定
buttons = [
    ["7", "8", "9", "/"],
    ["4", "5", "6", "*"],
    ["1", "2", "3", "-"],
    ["0", ".", "(", ")"],
    ["C", "=", "+"]
]

# 建立按鈕區
for row in buttons:
    frame = tk.Frame(window)
    frame.pack(expand=True, fill="both", padx=10, pady=5)
    for btn_text in row:
        btn = tk.Button(frame, text=btn_text, font=("Arial", 18), width=5, height=2)
        if btn_text == "C":
            btn.config(bg="#f44336", fg="white", command=clear_display)
        elif btn_text == "=":
            btn.config(bg="#4caf50", fg="white", command=calculate)
        else:
            btn.config(command=lambda val=btn_text: on_click(val))
        btn.pack(side="left", expand=True, fill="both", padx=5)

# 啟動主迴圈
window.mainloop()

