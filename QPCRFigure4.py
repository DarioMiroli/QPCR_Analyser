import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from scipy import stats
import time
import copy
concentrations = [1/(5**i) for i in range((5))]
logConc = np.log10(concentrations)
tickLabelFontSize = 15
axisLabelFontSize = 20
def readCts(path):
    f = open(path)
    oriCts = []
    terCts = []
    ters = False
    for line in f.readlines():
        if line.strip().split(",") == [""]:
            ters = True
        else:
            stripLine = line.strip().split(",")
            cts = [float(strp) for strp in stripLine]
            if not ters:
                oriCts.append(cts)
            if ters:
                terCts.append(cts)
    oriCts.append(list(np.mean(oriCts,axis=0)))
    terCts.append(list(np.mean(terCts,axis=0)))
    oriCts.append(list(np.std(oriCts[0:-1],axis=0,ddof=1)))
    terCts.append(list(np.std(terCts[0:-1],axis=0,ddof=1)))
    slope, intercept, r_value, p_value, std_err = stats.linregress(logConc, oriCts[-2])
    oriCts.append(list(logConc*slope + intercept))
    oriSlope = slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(logConc, terCts[-2])
    terSlope = slope
    terCts.append(list(logConc*slope + intercept))
    return oriCts,terCts, oriSlope, terSlope

which = 1
if which == 1:
    ori1Cts, ter1Cts, ori1Slope, ter1Slope = readCts("Data/HighOsmoDataForFigure/M63_1.csv")
    ori2Cts, ter2Cts, ori2Slope, ter2Slope = readCts("Data/HighOsmoDataForFigure/M63_2.csv")
    tau = 39.6
if which == 2:
    ori1Cts, ter1Cts, ori1Slope, ter1Slope = readCts("Data/HighOsmoDataForFigure/200mM_1.csv")
    ori2Cts, ter2Cts, ori2Slope, ter2Slope = readCts("Data/HighOsmoDataForFigure/200mM_2.csv")
    tau = 46
if which == 3:
    ori1Cts, ter1Cts, ori1Slope, ter1Slope = readCts("Data/HighOsmoDataForFigure/600mM_1.csv")
    ori2Cts, ter2Cts, ori2Slope, ter2Slope = readCts("Data/HighOsmoDataForFigure/600mM_2.csv")
    tau = 80

fig = plt.figure(figsize=(14,10))


#Top left plot standard curves
gs = gridspec.GridSpec(2, 2,figure = fig )
gs1 = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[0:2,0])
gs2 = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[0,1],wspace=0.06)
gs3 = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[1,1],wspace=0.06)
#ax1 = plt.subplot2grid((4, 4), (0, 0),rowspan=2,colspan=2,fig=fig)
ax1 = plt.subplot(gs1[0, 0])
ax1.text(0,1.05, "A", transform=ax1.transAxes, size=30, weight='bold')
#ax2 = plt.subplot2grid((4, 4), (0, 2),fig=fig)
ax2 = plt.subplot(gs2[0, 0])
ax2.text(0.0,1.1, "B", transform=ax2.transAxes, size=30, weight='bold')
#ax3 = plt.subplot2grid((4, 4), (0, 3),fig=fig)
ax3 = plt.subplot(gs2[0, 1])
ax3.set_yticklabels([])
#ax4 = plt.subplot2grid((4, 4), (1, 2),fig=fig)
ax4 = plt.subplot(gs2[1, 0])
#ax5 = plt.subplot2grid((4, 4), (1, 3),fig=fig)
ax5 = plt.subplot(gs2[1, 1])
ax5.set_yticklabels([])
#ax6 = plt.subplot2grid((4, 4), (2, 0),fig=fig,rowspan=2,colspan=2)
ax6 = plt.subplot(gs1[1,0])
ax6.text(0, 1.05 , "C", transform=ax6.transAxes, size=30, weight='bold')
#ax7 = plt.subplot2grid((4, 4), (2, 2),fig=fig)
ax7 = plt.subplot(gs3[0, 0])
ax7.text(0, 1.1 , "D", transform=ax7.transAxes, size=30, weight='bold')
#ax8 = plt.subplot2grid((4, 4), (2, 3),fig=fig)
ax8 = plt.subplot(gs3[0, 1])
ax8.set_yticklabels([])
#ax9 = plt.subplot2grid((4, 4), (3, 2),fig=fig)
ax9 = plt.subplot(gs3[1, 0])
#ax10 = plt.subplot2grid((4, 4), (3, 3),fig=fig)
ax10 = plt.subplot(gs3[1, 1])
ax10.set_yticklabels([])

c = 0
slopes = [ori1Slope,ori2Slope,ter1Slope,ter2Slope]
alphas = [10**(-1/s) -1 for s in slopes]
labels = ["Origin 1", "Origin 2", "Terminus 1", "Terminus 2"]
labels = [ labels[i] + " $\\alpha = {0:.0f} \\%$".format(alphas[i]*100.0) for i in range(len(alphas))]
for l,run in enumerate([ori1Cts,ori2Cts,ter1Cts,ter2Cts]):
    for i in range(6):
        if i ==4:
            ax1.plot(logConc,run[i],'^',color="C{0}".format(1+c),label=labels[l])
        elif i ==5:
            ax1.plot(logConc,run[-1],'-',color="C{0}".format(1+c))
        else:
            ax1.plot(logConc,run[i],'.',color="C{0}".format(c))
    c = c+2
ax1.legend(fontsize="x-large")
ax1.set_xlabel("$log_2(C)$",fontsize=axisLabelFontSize)
ax1.set_ylabel("$c_t$",fontsize=axisLabelFontSize)
ax1.tick_params(axis="x", labelsize=tickLabelFontSize)
ax1.tick_params(axis="y", labelsize=tickLabelFontSize)
#Top right plot residuals (sort of)
axes = [ax2,ax3,ax4,ax5]
runs = [ori1Cts,ori2Cts,ter1Cts,ter2Cts]
labels=["Origin 1", "Origin 2", "Termini 1", "Termini 2"]
c = 0
for i in range(len(runs)):
    for j in range(4):
        axes[i].plot(logConc,np.asarray(runs[i][-4-j])-np.asarray(runs[i][-1]),'o',color="C{0}".format(c))
    axes[i].errorbar(logConc,np.asarray(runs[i][-3])-np.asarray(runs[i][-1]),yerr=runs[i][-2],color="C{0}".format(1+c),label=labels[i],ecolor="k",fmt="^",zorder=999,capsize=5)
    axes[i].axhline(0,color='gray')
    axes[i].legend(fontsize="medium")
    axes[i].set_ylim(-0.3,0.3)
    axes[i].tick_params(axis="x", labelsize=tickLabelFontSize)
    axes[i].tick_params(axis="y", labelsize=tickLabelFontSize)
    c = c + 2
axes[2].set_xlabel("$log_2(C)$",fontsize=axisLabelFontSize)
axes[3].set_xlabel("$log_2(C)$",fontsize=axisLabelFontSize)
axes[0].set_ylabel("$Residuals$",fontsize=axisLabelFontSize)
axes[2].set_ylabel("$Residuals$",fontsize=axisLabelFontSize)




#Bottom left plot corrected standard curves
def improveStd(data, thresh = 0.03):
    best = np.std(data,ddof=1)
    newData = data.copy()
    while best > thresh and len([d for d in newData if d != None]) > 2:
        for i in range(len(newData)):
            #print("best {} \t data: {}".format(best,newData))
            if newData[i] != None:
                tempData = newData.copy()
                tempData[i] = None
                newBest = np.std([d for d in tempData if d != None],ddof=1)
                if newBest < best:
                    best = newBest
                    indexToRemove =i
        newData[indexToRemove] = None
        #time.sleep(1)
    return newData

def removeNone(array):
    newArray = []
    for a in array:
        if a != None:
            newArray.append(a)
    return copy.deepcopy(newArray)


runs = [ori1Cts,ori2Cts,ter1Cts,ter2Cts]
newRuns = copy.deepcopy(runs)
for i in range(len(runs)):
    for j in range(5):
        column = [runs[i][k][j] for k in range(4)]
        newColumn = improveStd(column)
        for l in range(len(newColumn)):
            newRuns[i][l][j] = newColumn[l]
        newRuns[i][4][j] = np.mean(removeNone(newColumn))
        newRuns[i][5][j] = np.std(removeNone(newColumn),ddof=1)
#Now we have replaced average values we can do fits
slopes = []
for run in newRuns:
    slope, intercept, r_value, p_value, std_err = stats.linregress(logConc, run[-3])
    yPredict = slope*logConc + intercept
    run[-1] = yPredict
    slopes.append(slope)
alphas = [10**(-1/m) -1 for m in slopes]
labels =  [ "Origin 1", "Origin 2", "Termini 1", "Temrini 2"]
labels = [labels[i] + " $\\alpha = ${0:.0f}%".format(alphas[i]*100.0) for i in range(len(alphas))]
for i,run in enumerate(newRuns):
    ax6.plot(logConc,run[-3],'^',label=labels[i])
    ax6.plot(logConc,run[-1])
ax6.legend(fontsize ="x-large")
ax6.set_xlabel("$log_2(C)$",fontsize=axisLabelFontSize)
ax6.set_ylabel("$c_t$",fontsize=axisLabelFontSize)
ax6.tick_params(axis="x", labelsize=tickLabelFontSize)
ax6.tick_params(axis="y", labelsize=tickLabelFontSize)

#Bottom  right plot residuals (sort of)
axes = [ax7,ax8,ax9,ax10]
colors = ["C1","C3","C5","C7"]
labels=["Origin 1", "Origin 2", "Termini 1", "Termini 2"]
c = 0
for i in range(len(newRuns)):
    for j in range(4):
        residuals = []
        for k in range(len(newRuns[i][-4-j])):
            if newRuns[i][-4-j][k] != None:
                residuals.append(newRuns[i][-4-j][k] - newRuns[i][-1][k])
            else:
                residuals.append(None)
        axes[i].plot(logConc,  residuals   ,'o',color="C{0}".format(c))
    axes[i].errorbar(logConc,np.asarray(newRuns[i][-3])-np.asarray(newRuns[i][-1]),yerr=newRuns[i][-2],fmt='^--',color=colors[i],label=labels[i],ecolor="k",capsize=5,zorder=999)
    axes[i].axhline(0,color='gray')
    axes[i].legend(fontsize="medium")
    axes[i].set_ylim(-0.3,0.3)
    axes[i].tick_params(axis="x", labelsize=tickLabelFontSize)
    axes[i].tick_params(axis="y", labelsize=tickLabelFontSize)
    c = c + 2
axes[2].set_xlabel("$log_2(C)$",fontsize=axisLabelFontSize)
axes[3].set_xlabel("$log_2(C)$",fontsize=axisLabelFontSize)
axes[0].set_ylabel("$Residuals$",fontsize=axisLabelFontSize)
axes[2].set_ylabel("$Residuals$",fontsize=axisLabelFontSize)

plt.tight_layout()
plt.show()
plt.clf()
plt.close()
fig = plt.figure(figsize=(14,9))
#Time to compute actual c periods

cts1 = []
cts2 = []
for r in range(len(newRuns[0][0])):
    ori1_ter1 = ((alphas[2]+1)**newRuns[2][-3][r])/((alphas[0]+1)**newRuns[0][-3][r])
    ori2_ter2 =  ((alphas[3]+1)**newRuns[3][-3][r])/((alphas[1]+1)**newRuns[1][-3][r])
    ct1 = tau*np.log2(ori1_ter1)
    ct2 = tau*np.log2(ori2_ter2)
    cts1.append(ct1)
    cts2.append(ct2)

fig.gca().plot(logConc,cts1,'o',label="Sample 1")
fig.gca().plot(logConc,cts2,'o',label="Sample 2")
mean = np.mean(cts1+cts2)
stdErr = np.std(cts1+cts2, ddof=1)/(len(cts1+cts2))**0.5
print("{0:.1f} +- {1:.1f}".format(mean,stdErr))
plt.xlabel("$log_2(C)$",fontsize=30)
plt.ylabel("$C$ period (min)",fontsize=30)
plt.axhline(mean,label="$\\bar C = ${0:.0f} $\pm$ {1:.0f}".format(mean,stdErr))
plt.axhspan(mean+stdErr, mean-stdErr, alpha=0.5)
fig.gca().tick_params(axis="x", labelsize=25)
fig.gca().tick_params(axis="y", labelsize=25)
plt.tight_layout()
plt.legend(fontsize="xx-large")
plt.show()
