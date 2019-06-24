import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
#Parameters
filePath = "Data/QPCRExperiments_TextFiles/dario_04_03_19_ori-terminus_m631_06.txt"
cellsToRead = ["A7","A8","A9","A10","A11","B7","B8","B9","B10","B11","C7","C8","C9","C10","C11","D7","D8","D9","D10","D11"]
concentrations = [1/(5**i) for i in range((5))]
threshold = 0.2
axisLabelFontSize = 18
tickLabelFontSize = 15
thresholds = np.arange(0.03,3,0.3)
logThresholds = np.arange(-5.5,2.5,0.4)
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

#Top left plot (Linear plot )
currentAxis = ax[0][0]
for j in range(len(cellsToRead)):
    xData = [i+1 for i in range(len(dataDic[cellsToRead[0]]))]
    currentAxis.plot(xData,dataDic[cellsToRead[j]],'--o')
for threshold in logThresholds:
    currentAxis.axhline(2**threshold,color="C2")
currentAxis.set_xlabel("Cycle number",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Fluorescence (A.U)",fontsize=axisLabelFontSize)
currentAxis.set_ylim(-0.1,0.1+max(dataDic[cellsToRead[0]]))
currentAxis.text(0.1,0.85, "A", transform=currentAxis.transAxes, size=40, weight='bold')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)


#Top right  plot (Log plot )
#Get logarithim of data ignoring zeros
currentAxis = ax[0][1]
for j in range(len(cellsToRead)):
    yData = dataDic[cellsToRead[j]]
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
    #Plot fit line and data
    currentAxis.plot(logxData,logyData,'o')#,label = "$\\alpha = {0:.0f}\%$".format(((2**slope)-1)*100))
    #currentAxis.plot(predictX,predictY)#,label="$y = {0:.1f}x + {1:.1f}$ , $r^2 = {2:.3f}$".format(slope,intercept,r_value**2))
#Compute residuals
residuals = newY-predictY
#ins = currentAxis.inset_axes([0.6,0.3,0.3,0.3])
#ins.axhline(0,color='k')
#ins.plot(predictX,residuals,'o--')
#ins.set_xlabel("Cycle number")
#ins.set_ylabel("Residuals")


for threshold in logThresholds:
    currentAxis.axhline(threshold,color="C2")
currentAxis.legend(loc="lower right",fontsize = 'small')
currentAxis.set_xlabel("Cycle number",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("$log_2(Fluorescence)$ (A.U)",fontsize=axisLabelFontSize)
currentAxis.text(0.1,0.85, "B", transform=currentAxis.transAxes, size=40, weight='bold')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)



#Bottom left plot (Linear plot )
currentAxis = ax[1][0]

meanEfficiencies = np.zeros((len(logThresholds),len(cellsToRead)))
for j in range(len(cellsToRead)):
    efficiencies = []
    yData = dataDic[cellsToRead[j]]
    xData = [i+1 for i in range(len(yData))]
    logyData = [np.log2(p) for p in yData if p >0 ]
    logxData = [xData[i] for i in range(len(xData)) if yData[i] >0 ]
    for thresh in logThresholds:
        predictX,predictY,slope,intercept,r_value,newY = fitLogThresh(thresh,logxData,logyData,span=5)
        efficiencies.append((2**slope) - 1)
    currentAxis.plot(logThresholds,np.asarray(efficiencies)*100,'--o')
    for i,eff in enumerate(efficiencies):
        meanEfficiencies[i][j] =  eff
#Mean efficiencies
#currentAxis.axhline(threshold,color="C2")
currentAxis.set_xlabel("$log_2($Threshold value$)$",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Efficiency (%)",fontsize=axisLabelFontSize)

#currentAxis.set_ylim(-0.1,0.1+max(dataDic[cellsToRead[0]]))
currentAxis.text(0.1,0.85, "C", transform=currentAxis.transAxes, size=40, weight='bold')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)








#Bottom right comparison between log plot and standard curve
currentAxis = ax[1][1]


#Standard curve
#Function to get ct
def getCt(x,y,thresh):
    for i,yValue in enumerate(y):
        if yValue == thresh:
            ct = x[y.index(yValue)]
        if yValue > thresh:
            x1 = x[i-1]
            x2 = x [i]
            y1 = y[i-1]
            y2 = yValue
            m = (y2-y1)/(x2-x1)
            c = y2-(m*x1)
            ct = (thresh-c)/m
            return ct


standardsEff = []
for thresh in logThresholds:
    ctValues = np.zeros((len(concentrations), 4))
    for repeat in range(4):
        for conc in range(len(concentrations)):
            yData = dataDic[cellsToRead[repeat*5 + conc]]
            xData = [i+1 for i in range(len(yData))]
            ctValues[conc][repeat] =  getCt(xData,yData,2**thresh)
            #print("Threshold:" + str(2**thresh))


    meanCts = np.mean(ctValues,axis=1)
    print(thresh)
    print(meanCts)
    slope, intercept, r_value, p_value, std_err = stats.linregress(np.log10(concentrations), meanCts)
    standardsEff.append((10**(-1.0/slope) -1)*100 )
#currentAxis.plot(np.log10(concentrations),meanCts)
print(standardsEff)
currentAxis.plot(logThresholds,standardsEff,color="C3",label="Standard curve")
currentAxis.fill_between(logThresholds,standardsEff-std_err,standardsEff+std_err,alpha=0.5,color="C3")
currentAxis.axhline(100.0116745,color="C5",linestyle="--",label="Maximum acceleration")
currentAxis.fill_between(logThresholds,[99.99-1.8]*len(logThresholds),[99.99+1.8]*len(logThresholds),color="C5",linestyle="--",alpha=0.5)


ins = currentAxis.inset_axes([0.6,0.65,0.3,0.3])
#ins.axhline(0,color='k')
ins.plot(logThresholds,standardsEff,color="C3")
ins.fill_between(logThresholds,standardsEff-std_err,standardsEff+std_err,alpha=0.5,color="C3")
ins.axhline(99.99,color="C5",linestyle="--")
ins.fill_between(logThresholds,[99.99-1.8]*len(logThresholds),[99.99+1.8]*len(logThresholds),color="C5",linestyle="--",alpha=0.5)
ins.set_ylim(96,103)
#ins.set_xlabel("Cycle number")
#ins.set_ylabel("Residuals")
#Semi log eff compari1.8
meanEff = np.mean(meanEfficiencies,axis=1)*100
stdEff = (np.std(meanEfficiencies,axis=1))*100
currentAxis.plot(logThresholds,meanEff,label="Semi log fit")
currentAxis.fill_between(logThresholds,meanEff-stdEff,meanEff+stdEff,alpha=0.5)
ins.plot(logThresholds,meanEff)
ins.fill_between(logThresholds,meanEff-stdEff,meanEff+stdEff,alpha=0.5)
currentAxis.text(0.1,0.85, "D", transform=currentAxis.transAxes, size=40, weight='bold')
currentAxis.tick_params(axis="x", labelsize=tickLabelFontSize)
currentAxis.tick_params(axis="y", labelsize=tickLabelFontSize)
currentAxis.set_xlabel("$log_2($Threshold value$)$",fontsize=axisLabelFontSize)
currentAxis.set_ylabel("Efficiency (%)",fontsize=axisLabelFontSize)
currentAxis.legend(fontsize="x-large",loc="lower center")
plt.tight_layout()
plt.show()
