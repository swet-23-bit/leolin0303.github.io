def f(m):
    l = []
    for i in range(m + 1):
        if i == 0:
            l.append(0)
        elif i == 1:
            l.append(1)
        else:
            l.append(l[i-1] + l[i-2])
    return l[-1]

num = int(input("請輸入數字："))
print(f(num))
print(m)