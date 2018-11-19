import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy import stats
import time
import os

class QPCRAnalyser(QtGui.QMainWindow):
    ''' class for analysing QPCR data for C period determination '''

    def __init__(self,parent=None):
        '''
        Constructor for the analyser GUI
        '''
        #Start with essential data structures
        self.data = {"Files":[] ,"Cells":[], "Xs":[], "Ys":[], "LogXs":[],"LogYs":[],
                    "Visible":[],"RawCurves":[],"LogCurves":[],"Hs":[],"HCurves":[],"RawHCurves":[], "Alphas":[],"AlphaCurves":[]}
        self.threshold  = None
        self.cX = None
        self.cY = None
        self.cFitX = None
        self.cFitY = None
        self.call = False
        self.LREZones = None
        self.concentrations =[1.0,0.2,0.04,0.008,0.0016]
        self.distances = [0.4603,0.02516,0.963,0.0,1.0]
        #Set global settings for plots
        pg.setConfigOption('background', (40,40,40))
        pg.setConfigOption('foreground', (220,220,220))
        #Call functions to set up GUI
        self.app = QtGui.QApplication([])
        QtGui.QMainWindow.__init__(self,parent)
        self.createMenuBar()
        self.resize(1500,750)
        self.show()

    def run(self):
        '''
        Starts the applicaiton
        '''
        self.app.exec_()

    def createMenuBar(self):
        '''
        Sets up the menu bar for loading files
        '''
        #Create menu bar
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)
        #Status bar allows hints to be shown at bottom of window
        self.statusBar()
        #Add file menu
        fileMenu = menuBar.addMenu("File")
        #Create action for opening files
        openFile = QtGui.QAction("Load file", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Load QPCR .txt file')
        openFile.triggered.connect(self.onOpenFile)
        #Add open file action to file menu
        fileMenu.addAction(openFile)
        #Add analysis menu
        analysisMenu = menuBar.addMenu("Analysis")
        setThresh = QtGui.QAction("Set threshold",self)
        setThresh.setShortcut("Ctrl+t")
        setThresh.setStatusTip('set threshold for log data')
        setThresh.triggered.connect(self.onSelectThresh)
        analysisMenu.addAction(setThresh)
        #Add distance calc
        addDistance = QtGui.QAction("Add distance info",self)
        addDistance.setShortcut("Ctrl+d")
        addDistance.setStatusTip('Add information about spacing of shown data')
        addDistance.triggered.connect(self.onAddDistance)
        analysisMenu.addAction(addDistance)
        #Add callibration menu
        calcEfficiency = QtGui.QAction("Calc standard curve efficiency",self)
        calcEfficiency.setShortcut("ctrl+c")
        calcEfficiency.setStatusTip('Compute efficiency of QPCR primers using dillution')
        calcEfficiency.triggered.connect(self.onComputeEfficiency)
        analysisMenu.addAction(calcEfficiency)
        #Add threshold scan
        thresholdScan = QtGui.QAction("Threshold Scan",self)
        thresholdScan.setShortcut("shift+t")
        thresholdScan.setStatusTip('Scan through possible threshold values and plot results')
        thresholdScan.triggered.connect(self.onThresholdScan)
        analysisMenu.addAction(thresholdScan)

        #Add LRE efficiency calculation
        LRE = QtGui.QAction("Calc LRE efficiency",self)
        LRE.setShortcut("shift+L")
        LRE.setStatusTip('Calculate efficiency of single trace')
        LRE.triggered.connect(self.CalcLREEfficiency)
        analysisMenu.addAction(LRE)

        #Add plot saving
        savePlot = QtGui.QAction("Save plots", self)
        savePlot.setShortcut("Ctrl+S")
        savePlot.setStatusTip('Save all 3 plots to file')
        savePlot.triggered.connect(self.onSavePlot)
        fileMenu.addAction(savePlot)
        #Add saving to peters format
        savePetersFormat = QtGui.QAction("Save peters format", self)
        savePetersFormat.setShortcut("Ctrl+P")
        savePetersFormat.setStatusTip('Save selected to peters format')
        savePetersFormat.triggered.connect(self.saveToPetersFormat)
        fileMenu.addAction(savePetersFormat)

    def onOpenFile(self):
        '''
        Opens file dialoug and loads data if .txt file is selected
        '''
        #Launch file selection dialoug
        filePath, filter = QtGui.QFileDialog.getOpenFileName(self,'Open File',
        './',filter="*.txt")
        #If file selected start reading file
        if filePath != '':
            self.readQPCRFile(filePath)
            self.setUpUI()

    def readQPCRFile(self,filePath):
        '''
        Load QPCR data from chosen .txt file
        '''
        #Get filename
        head, tail = os.path.split(filePath)
        self.data["Files"].append(tail)
        #Load in utf16 format
        f = open(filePath,encoding='utf-16-le')
        #Extract data
        x = []
        for i,line in enumerate(f.readlines()):
            splitLine = line.rstrip().split("\t")
            y = []
            for j,item in enumerate(splitLine):
                if i == 0 and j > 0:
                    x.append(j)
                if i > 0:
                    if j == 0:
                        self.data["Cells"].append(item)
                    else:
                        y.append(float(item))
            if i > 0:
                self.data["Ys"].append(y)
                self.data["Xs"].append(x)
                self.data["Visible"].append(False)
                self.data["RawCurves"].append(pg.PlotDataItem(x,y,symbolSize=7.0,symbol='o',symbolPen=None))
                self.data["Hs"].append(-1)
                self.data["HCurves"].append(pg.InfiniteLine())
                self.data["Alphas"].append(-1)
                self.data["AlphaCurves"].append(pg.PlotCurveItem([],[]))
                logX = [x[i] for i in range(len(x)) if y[i] >0]
                logY = [np.log2(y[i]) for i in range(len(x)) if y[i] >0]
                self.data["LogXs"].append(logX)
                self.data["LogYs"].append(logY)
                self.data["LogCurves"].append(pg.PlotDataItem(logX,logY,symbol='o',symbolSize=5,symbolPen=None))

    def setUpUI(self):
        '''
        After loading a file sets up the main UI
        '''
        #Create the main widget for our application and set the layout
        mainWidget = QtGui.QWidget()
        mainLayout = QtGui.QGridLayout()

        #Top left add plot
        self.rawPlot = pg.PlotWidget()
        self.rawPlot.showGrid(x=True,y=True)
        self.rawPlot.setLabel('bottom', "Cycle")
        self.rawPlot.setLabel('left', "Flourescence")
        self.rawPlot.setLabel('top', "Raw plot")
        self.rawPlot.addLegend()
        mainLayout.addWidget(self.rawPlot,0,0)

        #Top right add plot and slider
        logPlotLayout = QtGui.QGridLayout()
        self.logPlot = pg.PlotWidget()
        self.logPlot.showGrid(x=True,y=True)
        self.logPlot.addLegend()
        logPlotLayout.addWidget(self.logPlot,0,0)
        self.logPlot.setLabel('bottom', "Cycle")
        self.logPlot.setLabel('left', "Log(flourescence)")
        self.logPlot.setLabel('top', "Log plot")


        mainLayout.addLayout(logPlotLayout,0,1)

        #Bottom right plot
        self.cPlot = pg.PlotWidget()
        self.cPlot.showGrid(x=True,y=True)
        self.cPlot.addLegend()
        mainLayout.addWidget(self.cPlot,1,1)

        #Add layout to main window
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        #Add plate buttons
        plateLayout  = QtGui.QGridLayout()
        plateLayout.setSpacing(0)
        columns = [str(i) for i in range(1,13)]
        rows = ["A","B","C","D","E","F","G","H"]
        #Create column headers
        for i,column in enumerate(columns):
            headerBtn = QtGui.QPushButton(column)
            headerBtn.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
            plateLayout.addWidget(headerBtn,0,i+1)
        #Create row headers
        for i,row in enumerate(rows):
            headerBtn = QtGui.QPushButton(row)
            headerBtn.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
            plateLayout.addWidget(headerBtn,i+1,0)
        #Create cell buttons
        for i in range(1,len(rows)+1):
            for j in range(1,len(columns)+1):
                btn = QtGui.QPushButton(rows[i-1]+columns[j-1])
                btn.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
                btn.setCheckable(True)
                btn.clicked.connect(self.onCellPress)
                plateLayout.addWidget(btn,i,j)
        #Add layout to main layout
        mainLayout.addLayout(plateLayout,1,0)

        #Add marquee selection
        self.rubberband = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)
        self.setMouseTracking(True)

    def onCellPress(self):
        self.rawPlot.plotItem.legend.items = []
        for i,name in enumerate(self.data["Cells"]):
            if str(self.sender().text()) == name.split()[0]:
                if self.sender().isChecked():
                    self.rawPlot.addItem(self.data["RawCurves"][i])
                    self.logPlot.addItem(self.data["LogCurves"][i])
                    if len(self.data["HCurves"]) > 0:
                        self.logPlot.addItem(self.data["HCurves"][i])
                    self.data["Visible"][i] = True
                else:
                    self.rawPlot.removeItem(self.data["RawCurves"][i])
                    self.logPlot.removeItem(self.data["LogCurves"][i])
                    if len(self.data["HCurves"]) > 0:
                        self.logPlot.removeItem(self.data["HCurves"][i])
                    self.data["Visible"][i] = False
        n = np.sum(self.data["Visible"])
        j= 0
        for i,curve in enumerate(self.data["RawCurves"]):
            if self.data["Visible"][i]:
                self.rawPlot.plotItem.legend.addItem(self.data["RawCurves"][i],self.data["Cells"][i].split(" ")[0])
                curve.setPen((j,n))
                curve.setSymbolBrush((j,n))
                self.data["LogCurves"][i].setPen(None)#(j,n))
                self.data["LogCurves"][i].setSymbolBrush((j,n))
                if len(self.data["HCurves"]) > 0:
                    self.data["HCurves"][i].setPen((j,n))
                j+=1
        self.fitExpos()

    def onSelectThresh(self):
        if self.threshold == None:
            default = 0
        else:
            default = self.threshold
        num,ok = QtGui.QInputDialog.getDouble(self,"Select threshold","Enter threshold value",value=default)
        if ok:
            try:
                self.logPlot.removeItem(self.threshLine)
                self.rawPlot.removeItem(self.rawThreshLine)
            except:
                pass
            #Add horizontal line at value
            self.threshold = num
            self.threshLine  = pg.InfiniteLine(angle=0,pos=self.threshold)
            self.logPlot.addItem(self.threshLine)
            self.rawThreshold = 2**self.threshold
            self.rawThreshLine = pg.InfiniteLine(angle=0,pos=self.rawThreshold)
            self.rawPlot.addItem(self.rawThreshLine)
            self.computeHs()
            self.fitExpos()

    def computeHs(self):
        '''
        Compute the cycle at which the selected data crosses the threshold value
        '''
        for i in range(len(self.data["Xs"])):
            xs = self.data["LogXs"][i]
            ys = self.data["LogYs"][i]
            for j in range(len(xs)):
                if ys[j] > self.threshold:
                    #We have crossed threshold get points either side
                    y2 = ys[j]
                    y1 = ys[j-1]
                    x2 = xs[j]
                    x1 = xs[j-1]
                    m = (y2-y1)/float((x2-x1))
                    c = y2 - m*x2
                    h = (self.threshold-c)/float(m)
                    self.data["Hs"][i] = h
                    try:
                        vline = pg.InfiniteLine(angle=90,pos=h,pen=self.data["LogCurves"][i].opts["symbolBrush"])
                    except:
                        vline = pg.InfiniteLine(angle=90,pos=h,pen=self.data["LogCurves"][i].opts["symbolBrush"].color())
                    self.logPlot.removeItem(self.data["HCurves"][i])
                    self.data["HCurves"][i] = vline
                    if self.data["Visible"][i]:
                        self.logPlot.addItem(vline)
                    break

    def onAddDistance(self):
        D1 =DistanceDialog(self.data,defaults=self.distances)
        if D1.exec_():
            distances, Hs = D1.getValues()
            self.distances = distances
            self.plotDeltaGDeltaH(distances,Hs)

    def plotDeltaGDeltaH(self,distances,Hs):
        self.call = False
        self.cPlot.clear()
        self.cPlot.setLabel('bottom', "Delta G")
        self.cPlot.setLabel('left', "Delta H")
        self.cPlot.setLabel('top', "Delta H Delta G Plot")
        self.cPlot.plotItem.legend.items = []
        Hs = [x for _,x in sorted(zip(distances,Hs))]
        distances = sorted(distances)

        xs = []
        ys = []
        for i in range(len(distances)-1):
            for j in range(i+1,len(distances)):
                xs.append(distances[j]-distances[i])
                ys.append(Hs[j]-Hs[i])
        curve = pg.ScatterPlotItem(xs,ys,pen=(2,3))
        slope, intercept, r_value, p_value, std_err = stats.linregress(xs,ys)
        slope2, _, _, _ = np.linalg.lstsq(np.asarray(xs)[:,np.newaxis],ys)
        fitX = np.linspace(0,max(xs),100)
        fitY = [slope*x + intercept for x in fitX]
        deltaGOverDeltaHEstimates = [ys[k]/xs[k] for k in range(len(xs))]
        print("Median:" + str(np.median(deltaGOverDeltaHEstimates)) )
        self.cPlot.addItem(curve)
        self.cPlot.addItem(pg.PlotCurveItem(fitX,fitY,pen=(1,2)))
        self.cPlot.addItem(pg.PlotCurveItem(fitX,fitX*slope2,pen=(2,2)))
        self.cPlot.plotItem.legend.addItem(curve,"y = {0:.3} x + {1:.3} R2 {2:.4}".format(slope,intercept,r_value**2))
        self.cX = xs
        self.cY = ys
        self.cFitX = fitX
        self.cFitY = fitY

    def onSavePlot(self):
        S1 = SaveWindow(self.data,self.threshold,self.rawThreshold, self.cX,self.cY,self.cFitX,self.cFitY,call=self.call)

    def fitExpos(self):
        if self.threshold != None:
            self.logPlot.plotItem.legend.items = []
            n=np.sum(self.data["Visible"])
            c = 0
            for i in range(len(self.data["Cells"])):
                if self.data["Visible"][i]:
                    self.logPlot.removeItem(self.data["AlphaCurves"][i])
                    h = round(self.data["Hs"][i])
                    index = len([k for k in range(len(self.data["LogXs"][i])) if self.data["LogXs"][i][k] <= h])
                    if index > 1:
                        x = np.asarray(self.data["LogXs"][i])[index-2:index+2]
                        y = np.asarray(self.data["LogYs"][i])[index-2:index+2]
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
                        alpha = 2.0**(slope) - 1.0
                        self.data["Alphas"][i] = alpha
                        xFit = np.linspace(x[0],x[-1],100)
                        yFit = [i*slope + intercept for i in xFit]
                        curve = pg.PlotCurveItem(xFit,yFit,pen=(c,n))
                        c = c + 1
                        self.logPlot.addItem(curve)
                        self.logPlot.plotItem.legend.addItem(curve,"a= {0:.3} t= {1:.3}".format(alpha,self.data["Hs"][i]))
                        self.data["AlphaCurves"][i] = curve
                    else:
                        c = c+1
                else:
                    self.logPlot.removeItem(self.data["AlphaCurves"][i])

    def onComputeEfficiency(self):
        D1 = DistanceDialog(self.data,defaults=self.concentrations ,call=True)
        if D1.exec_():
            concentrations, cts = D1.getValues()
            self.concentrations = concentrations
            self.plotCallCurve(concentrations,cts)

    def plotCallCurve(self,concentrations,cts):
        self.call = True
        self.cPlot.clear()
        self.cPlot.setLabel('left', "Log(concentration)")
        self.cPlot.setLabel('bottom', "ct")
        self.cPlot.setLabel('top', "Callibration curve")
        self.cPlot.plotItem.legend.items = []
        y = list(np.log10(concentrations))
        x = (cts)
        curve = pg.ScatterPlotItem(x,y,pen=(2,3))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
        fitX = np.linspace(min(x),max(x),100)
        fitY = [slope*X + intercept for X in fitX]
        curveFit = pg.PlotCurveItem(fitX,fitY,pen=(1,2))
        self.cPlot.addItem(curve)
        self.cPlot.addItem(curveFit)
        self.cPlot.plotItem.legend.addItem(curveFit,"y = {0:.3} x + {1:.3}".format(slope,intercept))
        #efficiency =((10**(-1.0/slope)) -1 )*100.0
        efficiency =((10**(-1.0*slope)) -1 )*100
        self.cPlot.plotItem.legend.addItem(curve,"R2={0:.3} EFF={1:.4}".format(r_value**2,efficiency))
        self.cX = x
        self.cY = y
        self.cFitX = fitX
        self.cFitY = fitY
        return efficiency

    def onThresholdScan(self):
        for traceNo in range(len(self.data["LogYs"])):
            if self.data["Visible"][traceNo]:
                x = self.data["LogXs"][traceNo]
                y = self.data["LogYs"][traceNo]
                rSquareds = []
                errors = []
                xs = []
                for i in range(len(x)-4):
                    fitX = x[i:i+4]
                    fitY = y[i:i+4]
                    slope, intercept, r_value, p_value, std_err = stats.linregress(fitX,fitY)
                    yPredict = slope*np.asarray(fitX) + intercept
                    error = np.mean((yPredict-fitY)**2)
                    rSquareds.append(r_value**2)
                    errors.append(error)
                    xs.append(x[i])
                plt.plot(xs,rSquareds,'o--')
                plt.show()
                plt.plot(xs,errors,'o--')
                plt.show()




        return
        print("Threshold scan")
        #Determine min max values of all plotted traces
        minY = 1E6
        maxY = -1E6
        for i,yTrace in enumerate(self.data["LogYs"]):
            if self.data["Visible"][i]:
                if max(yTrace) > maxY:
                    maxY = max(yTrace)
                if min(yTrace) < minY:
                    minY = min(yTrace)
        thresholds = np.linspace(minY,maxY,100)
        alphas = [[] for i in range(sum(self.data["Visible"]))]
        for thresh in thresholds:
            self.threshold = thresh
            self.computeHs()
            self.fitExpos()
            j = 0
            for i,alpha in enumerate(self.data["Alphas"]):
                if self.data["Visible"][i]:
                    alphas[j].append(alpha)
                    j = j+1
        for i in range(len(alphas)):
            plt.plot(thresholds,alphas[i])
            plt.xlabel("Threshold")
            plt.ylabel("Efficiency")
        plt.show()

    def saveToPetersFormat(self):
        #Launch file selection dialoug
        filePath, filter = QtGui.QFileDialog.getSaveFileName(self,'Open File',
        './',filter="*.csv")
        #If file selected start reading file
        if filePath != '':
            f = open(filePath,"w")
            for i in range(len(self.data["Xs"][0])):
                line = ''
                for j in range(-1,len(self.data["Xs"])):
                    if j == -1:
                        line += str(self.data["Xs"][j][i])
                    else:
                        if self.data["Visible"][j]:
                            line += " , "
                            line += str(self.data["Ys"][j][i])

                line += "\n"
                f.write(line)

    def CalcLREEfficiency(self):
        #Plotting stuff
        self.cPlot.clear()
        self.cPlot.setLabel('left', "Cycle efficiency")
        self.cPlot.setLabel('bottom', "Flourescence")
        self.cPlot.setLabel('top', "Callibration curve")
        self.cPlot.plotItem.legend.items = []

        if self.LREZones != None:
            for zone in self.LREZones:
                self.rawPlot.removeItem(zone)
        self.LREZones = []

        c = 0
        for i in range(len(self.data["Xs"])):
            if self.data["Visible"][i]:
                x = self.data["Xs"][i]
                y = self.data["Ys"][i]
                flourescence = y[1:]
                cycleEfficiency = [(y[j]/y[j-1]) -1 for j in range(1,len(y))]
                curve = pg.ScatterPlotItem(flourescence,cycleEfficiency,pen=None,brush=(c,sum(self.data["Visible"])))
                self.cPlot.addItem(curve)
                hReigon = pg.LinearRegionItem([min(x),0.1*max(x)],movable=True,bounds=[min(x),max(x)])
                color = pg.mkColor((c,sum(self.data["Visible"])))
                color.setAlpha(int(25))
                hReigon.setBrush(color)
                self.rawPlot.addItem(hReigon)
                self.LREZones.append(hReigon)
                hReigon.sigRegionChangeFinished.connect(self.replotLRE)
                c+=1

    def replotLRE(self):
        self.cPlot.clear()
        c = 0
        for i in range(len(self.data["Xs"])):
            if self.data["Visible"][i]:
                x = self.data["Xs"][i]
                y = np.asarray(self.data["Ys"][i])
                flourescence = y[1:]
                minX, maxX = self.LREZones[c].getRegion()
                flourescence = [flourescence[j] for j in range(len(x)) if x[j] >= minX and x[j] <= maxX]
                cycleEfficiency = [(y[j]/y[j-1]) - 1.0 for j in range(1,len(y))]
                cycleEfficiency = [cycleEfficiency[j] for j in range(len(x)) if x[j] >= minX and x[j] <= maxX]
                curve = pg.ScatterPlotItem(flourescence,cycleEfficiency,pen=None, brush=(c,sum(self.data["Visible"])))
                self.cPlot.addItem(curve)
                #Fit
                slope, intercept, r_value, p_value, std_err = stats.linregress(flourescence,cycleEfficiency)
                xPredict = np.linspace(0,max(flourescence),100)
                yPredict = slope*xPredict + intercept
                curve = pg.PlotCurveItem(xPredict,yPredict,pen=(c,sum(self.data["Visible"])))
                self.cPlot.addItem(curve)
                c+=1





class DistanceDialog(QtGui.QDialog):

    def __init__(self,dataDic,defaults=None,parent=None,call=False):
        QtGui.QDialog.__init__(self,parent)
        self.call = call
        self.data = dataDic
        self.defaults = defaults
        self.setWindowTitle("Add distance data")
        self.setUpUI()
        self.setUpMainWidget()

    def setUpMainWidget(self):
        self.mainWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.addLayout(self.uiLayout,0,0)
        self.setLayout(self.mainLayout)
        self.show()

    def setUpUI(self):
        self.uiLayout = QtGui.QGridLayout()
        #Table for data
        self.table = QtGui.QTableWidget()
        self.table.setRowCount(np.sum(self.data["Visible"]))
        self.table.setColumnCount(3)
        if self.call:
            self.table.setHorizontalHeaderLabels(["Cell","H value","DNA concentration"])
        else:
            self.table.setHorizontalHeaderLabels(["Cell","H value","Distance"])
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table.resizeColumnsToContents()
        self.uiLayout.addWidget(self.table,0,0,1,2)
        self.populateTable()

        #OK button
        okButton = QtGui.QPushButton("OK")
        okButton.clicked.connect(self.onOK)
        self.uiLayout.addWidget(okButton,1,0,1,1)

        #Cancel button
        cancelButton = QtGui.QPushButton("Cancel")
        cancelButton.clicked.connect(self.onCancel)
        self.uiLayout.addWidget(cancelButton,1,1,1,1)

    def onOK(self):
        self.done(1)

    def onCancel(self):
        self.done(0)

    def populateTable(self):
        cells = []
        self.Hs = []
        for i,cell in enumerate(self.data["Cells"]):
            if self.data["Visible"][i]:
                cells.append(cell.split(" ")[0])
                self.Hs.append(self.data["Hs"][i])
        for row in range(self.table.rowCount()):
            self.table.setItem(row,0, QtGui.QTableWidgetItem(str(cells[row])))
            self.table.setItem(row,1, QtGui.QTableWidgetItem(str(round(self.Hs[row],1))))
            if self.defaults!= None:
                try:
                    self.table.setItem(row,2, QtGui.QTableWidgetItem(str(self.defaults[row])))
                except:
                    pass

    def getValues(self):
        #Read last oclumn
        distances = []
        for row in range(self.table.rowCount()):
            distances.append(float(self.table.item(row,2).text()))
        return distances,self.Hs


class SaveWindow(QtGui.QMainWindow):

    def __init__(self,data,thresh,rawThresh,cX,cY,cFitX,cFitY,call=False,parent=None):
        QtGui.QMainWindow.__init__(self,parent)
        self.data = data
        self.call = call
        self.thresh = thresh
        self.rawThresh = rawThresh
        self.cX = cX
        self.cY = cY
        self.cFitX = cFitX
        self.cFitY = cFitY
        self.setWindowTitle("Saveplot")
        self.setUpUI()
        self.setUpPlots()
        self.setUpMainWidget()
        self.plotData()

    def setUpUI(self):
        self.uiLayout = QtGui.QGridLayout()
        self.rawButton = QtGui.QRadioButton("Raw")
        self.rawButton.setChecked(True)
        self.logButton = QtGui.QRadioButton("log")
        self.cButton = QtGui.QRadioButton("C period")
        self.rawButton.clicked.connect(self.plotData)
        self.logButton.clicked.connect(self.plotData)
        self.threshButton = QtGui.QCheckBox("Thresh line")
        self.fitButton = QtGui.QCheckBox("Fits")

        self.cButton.clicked.connect(self.plotData)
        self.threshButton.clicked.connect(self.plotData)
        self.fitButton.clicked.connect(self.plotData)
        self.uiLayout.addWidget(self.rawButton,0,0,1,1)
        self.uiLayout.addWidget(self.logButton,1 ,0,1,1)
        self.uiLayout.addWidget(self.threshButton,2 ,0,1,1)
        self.uiLayout.addWidget(self.fitButton,3 ,0,1,1)
        self.uiLayout.addWidget(self.cButton,4 ,0,1,1)

    def setUpPlots(self):
        # a figure instance to plot on
        self.figure = Figure()
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.plotLayout = QtGui.QGridLayout()
        self.plotLayout.addWidget(self.canvas,0,0)
        self.plotLayout.addWidget(self.toolbar,1,0)

    def setUpMainWidget(self):
        self.mainWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.addLayout(self.uiLayout,0,0)
        self.mainLayout.addLayout(self.plotLayout,0,1)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        self.show()

    def plotData(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if self.rawButton.isChecked():
            #Plot raw data
            for i in range(len(self.data["Cells"])):
                if self.data["Visible"][i]:
                    x = self.data["Xs"][i]
                    y = self.data["Ys"][i]
                    ax.plot(x,y, '.--',label=self.data["Cells"][i])
            ax.legend()
            ax.set_xlabel("Cycle number")
            ax.set_ylabel("Flourescence")
            if self.rawThresh != None and self.threshButton.isChecked():
                ax.axhline(self.rawThresh,color = 'k')

        if self.logButton.isChecked():
            #Plot log data
            for i in range(len(self.data["Cells"])):
                if self.data["Visible"][i]:
                    x = self.data["LogXs"][i]
                    y = self.data["LogYs"][i]
                    if self.thresh == None or self.fitButton.isChecked() == False:
                        p = ax.plot(x,y, '.--',label = self.data["Cells"][i])
                    else:
                        p = ax.plot(x,y, '.--')
                    alphaX, alphaY = self.data["AlphaCurves"][i].getData()
                    if self.thresh != None:
                        if self.fitButton.isChecked():
                            ax.plot(alphaX,alphaY,color=p[0].get_color(),label=self.data["Cells"][i] + " a= {0:.3}".format(self.data["Alphas"][i]))
                        if self.threshButton.isChecked():
                            ax.axvline(self.data["Hs"][i],color=p[0].get_color())
                    else:
                        ax.plot(alphaX,alphaY,color=p[0].get_color(),label=self.data["Cells"][i])
            #Hline at thresh value
            if self.thresh != None and self.threshButton.isChecked():
                ax.axhline(self.thresh,color = 'k')
            ax.legend()
            ax.set_xlabel("Cycle number")
            ax.set_ylabel("Log Flourescence")

        if self.cButton.isChecked() and self.cX != None:
            #Plot c period plot
            if self.call:
                slope, intercept, r_value, p_value, std_err = stats.linregress(self.cX,self.cY)
                efficiency =((10**(-slope)) -1 )*100.0
                ax.plot(self.cX,self.cY,'.',label="Efficiency {0:.4}% R2 {1:.3}".format(efficiency,r_value**2))
                ax.plot(self.cFitX,self.cFitY,'--',label="y= {0:.3}x + {1:.3}".format(slope,intercept))
                ax.legend()
                ax.set_ylabel("Log(initial concentration)")
                ax.set_xlabel("ct")
            else:
                slope, intercept, r_value, p_value, std_err = stats.linregress(self.cX,self.cY)
                ax.plot(self.cX,self.cY,'.')
                ax.plot(self.cFitX,self.cFitY,'--',label="y= {0:.3}x + {1:.3} R2 {2:.4}".format(slope,intercept,r_value**2))
                slope2, _, _, _ = np.linalg.lstsq(np.asarray(self.cX)[:,np.newaxis],self.cY)
                ax.plot(self.cX,self.cX*slope2, '-', label= "Force 0 ")
                ax.legend()
                ax.set_xlabel("Delta distance")
                ax.set_ylabel("Delta H")


        # refresh canvas
        self.canvas.draw()


if __name__ == '__main__':
    from QPCRAnalyser import QPCRAnalyser as QPCRA

    QPCRA1 = QPCRA()
    QPCRA1.run()
    exit()
