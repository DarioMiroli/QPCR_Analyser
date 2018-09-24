import numpy as np
import matplotlib.pyplot as plt

fpath = "./Data/Call1_Rows.txt"
f = open(fpath,encoding='utf-16-le')

data = {}
x = []
for i,line in enumerate(f.readlines()):
    linelist = line.rstrip().split("\t")
    for j, item in enumerate(linelist):
        if j >0:
            if i==0:
                x.append(item)
            else:
                data[key].append(float(item))
        else:
            if i > 0:
                item= item.split(" ")[0]
                data[item] = []
                key = item

keys = ["C1","C2","C3","C4","C5"]
for key in keys:
    plt.plot(x,data[key],label=key)
plt.legend()
plt.show()

for key in keys:
    plt.plot(x,np.log(data[key]),'--o',label=key)
plt.legend()
plt.show()
