def check__year(year):
    if(year% 400 == 0)or(year % 4 == 0and year % 100 != 0)
                         return'閏年'
                        else:
                         return'平年'
print(int(input())))