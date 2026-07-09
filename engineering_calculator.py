import tkinter as tk
import math

class EngineeringCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("工程計算機")

        self.entry = tk.Entry(root, width=30, font=('Arial', 18), borderwidth=5, relief="ridge")
        self.entry.grid(row=0, column=0, columnspan=5)

        self.create_buttons()

    def create_buttons(self):
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3), ('√', 1, 4),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3), ('^', 2, 4),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3), ('(', 3, 4),
            ('0', 4, 0), ('.', 4, 1), ('+', 4, 2), (')', 4, 3), ('C', 4, 4),
            ('sin', 5, 0), ('cos', 5, 1), ('tan', 5, 2), ('π', 5, 3), ('e', 5, 4),
            ('=', 6, 0, 5)
        ]

        for (text, row, col, colspan) in [b if len(b) == 4 else (*b, 1) for b in buttons]:
            tk.Button(self.root, text=text, width=6, height=2,
                      command=lambda t=text: self.on_click(t))\
                      .grid(row=row, column=col, columnspan=colspan, sticky="nsew")

    def on_click(self, key):
        if key == 'C':
            self.entry.delete(0, tk.END)
        elif key == '=':
            self.calculate()
        elif key == 'π':
            self.entry.insert(tk.END, str(math.pi))
        elif key == 'e':
            self.entry.insert(tk.END, str(math.e))
        elif key == '√':
            self.entry.insert(tk.END, 'math.sqrt(')
        elif key == '^':
            self.entry.insert(tk.END, '**')
        elif key in ('sin', 'cos', 'tan'):
            self.entry.insert(tk.END, f'math.{key}(math.radians(')
        else:
            self.entry.insert(tk.END, key)

    def calculate(self):
        try:
            expression = self.entry.get()
            result = eval(expression)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, str(result))
        except Exception as e:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, "錯誤")

if __name__ == "__main__":
    root = tk.Tk()
    calc = EngineeringCalculator(root)
    root.mainloop()

