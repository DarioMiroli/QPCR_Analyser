import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph.ptime import time as ptime
from scipy import stats
from scipy import interpolate
import numpy as np
import time
import datetime
import os
from functools import partial
import matplotlib.pyplot as plt
from aqua.qsshelper import QSSHelper
import sip
import xlrd

class GrowthCurveApp(QtGui.QWidget):
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
        self.dataDic = {"ID":[],"FileNames":[],"Times":[], "ODs":[], "MinSliders":[],"MaxSliders":[],
                        "CheckBoxes":[], "DeleteButtons":[], "GroupBoxes":[], "DoublingTimes":[],
                        "LinearPlots":[], "LogPlots":[], "LogFitPlots":[], "OriginFiles":[],"Types":[]}
        self.plateDics = []
        self.nextID = 0
        self.setUpPlotWidget()
        self.setUpUIWidgets()
        self.setUpMainWidget()

        #Style sheet stuff
        self.styleSheetPath = os.path.join(os.path.abspath(os.path.dirname(__file__)),"aqua")
        qss = QSSHelper.open_qss(os.path.join(self.styleSheetPath,"aqua.qss"))
        self.app.setStyleSheet(qss)

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
        self.linearPlot = pg.PlotWidget()
        self.linearPlot.addLegend()
        self.linearLegend = self.linearPlot.plotItem.legend

        self.logPlot = pg.PlotWidget()
        self.logPlot.addLegend()
        self.logLegend = self.logPlot.plotItem.legend
        self.linearCurves = []
        self.logCurves = []

        #Add axis lables to plots
        self.linearPlot.setLabels(left='OD')
        self.linearPlot.setLabels(bottom=('Time', 'hours'))
        self.linearPlot.setLabels(top="Linear Plot")
        self.linearPlot.showGrid(x=True,y=True)

        self.logPlot.setLabels(left='Log OD')
        self.logPlot.setLabels(bottom=('Time', 'hours   '))
        self.logPlot.setLabels(top="Log Plot")
        self.logPlot.showGrid(x=True,y=True)

        self.plotLayout.addWidget(self.linearPlot,0,0)
        self.plotLayout.addWidget(self.logPlot,1,0)

    def setUpUIWidgets(self):
        '''
        Creates all not grpahing UI elements and adds them to the applicatiom
        '''
        self.UILayout = QtGui.QVBoxLayout()

        #File selection for output button and label to display output path
        self.convertBioDataBtn = QtGui.QPushButton("ConvertBioData")
        self.convertBioDataBtn.setToolTip("Open bioreactor data to convert.")
        self.convertBioDataBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_BrowserReload))
        self.convertBioDataBtn.setIconSize(QtCore.QSize(24,24))
        self.UILayout.addWidget(self.convertBioDataBtn)
        self.convertBioDataBtn.clicked.connect(self.onLoadBioDataPress)


        #File selection for output button and label to display output path
        self.selectFileBtn = QtGui.QPushButton("Load manual data")
        self.selectFileBtn.setToolTip("Choose the file to load.")
        self.selectFileBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        self.selectFileBtn.setIconSize(QtCore.QSize(24,24))
        self.UILayout.addWidget(self.selectFileBtn)
        self.selectFileBtn.clicked.connect(self.onLoadFilePress)

        #File selection for biolector
        self.selectBiolectorFileBtn = QtGui.QPushButton("Load biolector data")
        self.selectBiolectorFileBtn.setToolTip("Choose the file to load.")
        self.selectBiolectorFileBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        self.selectBiolectorFileBtn.setIconSize(QtCore.QSize(24,24))
        self.UILayout.addWidget(self.selectBiolectorFileBtn)
        self.selectBiolectorFileBtn.clicked.connect(self.onLoadBiolectorPress)

        #File select for opening plate
        self.openPlateBtn = QtGui.QPushButton("Load plate")
        self.openPlateBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        self.openPlateBtn.setIconSize(QtCore.QSize(24,24))
        self.UILayout.addWidget(self.openPlateBtn)
        self.openPlateBtn.clicked.connect(self.onOpenPlatePress)

        #For saving plots
        self.savePlotBtn = QtGui.QPushButton("Save plots")
        self.savePlotBtn.setToolTip("Choose the file to which recordings will be saved.")
        self.savePlotBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogSaveButton))
        self.savePlotBtn.setIconSize(QtCore.QSize(24,24))
        self.savePlotBtn.clicked.connect(self.onSavePlotPush)
        self.UILayout.addWidget(self.savePlotBtn)

        #Table for doubling times
        self.dataTable = QtGui.QTableWidget()
        self.dataTable.setRowCount(0)
        self.dataTable.setColumnCount(3)
        self.dataTable.setHorizontalHeaderLabels(["File","Doubling Time","Error"])
        self.dataTable.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.dataTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.dataTable.cellChanged.connect(self.onTableEdit)

        #Smoothing slider
        #self.smoothingSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        #self.UILayout.addWidget(self.smoothingSlider)
        #self.smoothingSlider.setMinimum(0)
        #self.smoothingSlider.setMaximum(100)
        #self.smoothingSlider.valueChanged.connect(self.onSmoothSliderChange)

        header = self.dataTable.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        self.UILayout.addWidget(self.dataTable)

        self.slidersList = []
        self.deleteBtnList = []
        self.toggleList = []
        self.UILayout.setSpacing(0)

    def setUpMainWidget(self):
        '''
        Combines the UI widgets and the plot widgets to build the final application.
        '''


        self.setWindowTitle('Growth rate plotter')

        #Define relative layout of plotting area and UI widgets
        self.resize(800,450)
        mainLayout = QtGui.QGridLayout()
        mainLayout.setColumnStretch(0,1)
        mainLayout.setColumnStretch(1,5)
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
        self.scrollWidget.setMinimumWidth(self.getQTableWidgetSize(self.dataTable).width())

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
        self.dataTable.blockSignals(True)
        filePath, filter = QtGui.QFileDialog.getOpenFileName(self,
                'Open File', './    ',filter="*.csv")
        if filePath != "":
            self.loadData(filePath)
        self.dataTable.blockSignals(False)

    def loadData(self,filePath):
        times = []
        ODs = []
        dataFile = open(filePath)
        for line in dataFile.readlines():
            if line != "":
                splitArray = line.rstrip().split(",")
                splitArray = [i.rstrip().lstrip() for i in splitArray]
                time = splitArray[0] + " " + splitArray[1]
                dateTime = datetime.datetime.strptime(time, '%d/%m/%y %H:%M')
                times.append(dateTime)
                ODs.append(float(splitArray[-1]))

        startTime = times[0]
        for i in range(len(times)):
            times[i] = (((times[i] - startTime).total_seconds())/60.0)/60.0
        fileName = filePath.split("/")[-1]
        #fileName = self.getUniqueFileName(fileName)
        self.dataDic["ID"].append(self.nextID)
        self.nextID += 1
        self.dataDic["FileNames"].append(fileName)
        self.dataDic["Times"].append(times)
        self.dataDic["ODs"].append(ODs)
        self.dataDic["DoublingTimes"].append(-1)
        self.dataDic["OriginFiles"].append(fileName)
        self.dataDic["Types"].append("Manual")

        count = sum([1 for j in range(len(ODs)) if ODs[j]-ODs[0] > 0])
        self.addSlider(self.dataDic["FileNames"][-1],0,count)
        self.addPlot()
        self.recolorPlots()

    def addPlot(self):
        x = self.dataDic["Times"][-1]
        y= np.asarray(self.dataDic["ODs"][-1])
        y = [i-y[0] for i in y]
        #y = [i-y[0] for i in y]
        linearPlot = pg.ScatterPlotItem(pen=(self.dataDic["ID"][-1],len(self.dataDic["ID"])))
        linearPlot.setData(x,y,label=self.dataDic["FileNames"][-1])
        self.dataDic["LinearPlots"].append(linearPlot)
        self.linearPlot.addItem(linearPlot)

        logPlot = pg.ScatterPlotItem(pen=(self.dataDic["ID"][-1],len(self.dataDic["ID"])))
        yLoged = [np.log(j) for j in y if j> 0]
        xLoged = [x[j] for j in range(len(x)) if y[j] > 0]
        logPlot.setData(xLoged,yLoged)
        self.dataDic["LogPlots"].append(logPlot)
        self.logPlot.addItem(logPlot)

        logFitPlot = pg.PlotCurveItem(pen=(self.dataDic["ID"][-1],len(self.dataDic["ID"])))

        xfit, yfit, doublingTime = self.getLogFit(self.dataDic["ID"][-1])
        logFitPlot.setData(xfit,yfit)
        self.logPlot.addItem(logFitPlot)
        #self.logLegend.addItem(logFitPlot,"y = {0:.3f}X + {1:.3f}".format(slope,intercept))
        self.dataDic["LogFitPlots"].append(logFitPlot)

        self.dataDic["DoublingTimes"][-1] = doublingTime
        self.dataTable.cellChanged.connect(self.onTableEdit)

        self.dataTable.insertRow(len(self.dataDic["ID"])-1)
        fileNameItem = QtGui.QTableWidgetItem(str(self.dataDic["FileNames"][-1]))
        self.dataTable.setItem(len(self.dataDic["ID"])-1,0,fileNameItem)

        doublingTimeItem = QtGui.QTableWidgetItem(str("{0:.3f}".format(doublingTime)))
        doublingTimeItem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.dataTable.setItem(len(self.dataDic["ID"])-1,1,doublingTimeItem)

        errorItem = QtGui.QTableWidgetItem(str("N/A"))
        errorItem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.dataTable.setItem(len(self.dataDic["ID"])-1,2,errorItem)

        #Resize UI
        self.resizeUIPannel()
        self.updateLegend()

    def removePlot(self,ID):
        index = self.dataDic["ID"].index(ID)
        self.linearPlot.removeItem(self.dataDic["LinearPlots"][index])

        self.logPlot.removeItem(self.dataDic["LogPlots"][index])

        self.logPlot.removeItem(self.dataDic["LogFitPlots"][index])
        self.recolorPlots()
        self.updateLegend()

    def checkBoxReplot(self,ID):
        ID = int(ID)
        index = self.dataDic["ID"].index(ID)
        if self.dataDic["CheckBoxes"][index].isChecked():
            self.linearPlot.addItem(self.dataDic["LinearPlots"][index])

            self.logPlot.addItem(self.dataDic["LogPlots"][index])
            self.logPlot.addItem(self.dataDic["LogFitPlots"][index])
        else:
            self.linearPlot.removeItem(self.dataDic["LinearPlots"][index])

            self.logPlot.removeItem(self.dataDic["LogPlots"][index])
            self.logPlot.removeItem(self.dataDic["LogFitPlots"][index])
        self.updateLegend()

    def sliderReplot(self,ID):
        index = self.dataDic["ID"].index(int(ID))
        xfit, yfit, doublingTime = self.getLogFit(int(ID))
        self.dataDic["LogFitPlots"][index].setData(xfit,yfit)
        doublingTimeItem = QtGui.QTableWidgetItem(str("{0:.3f}".format(doublingTime)))
        doublingTimeItem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.dataTable.setItem(index,1,doublingTimeItem)
        self.updateLegend()

    def addSlider(self,name,smin,smax):
        maxSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        maxSlider.setObjectName("{},max".format(self.dataDic["ID"][-1]))
        self.dataDic["MaxSliders"].append(maxSlider)
        self.dataDic["MaxSliders"][-1].setMinimum(smin)
        self.dataDic["MaxSliders"][-1].setMaximum(smax)
        self.dataDic["MaxSliders"][-1].setValue(smax)
        minSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.dataDic["MinSliders"].append(minSlider)
        minSlider.setObjectName("{},min".format(self.dataDic["ID"][-1]))
        self.dataDic["MinSliders"][-1].setMinimum(smin)
        self.dataDic["MinSliders"][-1].setMaximum(smax)

        self.dataDic["MaxSliders"][-1].valueChanged.connect(self.onSliderMove)
        self.dataDic["MinSliders"][-1].valueChanged.connect(self.onSliderMove)

        checkBox = QtGui.QCheckBox("show / hide")
        checkBox.setObjectName("{},checkBox".format(self.dataDic["ID"][-1]))
        checkBox.clicked.connect(self.onCheckBoxClick)
        checkBox.setChecked(True)
        self.dataDic["CheckBoxes"].append(checkBox)

        deleteBtn = QtGui.QPushButton("Delete")
        deleteBtn.clicked.connect(self.onDeleteBtnPress)
        deleteBtn.setObjectName("{}".format(self.dataDic["ID"][-1]))
        self.dataDic["DeleteButtons"].append(deleteBtn)

        sliderBox = QtGui.QGroupBox(name)
        sliderLayout = QtGui.QGridLayout()

        sliderLayout.addWidget(checkBox,0,0)
        sliderLayout.addWidget(self.dataDic["MinSliders"][-1],1,0,1,2)
        sliderLayout.addWidget(self.dataDic["MaxSliders"][-1],2,0,1,2)
        sliderLayout.addWidget(self.dataDic["DeleteButtons"][-1],0,1)
        sliderLayout.setSpacing(0)
        sliderBox.setLayout(sliderLayout)
        self.dataDic["GroupBoxes"].append(sliderBox)
        self.UILayout.insertWidget(self.UILayout.count()-1,sliderBox)

    def onSliderMove(self, index):
        ID, kind =  self.sender().objectName().split(",")[0],self.sender().objectName().split(",")[1]
        index = self.dataDic["ID"].index(int(ID))
        minSlider = self.dataDic["MinSliders"][index]
        maxSlider = self.dataDic["MaxSliders"][index]
        if kind == "min":
            #Minimum slider
            #If less than 2 gap between min and max sliders
            if minSlider.value() > maxSlider.value() -2:
                #Is max slider at max
                if maxSlider.value() == maxSlider.maximum():
                    minSlider.setValue(maxSlider.maximum() -2 )
                else:
                    maxSlider.setValue(minSlider.value() +2 )
        else:
            #Max slider
            if maxSlider.value() < minSlider.value() + 2:
                #Is min slider at min
                if minSlider.value() == minSlider.minimum():
                    maxSlider.setValue(minSlider.minimum()+2 )
                else:
                    minSlider.setValue(maxSlider.value()-2 )
        self.dataTable.blockSignals(True)
        self.sliderReplot(ID)
        self.dataTable.blockSignals(False)

    def onLoadBioDataPress(self):
        '''
        Opens the chosen file and adds to
        '''
        self.dataTable.blockSignals(True)
        filePath, filter = QtGui.QFileDialog.getOpenFileName(self,
                'Open File', '.',filter="*.TXT")
        if filePath != "":
            self.loadBioData(filePath)
        self.dataTable.blockSignals(False)

    def loadBioData(self,path):
        bioFile = open(path)
        times = []
        ODs = [ ]
        lines = bioFile.readlines()
        for i in range(len(lines[0].rstrip().split(","))-1):
            ODs.append([])

        for line in lines[1:]:
            if line != "":
                splitArray = line.rstrip().split(",")
                splitArray = [i.rstrip().lstrip() for i in splitArray]
                for i in range(len(splitArray)):
                    if i ==0:
                        times.append(float(splitArray[i]))
                    else:
                        ODs[i-1].append(float(splitArray[i]))
        tempNames = ["{}_{}".format(os.path.basename(path),i) for i in range(len(ODs))]
        for i in range(len(ODs)):
            fileName = tempNames[i]
            self.dataDic["ID"].append(self.nextID)
            self.nextID += 1
            self.dataDic["FileNames"].append(fileName)
            self.dataDic["OriginFiles"].append(fileName)
            self.dataDic["Types"].append("Bioreactor")
            self.dataDic["Times"].append(times)
            self.dataDic["ODs"].append(ODs[i])
            self.dataDic["DoublingTimes"].append(-1)
            count = sum([1 for j in range(len(ODs[i])) if ODs[i][j]-ODs[i][0] > 0])
            self.addSlider(fileName,0,count)
            self.addPlot()
        self.scrollWidget.repaint()
        self.resizeUIPannel()
        self.recolorPlots()

    def onSavePlotPush(self):
        fileName, filter = QtGui.QFileDialog.getSaveFileName(parent=self,caption='Select file name for raw OD plots', filter='*.png')
        if fileName != "":
            for i in range(len(self.dataDic["FileNames"])):
                if self.dataDic["CheckBoxes"][i].isChecked():
                    plt.plot(self.dataDic["Times"][i],self.dataDic["ODs"][i],".-",label=self.dataDic["FileNames"][i])
            plt.legend()
            plt.xlabel("Time hours")
            plt.ylabel("OD")
            plt.title("Raw ODs")
            plt.savefig(fileName, bbox_inches='tight')
            plt.show()

        fileName, filter = QtGui.QFileDialog.getSaveFileName(parent=self,
                caption='Select file name for fitted plots', filter='*.png')
        if fileName != "":
            cmap = plt.get_cmap('jet')
            j = 0
            for i in range(len(self.dataDic["FileNames"])):
                if self.dataDic["CheckBoxes"][i].isChecked():
                    color1 = cmap(float(j)/(len(self.linearLegend.items)))
                    color2 = cmap((float(j)+0.5)/(len(self.linearLegend.items)))
                    x,y = self.dataDic["LogPlots"][i].getData()
                    plt.plot(x,y,".",label=self.dataDic["FileNames"][i] + " DT: {0:.1f}".format(self.dataDic["DoublingTimes"][i]),c=color1,zorder=0)
                    x,y = self.dataDic["LogFitPlots"][i].getData()
                    plt.plot(x,y,linewidth=3,c= color2,zorder=10)
                    j +=1
            plt.legend()
            plt.xlabel("Time hours")
            plt.ylabel("Log(OD)")
            plt.title("Fits to Log(OD) curves")
            plt.savefig(fileName, bbox_inches='tight')
            plt.show()

    def onTableEdit(self):
        self.dataTable.blockSignals(True)
        nRows = self.dataTable.rowCount()
        for row in range(nRows):
            oldName = self.dataDic["FileNames"][row]
            newName = self.dataTable.item(row,0).text()
            #if name has been changed
            if oldName != newName:
                self.dataDic["FileNames"][row] = newName
                self.dataDic["GroupBoxes"][row].setTitle(newName)


        self.dataTable.blockSignals(False)
        self.resizeUIPannel()

    def onCheckBoxClick(self):
        self.dataTable.blockSignals(True)
        ID, kind =  self.sender().objectName().split(",")[0],self.sender().objectName().split(",")[1]
        self.checkBoxReplot(ID)
        self.dataTable.blockSignals(False)
        self.recolorPlots()

    def onDeleteBtnPress(self):
        ID =  int(self.sender().objectName())
        self.removePlot(ID)
        index = self.dataDic["ID"].index(ID)
        groupBox = self.dataDic["GroupBoxes"][index]
        groupBox.deleteLater()
        for key in self.dataDic.keys():
            del self.dataDic[key][index]
        self.dataTable.blockSignals(True)
        self.dataTable.removeRow(index)
        self.scrollWidget.repaint()
        self.dataTable.blockSignals(False)
        self.resizeUIPannel()
        self.updateLegend()

    def onLoadBiolectorPress(self):
        '''
        Opens the chosen biolector file
        '''
        self.dataTable.blockSignals(True)
        filePath, filter = QtGui.QFileDialog.getOpenFileName(self,
                'Open File', '.',filter="*.xlsx")
        if filePath != "":
            self.loadBiolectorData(filePath)
        self.dataTable.blockSignals(False)

    def loadBiolectorData(self,path):
        wb = xlrd.open_workbook(path)
        sheet = wb.sheet_by_index(0)
        nRows = sheet.nrows
        timeRow = nRows
        nCols = sheet.ncols
        times = []
        for row in range(nRows):

            rowData = []
            for col in range(nCols):
                rowData.append(sheet.cell_value(row, col))
            if "Time:" in rowData:
                index = rowData.index("Time:")
                times = np.asarray(rowData)[index+1:]
                times = [float(i) for i in times]
                timeRow = row
            if row > timeRow:
                name = rowData[0] + "_" + rowData[3]
                ODs = np.asarray(rowData)[4:]
                ODs = [float(i) for i in ODs]
                self.dataDic["ID"].append(self.nextID)
                self.nextID += 1
                self.dataDic["FileNames"].append(name)
                self.dataDic["OriginFiles"].append(name)
                self.dataDic["Types"].append("Biolector")
                self.dataDic["Times"].append(times)
                self.dataDic["ODs"].append(ODs)
                self.dataDic["DoublingTimes"].append(-1)
                count = sum([1 for j in range(len(ODs)) if ODs[j]-ODs[0] > 0])
                self.addSlider(name,0,count)
                self.addPlot()
                self.dataDic["CheckBoxes"][-1].setChecked(False)
                self.checkBoxReplot(self.dataDic["ID"][-1])
        self.recolorPlots()

    def getQTableWidgetSize(self,table):
        w = table.verticalHeader().width() + 4  # +4 seems to be needed
        for i in range(table.columnCount()):
            w += table.columnWidth(i)  # seems to include gridline (on my machine)
        h = table.horizontalHeader().height() + 4
        for i in range(table.rowCount()):
            h += table.rowHeight(i)
        return QtCore.QSize(w+ 2.0*self.UILayout.contentsMargins().left() , h)

    def resizeUIPannel(self):
        self.scroll.setMinimumWidth(1.02*self.getQTableWidgetSize(self.dataTable).width())
        self.scrollWidget.setMinimumWidth(self.getQTableWidgetSize(self.dataTable).width())

    def getLogFit(self,ID):
        index = self.dataDic["ID"].index(ID)
        x,y = self.dataDic["LogPlots"][index].getData()
        minValue = self.dataDic["MinSliders"][index].value()
        maxValue = self.dataDic["MaxSliders"][index].value()
        slope, intercept, r_value, p_value, std_err = stats.linregress(x[minValue:maxValue],y[minValue:maxValue])
        xfit = np.linspace(x[minValue],x[maxValue-1],1000)
        yfit = slope*xfit + intercept
        doublingTime = 60.0*np.log(2)/slope
        self.dataDic["DoublingTimes"][index] = doublingTime
        return xfit,yfit, doublingTime

    def recolorPlots(self):
        nColours = 0
        for checkBox in self.dataDic["CheckBoxes"]:
            if checkBox.isChecked():
                nColours += 1
        j =0
        for i in range(len(self.dataDic["FileNames"])):
            if self.dataDic["CheckBoxes"][i].isChecked():
                self.dataDic["LinearPlots"][i].setPen((j,nColours))
                self.dataDic["LogPlots"][i].setPen((j,nColours))
                self.dataDic["LogFitPlots"][i].setPen((j,nColours))
                j +=1

    def updateLegend(self):
        self.logLegend.items = []
        self.linearLegend.items = []

        for i in range(len(self.dataDic["ID"])):
            if self.dataDic["CheckBoxes"][i].isChecked():
                self.linearLegend.addItem(self.dataDic["LinearPlots"][i],self.dataDic["FileNames"][i])
                self.logLegend.addItem(self.dataDic["LogPlots"][i],self.dataDic["DoublingTimes"][i])

    def onOpenPlatePress(self):
        '''
        Opens the chosen biolector file as plate
        '''
        self.dataTable.blockSignals(True)
        filePath, filter = QtGui.QFileDialog.getOpenFileName(self,
                'Open File', '.',filter="*.xlsx")
        if filePath != "":
            self.loadPlateData(filePath)
        self.dataTable.blockSignals(False)

    def loadPlateData(self,path):
        wb = xlrd.open_workbook(path)
        sheet = wb.sheet_by_index(0)
        nRows = sheet.nrows
        timeRow = nRows
        nCols = sheet.ncols
        times = []
        for row in range(nRows):
            rowData = []
            for col in range(nCols):
                rowData.append(sheet.cell_value(row, col))
            if "Time:" in rowData:
                index = rowData.index("Time:")
                times = np.asarray(rowData)[index+1:]
                times = [float(i) for i in times]
                timeRow = row
            if row > timeRow:
                name = rowData[0] + "_" + rowData[3]
                ODs = np.asarray(rowData)[4:]
                ODs = [float(i) for i in ODs]
                self.dataDic["ID"].append(self.nextID)
                self.nextID += 1
                self.dataDic["FileNames"].append(name)
                self.dataDic["OriginFiles"].append(path)
                self.dataDic["Types"].append("Plate")
                self.dataDic["Times"].append(times)
                self.dataDic["ODs"].append(ODs)
                self.dataDic["DoublingTimes"].append(-1)
                count = sum([1 for j in range(len(ODs)) if ODs[j]-ODs[0] > 0])
                self.addSlider(name,0,count)
                self.addPlot()
                self.dataDic["CheckBoxes"][-1].setChecked(False)
                self.dataDic["DeleteButtons"][-1].hide()
                self.checkBoxReplot(self.dataDic["ID"][-1])

        for i in range(len(self.dataDic["ID"])):
            if self.dataDic["Types"][i] == "Plate" and self.dataDic["OriginFiles"][i] == path:
                self.dataDic["GroupBoxes"][i].hide()
                self.dataTable.hide()
        self.createPlateGrid(path)

        self.recolorPlots()

    def createPlateGrid(self,oriFile):
        plateDic = {"Rows":[],"Columns":[],"Channels":[],"IDs":[],"Buttons":[],"Active":[]}

        for i in range(len(self.dataDic["ID"])):
            if self.dataDic["Types"][i] == "Plate" and self.dataDic["OriginFiles"][i] == oriFile:
                name = self.dataDic["FileNames"][i]
                cell, channel = name.split("_")
                row = cell[0]
                column = cell[1:]
                plateDic["Rows"].append(row)
                plateDic["Columns"].append(column)
                plateDic["Channels"].append(channel)
                plateDic["IDs"].append(self.dataDic["ID"][i])
                plateDic["Buttons"].append(0)
                plateDic["Active"].append(False)
        rows = sorted(list(set(plateDic["Rows"])))
        columns = sorted(list(set(plateDic["Columns"])))
        channels = sorted(list(set(plateDic["Channels"])))

        #Add buttons to each plateDic entry and add them to layout
        plateLayout = QtGui.QGridLayout()
        for row in range(len(rows)):
            for column in range(len(columns)):
                for channel in range(len(channels)):
                    if channel == 0:
                        btn = QtGui.QPushButton(rows[row]+columns[column])
                        btn.setCheckable(True)
                        btn.setStyleSheet(
                        "QPushButton {"
                        "background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 rgb(120,120,120), stop: 1 rgb(80,80,80));"
                        "border: 1px solid rgb(20,20,20);"
                        "color: rgb(230,230,230);"
                        "padding: 4px 8px;"
                        "}"
                        "QPushButton:checked{"
                        "background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 rgb(40,150,200), stop: 1 rgb(90,200,255));"
                        "color: rgb(20,20,20);"
                        "}")
                        btn.clicked.connect(partial(self.onPlateButtonPress,plateDic))
                        plateLayout.addWidget(btn,column,row)
                    index = [i for i in range(len(plateDic["IDs"])) if plateDic["Rows"][i] == rows[row] and
                            plateDic["Columns"][i]==columns[column] and plateDic["Channels"][i] == channels[channel]]
                    plateDic["Buttons"][index[0]] = btn

        self.UILayout.insertLayout(5,plateLayout)

        #Add channel selector
        self.channelSelector = QtGui.QComboBox()
        self.channelSelector.addItems(channels)
        self.channelSelector.currentIndexChanged.connect(partial(self.onChannelSelectionChange,plateDic))
        self.UILayout.insertWidget(5,self.channelSelector)

    def onPlateButtonPress(self,plateDic):
        channel = str(self.channelSelector.currentText())
        btn = self.sender()
        index = [i for i in range(len(plateDic["IDs"])) if plateDic["Buttons"][i]==btn and plateDic["Channels"][i]==channel][0]

        ID = plateDic["IDs"][index]
        index = self.dataDic["ID"].index(ID)
        on = self.sender().isChecked()
        if on:
            #Reveal widgets and plot
            self.dataDic["GroupBoxes"][index].show()
            self.dataDic["CheckBoxes"][index].setChecked(True)
            plateDic["Active"][index] = True
            self.checkBoxReplot(ID)
            self.recolorPlots()
        if not on:
            self.dataDic["GroupBoxes"][index].hide()
            self.dataDic["CheckBoxes"][index].setChecked(False)
            plateDic["Active"][index] = False
            self.checkBoxReplot(ID)
            self.recolorPlots()

    def onChannelSelectionChange(self,plateDic):
        channel = str(self.channelSelector.currentText())
        for i in range(len(plateDic["IDs"])):
                plateDic["Buttons"][i].setChecked(False)
        for i in range(len(plateDic["IDs"])):
            if channel == plateDic["Channels"][i] and plateDic["Active"][i]==True:
                plateDic["Buttons"][i].setChecked(True)

#    def splineFit(self,x,y,S=0):
        #T = np.linspace(x[1],x[-2], max(3,S))
        #yPredict = interpolate.splrep(x, y,s=0,t=T)
        #x2 = np.linspace(x[0],x[-1],200)
        #y2 = interpolate.splev(x2,yPredict)
        #return x2,y2

#    def onSmoothSliderChange(self):
        #self.dataTable.blockSignals(True)
        #self.replot()
        #self.dataTable.blockSignals(False)

if __name__ == '__main__':
    from GrowthCurveApp import GrowthCurveApp

    GCA1 = GrowthCurveApp()
    GCA1.run()
    exit()
