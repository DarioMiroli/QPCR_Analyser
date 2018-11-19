import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
from scipy.optimize import minimize
from scipy.optimize import differential_evolution
import random

seed =1
x = np.linspace(0,12,20)
x0 = 6
L = 1
k = 1.5
y = L/(1+np.exp(-k*(x-x0)))
np.random.seed(seed)
y_noise = y + np.random.normal(scale=0.01,size=len(x))

#plt.plot(x,y,label="Actual")
#plt.plot(x,y_noise,"o",label="Noise")
#plt.legend()
#plt.show()

def getError(xTest,yTest,xVal,yVal,s):
    #print(s)
    sp = UnivariateSpline(xTest, yTest,s=s)
    testError = (np.mean(np.power((sp(xTest) - yTest),2)))
    validateError = (np.mean(np.power((sp(xVal) - yVal),2)))
    return validateError

def getFit(x,y,s):
    #print(s)
    testFraction = 0.5
    random.seed(seed)
    error = 0
    for i in range(10):
        testIndexes = random.sample([i for i in range(len(x))],int(len(x)*testFraction))
        testIndexes.sort()
        validateIndexes = [i for i in range(len(x)) if i not in testIndexes]
        validateIndexes.sort()
        xTest = x[testIndexes]
        yTest = y_noise[testIndexes]
        xVal = x[validateIndexes]
        yVal = y_noise[validateIndexes]
        error += getError(xTest,yTest,xVal,yVal,s)
    return error
        #plt.plot(xTest,yTest,'o',label="test")
        #plt.plot(xVal,yVal,'*',label="val")
        #plt.legend()
        #plt.show()

valErrors = []
ss = np.linspace(0.0001,0.5,100)
for s in ss:
    valErrors.append(getFit(x,y_noise,s))

plt.plot(ss,valErrors,label="Val")
plt.legend()
plt.show()

bestS = ss[valErrors.index(min(valErrors))]
sp = UnivariateSpline(x, y_noise,s=bestS)

#m = minimize(lambda s : getError(xTest,yTest,xVal,yVal,s),x0=0.25,tol=0.00001, method='nelder-mead')
m = differential_evolution(lambda s : getFit(x,y_noise,s), bounds = [(0,1)],tol=0.0001)
fitS = m.x
spFit =  UnivariateSpline(x, y_noise,s=fitS)
plt.plot(x,y,label="True")
plt.plot(x,y_noise,'o',label='Data')
plt.plot(x,sp(x),label="Spline {}".format(bestS))
plt.plot(x,spFit(x),label="fit spline {}".format(fitS))
plt.legend()
plt.show()
