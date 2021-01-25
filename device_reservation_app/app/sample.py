l = []
d = {"one": [(1,3),(1,4)], "two": [(1,2),(1,2),(1,3)], "three": [(1,1)]}
for k in sorted(d, key=lambda k: len(d[k]), reverse=False):
    l.append(k)
print(l)