import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import os

class QPCRAnalyser(QtGui.QMainWindow):
    ''' class for analysing QPCR data for C period determination '''

    def __init__(self,parent=None):
        '''
        Constructor for the analyser GUI
        '''
        #Start with essential data structures
        self.data = {"Files":[] ,"Cells":[], "Xs":[], "Ys":[],"Visible":[],"RawCurves":[],"LogCurves":[],"Hs":[],"HCurves":[]}
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
                self.data["RawCurves"].append(pg.PlotCurveItem(x,y))
                self.data["LogCurves"].append(pg.PlotDataItem(x,np.log(y),symbol='o',symbolSize=5,symbolPen=None))
                self.data["Hs"].append(-1)
                self.data["HCurves"].append(pg.InfiniteLine())

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
        mainLayout.addWidget(self.rawPlot,0,0)

        #Top right add plot and slider
        logPlotLayout = QtGui.QGridLayout()
        self.logPlot = pg.PlotWidget()
        self.logPlot.showGrid(x=True,y=True)
        logPlotLayout.addWidget(self.logPlot,0,0)
        mainLayout.addLayout(logPlotLayout,0,1)

        #Bottom right plot
        self.cPlot = pg.PlotWidget()
        self.cPlot.showGrid(x=True,y=True)
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
                curve.setPen((j,n))
                self.data["LogCurves"][i].setPen(None)#(j,n))
                self.data["LogCurves"][i].setSymbolBrush((j,n))
                if len(self.data["HCurves"]) > 0:
                    self.data["HCurves"][i].setPen((j,n))
                j+=1

    def onSelectThresh(self):
        num,ok = QtGui.QInputDialog.getDouble(self,"Select threshold","Enter threshold value")
        if ok:
            try:
                self.logPlot.removeItem(self.threshLine)
            except:
                pass
            #Add horizontal line at value
            self.threshold = num
            self.threshLine  = pg.InfiniteLine(angle=0,pos=self.threshold)
            self.logPlot.addItem(self.threshLine)
            self.computeHs()

    def computeHs(self):
        '''
        Compute the cycle at which the selected data crosses the threshold value
        '''
        for i in range(len(self.data["Xs"])):
            xs = self.data["Xs"][i]
            ys = np.log(self.data["Ys"][i])
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
                    print(x1,x2,h)
                    self.data["Hs"][i] = h
                    try:
                        vline = pg.InfiniteLine(angle=90,pos=h,pen=self.data["LogCurves"][i].opts["symbolBrush"])
                    except:
                        vline = pg.InfiniteLine(angle=90,pos=h,pen=self.data["LogCurves"][i].opts["symbolBrush"].color())
                    self.data["HCurves"][i] = vline
                    if self.data["Visible"][i]:
                        self.logPlot.addItem(vline)
                    break


if __name__ == '__main__':
    from QPCRAnalyser import QPCRAnalyser as QPCRA

    QPCRA1 = QPCRA()
    QPCRA1.run()
    exit()
