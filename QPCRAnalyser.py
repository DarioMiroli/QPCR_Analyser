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
        self.data = {"Files":[] ,"Cells":[], "Xs":[], "Ys":[]}
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
            self.plotRawData()

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

    def setUpUI(self):
        '''
        After loading a file sets up the main UI
        '''
        #Create the main widget for our application and set the layout
        mainWidget = QtGui.QWidget()
        mainLayout = QtGui.QGridLayout()

        #Top left add plot
        self.rawPlot = pg.PlotWidget()
        mainLayout.addWidget(self.rawPlot,0,0)

        #Top right add plot
        self.logPlot = pg.PlotWidget()
        mainLayout.addWidget(self.logPlot,0,1)

        #Bottom right plot
        self.cPlot = pg.PlotWidget()
        mainLayout.addWidget(self.cPlot,1,1)

        #Add layout to main window
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def plotRawData(self):
        self.rawPlot.clear()
        for i,cell in enumerate(self.data["Cells"]):
            curve = pg.PlotCurveItem(self.data["Xs"][i],self.data["Ys"][i],pen=(i,len(self.data["Cells"])))
            self.rawPlot.addItem(curve)

if __name__ == '__main__':
    from QPCRAnalyser import QPCRAnalyser as QPCRA

    QPCRA1 = QPCRA()
    QPCRA1.run()
    exit()
