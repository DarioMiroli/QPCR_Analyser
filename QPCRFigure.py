import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
#Parameters
filePath = "Data/Call1_Rows.txt"
cellsToRead = ["G1","G2","G3","G4","G5"]
concentrations = [1/(5**i) for i in range(len(cellsToRead))]
threshold = 1
axisLabelFontSize = 18
tickLabelFontSize = 15
#Create Data Dic
dataDic = {key: [] for key in cellsToRead}
#Read files
dataFile = open(filePath,encoding='utf-16-le')
for line in dataFile.readlines():
    splitLine = line.rstrip().split("\t")
    cell = splitLine[0].split()[0]
    if cell in cellsToRead:
        dataDic[cell] =  np.asarray(splitLine[1:],dtype="float")

#Set up sub figures
fig, ax = plt.subplots(nrows=2, ncols=2,figsize=(14,9))



#Top left plot (Example trace plot )
currentAxis = ax[0][0]
currentAxis.plot(dataDic[cellsToRead[0]])
currentAxis.set_xlabel("Cycle number",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Fluoroescence (A.U)",fontsize=axisLabelFontSize)
currentAxis.set_ylim(-0.1,5)
#Annotate bracketed reigon
currentAxis.fill_between([0,7],[5,5],alpha = 0.1 )
currentAxis.fill_between([7,18],[5,5],alpha = 0.1 )
currentAxis.fill_between([18,39],[5,5],alpha = 0.1 )
currentAxis.annotate('Baaseline\n phase', xy=(3.5, 4.9), xycoords='data', size=12, color='k',ha='center',va='top')
currentAxis.annotate('Exponential\n phase', xy=(12.5, 4.9), xycoords='data', size=12, color='k',ha='center',va='top')
currentAxis.annotate('Plateau\n phase', xy=(28.5, 4.9), xycoords='data', size=12, color='k',ha='center',va='top')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)
currentAxis.text(-0.1, 1.1, "A", transform=currentAxis.transAxes, size=20, weight='bold')

#Top right plot (Dilutions data plot )
#Calculations
cts = []
for cell in cellsToRead:
    x = np.arange(1,len(dataDic[cell]))
    y = dataDic[cell]
    for i,yValue in enumerate(y):
        if yValue == threshold:
            ct = x[y.index(yValue)]
        if yValue > threshold:
            x1 = x[i-1]
            x2 = x [i]
            y1 = y[i-1]
            y2 = yValue
            m = (y2-y1)/(x2-x1)
            c = y2-(m*x1)
            ct = (threshold-c)/m
            cts.append(ct)
            break

#Plotting
currentAxis = ax[0][1]
currentAxis.axhline(threshold,color='k')
for i,cell in enumerate(cellsToRead):
    currentAxis.plot(dataDic[cell],'o--', color = "C"+str(i), label="$f_0 = {0:.3}, c_t = {1:.3}$".format(concentrations[i],cts[i]))
    currentAxis.plot([cts[i],cts[i]], [0,threshold],color="C"+str(i),zorder=99)
    currentAxis.axhline(0,zorder=0,color="gray")
currentAxis.set_xlabel("Cycle number",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Fluoroescence (A.U)",fontsize=axisLabelFontSize)
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)
currentAxis.legend(fontsize = 'large')
currentAxis.text(-0.1, 1.1, "B", transform=currentAxis.transAxes, size=20, weight='bold')

#Bottom left (Efficiency plot )
#calculations
x= np.log10(concentrations)
y = cts


#Fitting
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
yfit = x*slope + intercept
Efficiency = (10**(-1.0*(1/slope)) -1) * 100

#plotting
currentAxis = ax[1][0]
currentAxis.plot(x,yfit,label= "$y = {0:.3}x + {1:.3}$  $r^2 = {2:.4}$".format(slope,intercept,r_value**2),color="C1")
currentAxis.plot(x,y,'o',label="Efficiency = {0:.3}%".format(Efficiency),color="C0")
currentAxis.set_xlabel("$log_{10}\\left( f_0 \\right)$",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("$c_t$ ",fontsize=axisLabelFontSize)
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)
currentAxis.legend(fontsize = 'large')
currentAxis.text(-0.1, 1.1, "C", transform=currentAxis.transAxes, size=20, weight='bold')


#Bottom right (Residuals)
#calculations
residuals = y- yfit
#plotting
currentAxis = ax[1][1]
currentAxis.plot(x,residuals,'o--')
currentAxis.set_ylim(-0.2,0.2)
currentAxis.axhline(0,color='grey')
currentAxis.set_xlabel("$log_{10}\\left( f_0\\right)$",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Residual",fontsize=axisLabelFontSize)
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)
currentAxis.text(-0.1, 1.1, "D", transform=currentAxis.transAxes, size=20, weight='bold')






plt.tight_layout()
plt.savefig("./Graphs/ThesisFigures/QPCRFigure1.pdf",bbox_inches = 'tight')
plt.show()
