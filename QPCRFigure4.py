import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


concentrations = [1/(5**i) for i in range((5))]
logConc = np.log10(concentrations)

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
    print( oriCts[-2])
    print(logConc)
    slope, intercept, r_value, p_value, std_err = stats.linregress(logConc, oriCts[-2])
    oriCts.append(list(logConc*slope + intercept))
    oriSlope = slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(logConc, terCts[-2])
    terSlope = slope
    terCts.append(list(logConc*slope + intercept))
    return oriCts,terCts, oriSlope, terSlope

ori1Cts, ter1Cts, ori1Slope, ter1Slope = readCts("Data/HighOsmoDataForFigure/M63_1.csv")
ori2Cts, ter2Cts, ori2Slope, ter2Slope = readCts("Data/HighOsmoDataForFigure/M63_2.csv")

fig = plt.figure(figsize=(14,9))


#Top left plot standard curves
ax1 = plt.subplot2grid((4, 4), (0, 0),rowspan=2,colspan=2,fig=fig)

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


#Top right plot residuals (sort of)
ax2 = plt.subplot2grid((4, 4), (0, 2),fig=fig)
ax3 = plt.subplot2grid((4, 4), (0, 3),fig=fig)
ax4 = plt.subplot2grid((4, 4), (1, 2),fig=fig)
ax5 = plt.subplot2grid((4, 4), (1, 3),fig=fig)
axes = [ax2,ax3,ax4,ax5]
runs = [ori1Cts,ori2Cts,ter1Cts,ter2Cts]
colors = ["C1","C3","C5","C7"]
labels=["Origin 1", "Origin 2", "Termini 1", "Termini 2"]
for i in range(len(runs)):

    axes[i].plot(logConc,np.asarray(runs[i][-3])-np.asarray(runs[i][-1]),'^--',color=colors[i],label=labels[i])
    axes[i].axhline(0,color='gray')
    axes[i].legend(fontsize="medium")



#Bottom left plot corrected standard curves



plt.tight_layout()
plt.show()
