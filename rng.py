import random

a = int(input("enter min"))
b = int(input("enter max"))
c = int(input("enter n"))

for i in range(c): print(random.randint(a, b))