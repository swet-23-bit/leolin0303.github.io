def calculator():
    print("歡迎使用基本四則運算計算機")
    num1 = float(input("請輸入第一個數字："))
    op = input("請輸入運算符號（+ - * /）：")
    num2 = float(input("請輸入第二個數字："))

    if op == "+":
        result = num1 + num2
    elif op == "-":
        result = num1 - num2
    elif op == "*":
        result = num1 * num2
    elif op == "/":
        if num2 != 0:
            result = num1 / num2
        else:
            result = "錯誤：不能除以零"
    else:
        result = "無效的運算符號"

    print("結果是：", result)

calculator()
