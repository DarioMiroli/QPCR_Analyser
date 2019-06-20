import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
#Parameters
filePath = "Data/QPCRExperiments_TextFiles/dario_04_03_19_ori-terminus_m631_06.txt"
cellsToRead = ["B1"]
concentrations = [1/(5**i) for i in range(len(cellsToRead))]
threshold = 0.2
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
fig, ax = plt.subplots(nrows=1, ncols=2,figsize=(14,6))

#Top left plot (Linear plot )
currentAxis = ax[0]
xData = [i+1 for i in range(len(dataDic[cellsToRead[0]]))]
currentAxis.plot(xData,dataDic[cellsToRead[0]],'--o')
currentAxis.axhline(threshold,color="C2")
currentAxis.set_xlabel("Cycle number",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Fluoroescence (A.U)",fontsize=axisLabelFontSize)
currentAxis.set_ylim(-0.1,0.1+max(dataDic[cellsToRead[0]]))
currentAxis.text(0.05,0.9, "A", transform=currentAxis.transAxes, size=40, weight='bold')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)


#Top right  plot (Log plot )
#Get logarithim of data ignoring zeros
currentAxis = ax[1]
yData = dataDic[cellsToRead[0]]
xData = [i+1 for i in range(len(yData))]
logyData = [np.log2(p) for p in yData if p >0 ]
logxData = [xData[i] for i in range(len(xData)) if yData[i] >0 ]
#Function to fit
def fitLog(index,x,y,span=5):
    newX = x[index:index+span]
    newY = y[index:index+span]
    slope, intercept, r_value, p_value, std_err = stats.linregress(newX, newY)
    predicty = slope*np.asarray(newX) + intercept
    return newX,predicty,slope,intercept,r_value,newY

def fitLogThresh(thresh,x,y,span=5):
    difference = abs(np.asarray(y) -thresh)
    closestIndex = list(difference).index(min(difference))
    #If even span
    indexes = []
    if span % 2 ==0:
        if y[closestIndex] > thresh:
            for i in range(int(closestIndex),int(closestIndex+(span/2)+1)):
                indexes.append(i)
            for i in range(int(closestIndex-1-(span/2)),int(closestIndex)):
                indexes.append(i)
        else:
            for i in range(int(closestIndex+1),int((span/2)+1+closestIndex)):
                indexes.append(i)
            for i in range(int(closestIndex-(span/2)+1),int(closestIndex+1)):
                indexes.append(i)
    #If odd span
    else:
        for i in range(int(closestIndex-((span-1)/2)), int(closestIndex + ((span-1)/2) + 1)):
            indexes.append(i)
    indexes.sort()
    newX = [x[i] for i in indexes]
    newY = [y[i] for i in indexes]
    slope, intercept, r_value, p_value, std_err = stats.linregress(newX, newY)
    predicty = slope*np.asarray(newX) + intercept
    return newX,predicty,slope,intercept,r_value,newY

#Compute fit
#predictX,predictY,slope,intercept,r_value,newY = fitLog(6,logxData,logyData)
predictX,predictY,slope,intercept,r_value,newY = fitLogThresh(np.log2(threshold),logxData,logyData,span=5)
#Compute residuals
residuals = newY-predictY
ins = currentAxis.inset_axes([0.6,0.3,0.3,0.3])
ins.axhline(0,color='k')
ins.plot(predictX,residuals,'o--')
ins.set_xlabel("Cycle number")
ins.set_ylabel("Residuals")


#Plot fit line and data
currentAxis.plot(logxData,logyData,'o',label = "$\\alpha = {0:.0f}\%$".format(((2**slope)-1)*100))
currentAxis.plot(predictX,predictY,label="$y = {0:.1f}x + {1:.1f}$ , $r^2 = {2:.3f}$".format(slope,intercept,r_value**2))
currentAxis.axhline(np.log2(threshold),color="C2")
currentAxis.legend(loc="lower right",fontsize = 'x-large')
currentAxis.set_xlabel("Cycle number",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("$log_2(Fluoroescence)$ (A.U)",fontsize=axisLabelFontSize)
currentAxis.text(0.05, 0.9, "B", transform=currentAxis.transAxes, size=40, weight='bold')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)



#currentAxis.set_ylim(-0.1,5)

plt.tight_layout()
plt.show()
