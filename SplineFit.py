import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.optimize import minimize
from scipy.optimize import basinhopping
from scipy.optimize import differential_evolution
import random

def getFit(x,y,s):
    error = 0
    for i in range(len(x)**2):
        indexes1 = []
        indexes2 = []
        #np.random.seed(1)
        for i in range(len(x)):
            if np.random.random() > 0.5:
                indexes1.append(i)
            else:
                indexes2.append(i)
        tck1 = interpolate.splrep(x[indexes1], y[indexes1],s=s)
        prediction1 = interpolate.splev(x[indexes2], tck1, der=0)

        tck2 = interpolate.splrep(x[indexes2], y[indexes2],s=s)
        prediction2 = interpolate.splev(x[indexes1], tck2, der=0)

        error += np.mean(np.abs(prediction1-y[indexes2]))/2.0
        error += np.mean(np.abs(prediction2-y[indexes1]))/2.0
    print(s)
    return error


if __name__ == "__main__":

    x = np.linspace(0,8,50)
    x = x + 0.04*(2*np.random.random(len(x)) - 1)
    y = np.exp(x) + 200*(2*np.random.random(len(x))-1)
    errors = []
    ss = []
    for s in np.linspace(0,1E6,100):
        errors.append(getFit(x,y,s))
        ss.append(s)
    plt.plot(ss,errors,label= np.linspace(0,1E6,1000)[errors.index(min(errors))])
    plt.legend()
    plt.show()

    #m = minimize(lambda s : getFit(x,y,s),x0=5000,tol=0.1, method='nelder-mead')
    m = differential_evolution(lambda s : getFit(x,y,s), bounds = [(1,1E6)],tol=0.1)
    fitS = m.x
    tck = interpolate.splrep(x, y,s=fitS)
    predictedY = interpolate.splev(x, tck, der=0)
    plt.plot(x,predictedY)
    plt.plot(x,y,'*',label=fitS)
    plt.legend()
    plt.show()


    #getFit(x,y,1000000)
