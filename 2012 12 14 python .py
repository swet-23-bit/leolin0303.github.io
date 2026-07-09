a = [1,2,3]
b = [2,3,1]
c = [1,2,3]
print(a == b)
print(a == c)

x = {'A':1,'B':2,'C':3}
y = {'B':2,'C':3,'A':1}
z = {'A':1,'B':2,'C':3}
print(x == y)
capitals = {'Taiwan':'Taipei','USA':'華盛頓','土耳其':'新德里','Japan':'東京','China':'北京'}
print(len('capitals'))
print(len(capitals.keys()))

d = {'name':'Rebel Wilson','year':1980}
for value in d.values():
    print(value)