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
        self.data = {"Files":[] ,"Cells":[], "Xs":[], "Ys":[],"Visible":[],"RawCurves":[]}
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

        #Top right add plot
        self.logPlot = pg.PlotWidget()
        self.logPlot.showGrid(x=True,y=True)
        mainLayout.addWidget(self.logPlot,0,1)

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
                    self.data["Visible"][i] = True
                else:
                    self.rawPlot.removeItem(self.data["RawCurves"][i])
                    self.data["Visible"][i] = False
        n = np.sum(self.data["Visible"])
        j= 0
        for i,curve in enumerate(self.data["RawCurves"]):
            if self.data["Visible"][i]:
                curve.setPen((j,n))
                j+=1

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubberband.setGeometry(
            QtCore.QRect(self.origin, QtCore.QSize()))
        self.rubberband.show()
        QtGui.QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.rubberband.isVisible():
            self.rubberband.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
        QtGui.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.rubberband.isVisible():
            self.rubberband.hide()
            selected = []
            rect = self.rubberband.geometry()
            for child in self.findChildren(QtGui.QPushButton):
                if rect.intersects(child.geometry()):
                    selected.append(child)
            for btn in selected:
                #btn.setChecked(True)
                btn.animateClick()
            QtGui.QWidget.mouseReleaseEvent(self, event)

if __name__ == '__main__':
    from QPCRAnalyser import QPCRAnalyser as QPCRA

    QPCRA1 = QPCRA()
    QPCRA1.run()
    exit()
