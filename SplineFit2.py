import numpy as np
import matplotlib.pyplot as plt

import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.signal import wiener, filtfilt, butter, gaussian, freqz
from scipy.ndimage import filters
import scipy.optimize as op
import matplotlib.pyplot as plt


n = 100
x = np.linspace(0,100,n)
y = np.exp(0.05*x)
y_noise = y+  np.random.normal(scale=1,size=n)
plt.plot(x,y,label = 'actual')
plt.plot(x,y_noise,'o',label= "actual + noise")
plt.legend()
plt.show()

sigma = 3.0
b = gaussian(39, sigma)
plt.plot(b,label="Gaussian B sigma={}".format(sigma))
plt.legend()
plt.show()

average = filters.convolve1d(y_noise, b/b.sum())
plt.plot(x,y,label="Actual")
plt.plot(x,y_noise,'o', label= "Actual + noise")
plt.plot(x,average,label="smoothed")
plt.legend()
plt.show()

var = filters.convolve1d(np.power(y_noise-average,2), b/b.sum())
plt.plot(x,y,label="Actual")
plt.plot(x,y_noise,'o', label= "Actual + noise")
plt.plot(x,var,label="varience")
plt.legend()
plt.show()

sp = UnivariateSpline(x, y_noise, w=1/np.sqrt(var))
plt.plot(x,y,label="Actual")
plt.plot(x,y_noise,'o', label= "Actual + noise")
plt.plot(x,sp(x),label="spline")
plt.legend()
plt.show()

plt.plot(np.linspace(0,100,10000),sp(np.linspace(0,100,10000)),label="Spline")
plt.plot(x,y,label="Actual")
plt.legend()
plt.show()

plt.plot(x,sp.derivative()(x))
plt.plot(x,0.05*np.exp(0.05*x))
plt.show()
