h = 10
for i in range(1, h + 1):
    print(" " * (h - i) + "*" * (2 * i - 1))
for i in range(2):
    print("*" * (h * 2 - 1))
print("   *****")
for i in range(h - 1, 0, -1):
    print(" " * (h - i) + "*" * (2 * i - 1))