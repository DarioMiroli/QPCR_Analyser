import numpy as np
import matplotlib.pyplot as plt

expoFits = [117.4,115.0,103.76,102.96,104.6,104.12,110.4,111.4,113.6,109.96,107.2,-1,111.2,111.2,107.6,107.4]
diluts = [116.0,111.9,76.89,71.99,98.19,102.6,100.9,100.7,99.21,100.1,98.37,-1,98.69,96.71,97.33,97.35]




x = [i for i in expoFits if i != -1 ]
y = [i for i in diluts if i != -1 ]
plt.plot(x,y,'o')
plt.show()


x = []
y = []
for i in range(0,len(expoFits),2):
    if expoFits[i+1] != -1:
        x.append(expoFits[i])
        y.append(expoFits[i+1])
plt.plot(x,y,'o')
plt.show()

x = []
y = []
for i in range(0,len(expoFits),2):
    if diluts[i+1] != -1:
        x.append(diluts[i])
        y.append(diluts[i+1])
plt.plot(x,y,'o')
plt.show()
