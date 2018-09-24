import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph.ptime import time as ptime
from scipy import stats
from scipy import interpolate
from scipy.optimize import curve_fit
import numpy as np
import time
import math
import datetime
import os
from functools import partial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
import FlowCytometryTools
from FlowCytometryTools import FCMeasurement as FCM
from FlowCytometryTools import ThresholdGate, PolyGate, IntervalGate
from scipy.stats import gaussian_kde

import matplotlib
matplotlib.rcParams["savefig.directory"] = "./Graphs"

class FlowCytometryAnalyser(QtGui.QWidget):
    '''
    Main application window. Handles live plotting and allows access to data viewer
    and callibration UIs.
    '''

    def __init__(self,parent=None):
        '''
        Constructor for the entire graphing application.
        '''
        self.app = QtGui.QApplication([])
        QtGui.QWidget.__init__(self,parent)
        self.dataDic = {"FileNames":[],"Data":[]}
        self.UIDic = {"FileSelectors":[],"XAxisSelectors":[],"YAxisSelectors":[],"LogXAxis":[],
                        "LogYAxis":[],"Plots":[],"PlotLegends":[],"GateCheckBoxes":[],"GateTypeSelector":[],"ROIs":[],
                        "PlotData":[],"SaveBtns":[],"AverageBtns":[],"AverageReigons":[],"AverageReigonCurves":[]}
        self.setUpUIWidgets()
        self.setUpPlotWidget()
        self.setUpMainWidget()
        self.show()

    def run(self):
        '''
        Starts the main application window. Is blocking.
        '''
        self.app.exec_()

    def setUpPlotWidget(self):
        '''
        Creates plots for linear and log data
        '''
        #Set default background and foreground colors for plots
        pg.setConfigOption('background', (40,40,40))
        pg.setConfigOption('foreground', (220,220,220))
        # Generate grid of plots
        self.plotLayout = QtGui.QGridLayout()

        #self.UIDic["Plots"].append(pg.PlotWidget())
        #self.UIDic["Plots"][0].addLegend()
        #self.UIDic["Plots"]Legends.append(self.UIDic["Plots"][0].plotItem.legend)
        #self.UIDic["Plots"][0].showGrid(x=True,y=True)
        #self.plotLayout.addWidget(self.UIDic["Plots"][0],0,0)

    def setUpUIWidgets(self):
        '''
        Creates all not grpahing UI elements and adds them to the applicatiom
        '''
        self.UILayout = QtGui.QVBoxLayout()

        #File selection for output button and label to display output path
        self.selectFileBtn = QtGui.QPushButton("Load manual data")
        self.selectFileBtn.setToolTip("Choose the file to load.")
        self.selectFileBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        self.selectFileBtn.setIconSize(QtCore.QSize(24,24))
        self.UILayout.addWidget(self.selectFileBtn)
        self.selectFileBtn.clicked.connect(self.onLoadFilePress)

        #File selection for output button and label to display output path
        self.addPlotBtn = QtGui.QPushButton("Add plot")
        self.addPlotBtn.setToolTip("Add a plot to the grid.")
        self.addPlotBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        self.addPlotBtn.setIconSize(QtCore.QSize(24,24))
        self.UILayout.addWidget(self.addPlotBtn)
        self.addPlotBtn.clicked.connect(self.onAddPlotPress)

    def setUpMainWidget(self):
        '''
        Combines the UI widgets and the plot widgets to build the final application.
        '''

        self.setWindowTitle('Growth rate plotter')

        #Define relative layout of plotting area and UI widgets
        self.resize(800,450)
        mainLayout = QtGui.QGridLayout()
        mainLayout.setColumnStretch(0,1)
        #mainLayout.setColumnStretch(1,4)
        #mainLayout.setRowStretch(2,5)

        mainLayout.addLayout(self.plotLayout,0,1)

        # Adds all UI widgets to a vertical scroll area.
        self.scrollWidget = QtGui.QWidget()
        self.UILayout.setSpacing(0)
        self.UILayout.addStretch(0)
        self.scrollWidget.setLayout(self.UILayout)
        self.scroll = QtGui.QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scrollWidget)
        self.scroll.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Expanding)
        #scroll.setMaximumSize(self.UILayout.geometry().width()*1.3,2000)
        #scroll.setMinimumSize(self.UILayout.geometry().width()*1.3,200)
        self.scroll.setWidgetResizable(True)
        vLayout = QtGui.QVBoxLayout()
        vLayout.addWidget(self.scroll)
        mainLayout.addLayout(vLayout,0,0)
        self.setLayout(mainLayout)

    def onLoadFilePress(self):
        '''
        Opens the chosen file and plots data
        '''
        filePath, filter = QtGui.QFileDialog.getOpenFileName(self,
                'Open File', './    ',filter="*.fcs")
        if filePath != "":
            self.loadFile(filePath)

    def loadFile(self,path):
        sample = FCM(ID='Test Sample', datafile=path)
        self.dataDic["FileNames"].append(os.path.basename(path))
        self.dataDic["Data"].append(sample)
        self.onFileAdded()

    def onAddPlotPress(self):
        self.addPlot()

    def addPlot(self):
        plotBox = QtGui.QGroupBox("Plot {}".format(len(self.UIDic["Plots"])+1))
        plotBoxLayout = QtGui.QGridLayout()
        plotBox.setLayout(plotBoxLayout)

        #Add file combo box
        plotBoxLayout.addWidget(QtGui.QLabel("File"),0,0,1,2)
        fileSelector = QtGui.QComboBox()
        fileSelector.addItems(self.dataDic["FileNames"])
        plotBoxLayout.addWidget(fileSelector,1,0,1,2)
        fileSelector.currentIndexChanged.connect(self.onFileChanged)
        self.UIDic["FileSelectors"].append(fileSelector)

        #Get file name
        fileNameIndex = self.dataDic["FileNames"].index(str(fileSelector.currentText()))
        #Add xaxis selector
        plotBoxLayout.addWidget(QtGui.QLabel("X axis"),2,0,1,2)
        xAxisSelector = QtGui.QComboBox()
        xAxisSelector.addItems(self.dataDic["Data"][fileNameIndex].channel_names)
        xAxisSelector.currentIndexChanged.connect(self.onAxisChange)
        plotBoxLayout.addWidget(xAxisSelector,3,0)
        self.UIDic["XAxisSelectors"].append(xAxisSelector)

        #Add checkbox for logging x axis
        logXAxis = QtGui.QCheckBox("Log x axis")
        plotBoxLayout.addWidget(logXAxis,2,1)
        logXAxis.clicked.connect(self.onLogChange)
        self.UIDic["LogXAxis"].append(logXAxis)

        #Add yaxis selector
        plotBoxLayout.addWidget(QtGui.QLabel("Y axis"),4,0,1,2)
        yAxisSelector = QtGui.QComboBox()
        yAxisSelector.addItems(self.dataDic["Data"][fileNameIndex].channel_names+("Events",))
        yAxisSelector.currentIndexChanged.connect(self.onAxisChange)
        plotBoxLayout.addWidget(yAxisSelector,5,0)
        self.UIDic["YAxisSelectors"].append(yAxisSelector)

        #Add checkbox for logging y axis
        logYAxis = QtGui.QCheckBox("Log y axis")
        plotBoxLayout.addWidget(logYAxis,4,1)
        logYAxis.clicked.connect(self.onLogChange)
        self.UIDic["LogYAxis"].append(logYAxis)

        #Add gate checkbox
        gateCheckBox = QtGui.QCheckBox("Gate on this channel")
        gateCheckBox.clicked.connect(self.onGate)
        self.UIDic["GateCheckBoxes"].append(gateCheckBox)
        plotBoxLayout.addWidget(gateCheckBox,6,0,1,1)

        #Add ROI type selector
        roiSelector = QtGui.QComboBox()
        roiSelector.addItem("square")
        self.UIDic["GateTypeSelector"].append(roiSelector)
        plotBoxLayout.addWidget(roiSelector,6,1,1,1)

        #Add add average reigon button
        addAverageButton = QtGui.QPushButton("Add average")
        addAverageButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        addAverageButton.setIconSize(QtCore.QSize(24,24))
        addAverageButton.clicked.connect(self.onAddAverage)
        self.UIDic["AverageBtns"].append(addAverageButton)
        plotBoxLayout.addWidget(addAverageButton,7,0,1,1)

        #Add save file button
        savePlotsButton = QtGui.QPushButton("Save plots")
        savePlotsButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        savePlotsButton.setIconSize(QtCore.QSize(24,24))
        savePlotsButton.clicked.connect(self.onSavePlot)
        self.UIDic["SaveBtns"].append(savePlotsButton)
        plotBoxLayout.addWidget(savePlotsButton,7,1,1,1)

        #Add entry to ROI list
        self.UIDic["ROIs"].append(-1)
        self.UIDic["PlotData"].append(-1)

        #Add plot
        self.UIDic["Plots"].append(pg.PlotWidget(padding=0))
        self.UIDic["Plots"][-1].addLegend()
        self.UIDic["PlotLegends"].append(self.UIDic["Plots"][-1].plotItem.legend)
        self.UIDic["Plots"][-1].showGrid(x=True,y=True)
        x,y = self.plotNoToGridCoords(len(self.UIDic["Plots"]))
        self.plotLayout.addWidget(self.UIDic["Plots"][-1],y,x)
        self.UIDic["AverageReigons"].append([])

        #Add group box to UI
        self.UILayout.insertWidget(1+len(self.UIDic["Plots"]),plotBox)

        #Resize plot
        width = max(self.UILayout.sizeHint().width(),plotBoxLayout.sizeHint().width()+2.0*self.UILayout.contentsMargins().left())
        self.scroll.setMinimumWidth(width + self.scroll.verticalScrollBar().sizeHint().width())

    def plotNoToGridCoords(self,n):
        if n <= 9 :
            coords = [[0,0],[1,0],[0,1],[1,1],[2,0],[2,1],[0,2],[1,2],[2,2]][n-1]
        if n > 9:
            coords = [n%3,math.ceil(n/3.0)-1]
        return coords[0], coords[1]

    def onFileAdded(self):
        for selector in self.UIDic["FileSelectors"]:
            selector.addItems([self.dataDic["FileNames"][-1]])

    def onFileChanged(self):
        index = self.UIDic["FileSelectors"].index(self.sender())
        plot = self.UIDic["Plots"][index]
        xSelect = self.UIDic["XAxisSelectors"][index]
        fileIndex = self.dataDic["FileNames"].index(str(self.sender().currentText()))
        xSelect.clear()


        ySelect = self.UIDic["YAxisSelectors"][index]
        fileIndex = self.dataDic["FileNames"].index(str(self.sender().currentText()))
        ySelect.clear()
        ySelect.addItems(self.dataDic["Data"][fileIndex].channel_names+("Events",))
        xSelect.addItems(self.dataDic["Data"][fileIndex].channel_names)

        self.rePlot(index,fileIndex)

    def rePlot(self,UIIndex,fileIndex):
        #Clear plot and replot
        plot = self.UIDic["Plots"][UIIndex]
        plot.clear()
        xSelect = self.UIDic["XAxisSelectors"][UIIndex]
        ySelect = self.UIDic["YAxisSelectors"][UIIndex]

        #Check if we are gating and if yes gate
        gating = False
        for checkBox in self.UIDic["GateCheckBoxes"]:
            if checkBox.isChecked():
                gating=True
                gateIndex = self.UIDic["GateCheckBoxes"].index(checkBox)
                break
        if gating:
            #Get coords of
            data = self.dataDic["Data"][fileIndex]
            roi = self.UIDic["ROIs"][gateIndex]
            gateBounds = roi.parentBounds()
            x1 = gateBounds.bottomLeft().x()
            x2 = gateBounds.bottomRight().x()
            y1 = gateBounds.topLeft().y()
            y2 = gateBounds.bottomRight().y()
            xChannel = str(self.UIDic["XAxisSelectors"][gateIndex].currentText())
            yChannel = str(self.UIDic["YAxisSelectors"][gateIndex].currentText())
            gate = PolyGate([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],channels = [xChannel,yChannel])
            data = data.gate(gate)
        else:
            data = self.dataDic["Data"][fileIndex]


        if str(ySelect.currentText()) == "Events":
            z = data[str(xSelect.currentText())]
            if len(z) > 0:
                y,x = np.histogram(z, bins=np.linspace(min(z), max(z), max(z)/500))
                curve = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 80))
                for reigon in self.UIDic["AverageReigons"][UIIndex]:
                    x1,x3
            else:
                curve = pg.PlotCurveItem([], [])

        else:
            curve = pg.ScatterPlotItem(pen=None,brush=(1,2),pxMode=True,size=2)
            x = data[str(xSelect.currentText())]
            y = data[str(ySelect.currentText())]
            if self.UIDic["LogXAxis"][UIIndex].isChecked():
                #x = np.sign(x)* np.log10(abs(x) + 1)
                x = np.log(x + abs(min(x)) + 1)
            if self.UIDic["LogYAxis"][UIIndex].isChecked():
                #y = np.sign(y)* np.log10(abs(y) + 1)
                y = np.log(y + abs(min(y)) + 1)
            curve.setData(x,y)
        self.UIDic["PlotData"][UIIndex] = data
        self.UIDic["Plots"][UIIndex].addItem(curve)
        #Add axis labels
        self.UIDic["Plots"][UIIndex].setLabel('left', str(self.UIDic["YAxisSelectors"][UIIndex].currentText()))
        self.UIDic["Plots"][UIIndex].setLabel('bottom', str(self.UIDic["XAxisSelectors"][UIIndex].currentText()))

        #Add reigons we cleared
        if str(ySelect.currentText()) == "Events":
            for reigon in self.UIDic["AverageReigons"][UIIndex]:
                self.UIDic["Plots"][UIIndex].addItem(reigon)

    def onAxisChange(self):
        try:
            uiIndex = self.UIDic["XAxisSelectors"].index(self.sender())
        except:
            uiIndex = self.UIDic["YAxisSelectors"].index(self.sender())
        if  str(self.UIDic["XAxisSelectors"][uiIndex].currentText()) != '' and str(self.UIDic["YAxisSelectors"][uiIndex].currentText()) != '':
            fileIndex = self.dataDic["FileNames"].index(str(self.UIDic["FileSelectors"][uiIndex].currentText()))
            if self.UIDic["GateCheckBoxes"][uiIndex].isChecked():
                self.UIDic["GateCheckBoxes"][uiIndex].animateClick()
            else:
                self.rePlot(uiIndex,fileIndex)

    def onLogChange(self):
        checkBox = self.sender()
        try:
            uiIndex = self.UIDic["LogXAxis"].index(checkBox)
        except:
            uiIndex = self.UIDic["LogYAxis"].index(checkBox)
        fileName = str(self.UIDic["FileSelectors"][uiIndex].currentText())
        fileIndex = self.dataDic["FileNames"].index(fileName)
        self.rePlot(uiIndex,fileIndex)

    def onGate(self):
        on = self.sender().isChecked()
        UIIndex = self.UIDic["GateCheckBoxes"].index(self.sender())
        #Check if ROI holds -1 and thus is first time this ROI has been interacted with
        if self.UIDic["ROIs"][UIIndex] == -1:
            self.UIDic["ROIs"][UIIndex] = pg.RectROI([1,1],[1,1], pen=(0,9),centered=False)

        #Turn off all check boxes remove ROIS
        for i,checkBox in enumerate(self.UIDic["GateCheckBoxes"]):
            checkBox.setChecked(False)
            try:
                self.UIDic["Plots"][i].removeItem(self.UIDic["ROIs"][i])
            except:
                pass

        #Then replot each graph
        for i in range(len(self.UIDic["Plots"])):
            fIndex = self.dataDic["FileNames"].index(str(self.UIDic["FileSelectors"][i].currentText()))
            self.rePlot(i,fIndex)

        #If we meant to turn a gate on
        if on:
            self.sender().setChecked(True)
            plot = self.UIDic["Plots"][UIIndex]
            plotData = self.UIDic["PlotData"][UIIndex]
            #ROIS?
            xData = plotData[str(self.UIDic["XAxisSelectors"][UIIndex].currentText())]
            yData = plotData[str(self.UIDic["YAxisSelectors"][UIIndex].currentText())]
            minX = min(xData)
            maxX = max(xData)
            minY = min(yData)
            maxY = max(yData)
            ix = minX
            iy = minY
            xSpan = abs(maxX-minX)
            ySpan = abs(maxY-minY)
            bounds = QtCore.QRectF(ix,iy,xSpan,ySpan)
            self.UIDic["ROIs"][UIIndex] = pg.RectROI([ix,iy], [xSpan,ySpan], pen=(0,9),centered=False,maxBounds=bounds)
            self.UIDic["ROIs"][UIIndex].addScaleHandle((0,0),(1,1))
            self.UIDic["ROIs"][UIIndex].addScaleHandle((0,1),(1,0))
            self.UIDic["ROIs"][UIIndex].addScaleHandle((1,0),(0,1))
            self.UIDic["ROIs"][UIIndex].addScaleHandle((0,0.5),(1,0.5))
            self.UIDic["ROIs"][UIIndex].addScaleHandle((0.5,0),(0.5,1))
            self.UIDic["ROIs"][UIIndex].addScaleHandle((1,0.5),(0,0.5))
            self.UIDic["ROIs"][UIIndex].addScaleHandle((0.5,1),(0.5,0))
            self.UIDic["ROIs"][UIIndex].sigRegionChangeFinished.connect(self.onROIMove)
            plot.addItem(self.UIDic["ROIs"][UIIndex])
            self.onROIMove()

    def onROIMove(self):
        for i in range(len(self.UIDic["Plots"])):
            uiIndex = i
            if not self.UIDic["GateCheckBoxes"][i].isChecked():
                fileIndex = self.dataDic["FileNames"].index(str(self.UIDic["FileSelectors"][i].currentText()))
                self.rePlot(uiIndex,fileIndex)

    def onSavePlot(self):
        i = self.UIDic["SaveBtns"].index(self.sender())
        self.savePlot("",i)

    def savePlot(self,fileName,UIIndex):
        plot = self.UIDic["Plots"][UIIndex]
        yAxisLabel = str(self.UIDic["YAxisSelectors"][UIIndex].currentText())
        xAxisLabel = str(self.UIDic["XAxisSelectors"][UIIndex].currentText())
        curves = plot.listDataItems()
        for curve in curves:
            x, y = curve.getData()
            if yAxisLabel != "Events":
                if type(curve) == type(pg.ScatterPlotItem()):
                    #plt.plot(x,y,'.',markersize=0.1)
                    #plt.hexbin(x,y,gridsize=100,cmap='jet',bins='log')
                    SaveWindow(UIIndex,self.dataDic,self.UIDic)
            else:
                data = self.UIDic["PlotData"][UIIndex][xAxisLabel]
                #plt.hist(data,bins=300)
                SaveWindow(UIIndex,self.dataDic,self.UIDic)

        #plt.title(str(self.UIDic["FileSelectors"][UIIndex].currentText()))
        #plt.xlabel(xAxisLabel)
        #plt.ylabel(yAxisLabel)
        #plt.show()

    def onAddAverage(self):
        uiIndex = self.UIDic["AverageBtns"].index(self.sender())
        plot = self.UIDic["Plots"][uiIndex]
        #Get x values
        plotData = self.UIDic["PlotData"][uiIndex]
        #ROIS?
        xData = plotData[str(self.UIDic["XAxisSelectors"][uiIndex].currentText())]
        minX = min(xData)
        maxX = max(xData)
        hReigon = pg.LinearRegionItem([minX,0.1*maxX],movable=True,bounds=[minX,maxX])
        hReigon.sigRegionChangeFinished.connect(self.onAverageMove)
        plot.addItem(hReigon)
        self.UIDic["AverageReigons"][uiIndex].append(hReigon)

    def onAverageMove(self):
        #Get correct plot
        uiIndex = None
        for i in range(len(self.UIDic["AverageReigons"])):
            if self.sender() in self.UIDic["AverageReigons"][i]:
                uiIndex = i
        self.UIDic["PlotLegends"][uiIndex].items = []
        if uiIndex != None:
            plot = self.UIDic["Plots"][uiIndex]
            data = self.UIDic["PlotData"][uiIndex]
            for c,reigon in enumerate(self.UIDic["AverageReigons"][i]):
                color = pg.mkColor((c,len(self.UIDic["AverageReigons"][uiIndex])))
                color.setAlpha(int(100))
                reigon.setBrush(color)
                xmin,xmax = reigon.getRegion()
                gate = IntervalGate((xmin,xmax),channel=str(self.UIDic["XAxisSelectors"][uiIndex].currentText()),region='in')
                gated = data.gate(gate)
                mean = gated[str(self.UIDic["XAxisSelectors"][uiIndex].currentText())].mean()
                color.setAlpha(int(255))
                self.UIDic["PlotLegends"][uiIndex].addItem(pg.PlotDataItem(pen=color),"{}".format(mean))
                x1,x2 = reigon.getRegion()
                xfit,yfit = self.getHistogramFit(1,2,x1,x2)
                print(xfit,yfit)
                curve = pg.PlotCurveItem(xfit, yfit)
                self.UIDic["Plots"][uiIndex].addItem(curve)


    def getHistogramFit(self,x,y,x1,x2):
        def gaussian(x,a,b,c):
            y = a * np.exp((-1.0*(x-b)**2)/(2*(c**2)))
            return y
        xfit = np.linspace(x1,x2,10)
        yfit = [i for i in xfit]
        return xfit, yfit



class SaveWindow(QtGui.QMainWindow):

    def __init__(self,uiIndex,dataDic,UIDic,parent=None):
        QtGui.QMainWindow.__init__(self,parent)
        self.dataDic = dataDic
        self.UIDic = UIDic
        self.uiIndex = uiIndex
        self.setWindowTitle("Saveplot")
        self.setUpUI()
        self.setUpPlots()
        self.setUpMainWidget()
        self.plotData()

    def setUpUI(self):
        self.uiLayout = QtGui.QGridLayout()

        if str(self.UIDic["YAxisSelectors"][self.uiIndex].currentText()) != "Events":
            self.scatterButton = QtGui.QRadioButton("Scatter")
            self.scatterButton.setChecked(True)
            self.hexBinButton = QtGui.QRadioButton("Hexbins")
            self.scatterButton.clicked.connect(self.plotData)
            self.hexBinButton.clicked.connect(self.plotData)
            self.uiLayout.addWidget(self.scatterButton,0,0,1,1)
            self.uiLayout.addWidget(self.hexBinButton,1 ,0,1,1)

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
        fileName = str(self.UIDic["FileSelectors"][self.uiIndex].currentText())
        xlabel = str(self.UIDic["XAxisSelectors"][self.uiIndex].currentText())
        ylabel = str(self.UIDic["YAxisSelectors"][self.uiIndex].currentText())
        data = self.UIDic["PlotData"][self.uiIndex]
        xdata = data[xlabel]

        # create an axis
        ax = self.figure.add_subplot(111)
        # discards the old graph
        ax.clear()
        # plot data
        if ylabel != "Events":
            ydata = data[ylabel]
            if self.scatterButton.isChecked():
                ax.plot(xdata.values,ydata.values, '.', markersize = 1,zorder=1)
            else:
                ax.hexbin(xdata.values,ydata.values,gridsize=100,cmap='jet',bins='log',zorder=1)
            if self.UIDic["GateCheckBoxes"][self.uiIndex].isChecked():
                roi = self.UIDic["ROIs"][self.uiIndex]
                gateBounds = roi.parentBounds()
                x1 = gateBounds.bottomLeft().x()
                x2 = gateBounds.bottomRight().x()
                y1 = gateBounds.topLeft().y()
                y2 = gateBounds.bottomRight().y()
                rect = patches.Rectangle((x1,y1),x2-x1,y2-y1,linewidth=1,edgecolor='r',facecolor='none',zorder=2,label="gate")
                ax.add_patch(rect)
                ax.legend()
        else:
            ax.hist(xdata.values,bins=300)
            nCols = len(self.UIDic["AverageReigons"][self.uiIndex])
            for c,reigon in enumerate(self.UIDic["AverageReigons"][self.uiIndex]):
                x1,x2 = reigon.getRegion()
                color = pg.intColor(c,nCols)
                r,g,b,a = color.getRgb()
                #Compute mean
                gate = IntervalGate((x1,x2),channel=xlabel,region='in')
                gated = data.gate(gate)
                mean = gated[xlabel].mean()
                ax.axvspan(x1, x2, alpha=0.5,label=mean,facecolor=(r/255.0,g/255.0,b/255.0))
                ax.legend()

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(fileName)
        # refresh canvas
        self.canvas.draw()

if __name__ == '__main__':
    from Test import FlowCytometryAnalyser

    FCA1 = FlowCytometryAnalyser()
    FCA1.run()
    exit()
