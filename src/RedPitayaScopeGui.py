'''    
Created on 16 mar 2014

@author: Filip
'''
import sys
from PyQt4 import QtGui, QtCore
import pyqtgraph as pq
import numpy as np
import threading
import time
import socket
import redpitaya_control as rp

class RedPitayaGui(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English))
        self.layout = QtGui.QVBoxLayout(self)
        self.gridLayout = QtGui.QGridLayout()
        
        self.recordSpinbox = QtGui.QSpinBox()
        self.recordSpinbox.setMaximum(16384)
        self.recordSpinbox.setValue(4000)
        self.recordSpinbox.editingFinished.connect(self.setRecordLength)
        self.decimationSpinbox = QtGui.QSpinBox()
        self.decimationSpinbox.setMaximum(5)
        self.decimationSpinbox.editingFinished.connect(self.setDecimation)
        self.trigLevelSpinbox = QtGui.QDoubleSpinBox()
        self.trigLevelSpinbox.setMaximum(2)
        self.trigLevelSpinbox.setMinimum(-2)
        self.trigLevelSpinbox.setValue(0.2)
        self.trigLevelSpinbox.editingFinished.connect(self.setTrigLevel)
        self.trigDelaySpinbox = QtGui.QSpinBox()
#        self.trigDelaySpinbox.setDecimals(6)
        self.trigDelaySpinbox.setMaximum(2000000)
        self.trigDelaySpinbox.setMinimum(0)
        self.trigDelaySpinbox.setValue(2000)
        self.trigDelaySpinbox.editingFinished.connect(self.setTrigDelay)
        self.trigSourceCombobox = QtGui.QComboBox()
        self.trigSourceCombobox.addItem("Channel1")
        self.trigSourceCombobox.addItem("Channel2")
        self.trigSourceCombobox.addItem("External")
        self.trigSourceCombobox.activated.connect(self.setTrigSource)
        self.trigModeCombobox = QtGui.QComboBox()
        self.trigModeCombobox.addItem("Auto")
        self.trigModeCombobox.addItem("Normal")
        self.trigModeCombobox.addItem("Single")        
        self.trigModeCombobox.activated.connect(self.setTrigMode)
        self.trigEdgeCombobox = QtGui.QComboBox()
        self.trigEdgeCombobox.addItem("Positive")
        self.trigEdgeCombobox.addItem("Negative")
        self.trigEdgeCombobox.activated.connect(self.setTrigEdge)
        self.fpsLabel = QtGui.QLabel()
        
        self.gridLayout.addWidget(QtGui.QLabel("Record length"), 0, 0)
        self.gridLayout.addWidget(self.recordSpinbox, 0, 1)
        self.gridLayout.addWidget(QtGui.QLabel("Decimation factor"), 1, 0)
        self.gridLayout.addWidget(self.decimationSpinbox, 1, 1)
        self.gridLayout.addWidget(QtGui.QLabel("Trigger level"), 2, 0)
        self.gridLayout.addWidget(self.trigLevelSpinbox, 2, 1)
        self.gridLayout.addWidget(QtGui.QLabel("Trigger delay / samples"), 3, 0)
        self.gridLayout.addWidget(self.trigDelaySpinbox, 3, 1)
        self.gridLayout.addWidget(QtGui.QLabel("Trigger source"), 4, 0)
        self.gridLayout.addWidget(self.trigSourceCombobox, 4, 1)
        self.gridLayout.addWidget(QtGui.QLabel("Trigger edge"), 5, 0)
        self.gridLayout.addWidget(self.trigEdgeCombobox, 5, 1)
        self.gridLayout.addWidget(QtGui.QLabel("FPS"), 6, 0)
        self.gridLayout.addWidget(self.fpsLabel, 6, 1)
        
        self.plotWidget = pq.PlotWidget(useOpenGL=True)
        self.plot1 = self.plotWidget.plot()
        self.plot1.setPen((200, 25, 10))
        self.plot2 = self.plotWidget.plot()
        self.plot2.setPen((10, 200, 25))
        self.plot1.antialiasing = True
        self.plotWidget.setAntialiasing(True)

        self.layout.addLayout(self.gridLayout)
        self.layout.addWidget(self.plotWidget)
                
        print 'Connecting...'
        self.rpc = rp.RedPitaya_control('130.235.94.53')
#        self.sock = socket.socket()
#        print 'Socket created'
#        self.sock.connect(('130.235.94.53', 8888))
        print '...connected' 
        
        self.t0 = np.zeros(20)
        for i in range(self.t0.shape[0]):
            self.t0[i] = time.time()
        
        self.lock = threading.Lock()
        
        self.setAll()
        
        self.running = True
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.updateAction)
        self.updateTimer.start(30)
        
    def setAll(self):
        self.setTrigLevel()        
        self.setTrigSource(self.trigSourceCombobox.currentIndex())
        self.setTrigDelay()
        self.setTrigEdge(self.trigEdgeCombobox.currentIndex())
        self.setDecimation()
        self.setRecordLength()
        
    def setRecordLength(self):
        self.lock.acquire()
        self.rpc.setRecordLength(self.recordSpinbox.value())
        self.lock.release()

    def setDecimation(self):
        self.lock.acquire()
        self.rpc.setDecimationFactor(self.decimationSpinbox.value())
        self.lock.release()

    def setTrigLevel(self):
        self.lock.acquire()
        self.rpc.setTriggerLevel(self.trigLevelSpinbox.value())
        self.lock.release()

    def setTrigDelay(self):
        self.lock.acquire()
        self.rpc.setTriggerDelaySamples(self.trigDelaySpinbox.value())
        self.lock.release()
        
    def setTrigSource(self, index):
        sourceList = ['CH1', 'CH2', 'EXT']
        edgeList = ['pe', 'ne']
        self.lock.acquire()
        edgeIndex = self.trigEdgeCombobox.currentIndex()
        self.rpc.setTriggerSourceExplicit(sourceList[index], edgeList[edgeIndex])
        self.lock.release()        

    def setTrigMode(self, index):
        modeList = ['AUTO', 'NORMAL', 'SINGLE']
        self.lock.acquire()
        self.rpc.setTriggerMode(modeList[index])
        self.lock.release()        

    def setTrigEdge(self, index):
        edgeList = ['pe', 'ne']
        sourceList = ['CH1', 'CH2', 'EXT']
        self.lock.acquire()
        sourceIndex = self.trigSourceCombobox.currentIndex()
        self.rpc.setTriggerSourceExplicit(sourceList[sourceIndex], edgeList[index])
        self.lock.release()        
            
    def updateAction(self):
        # Update world here
        self.lock.acquire()
        self.rpc.updateWaveforms()
        data = self.rpc.getWaveform(1)
        self.lock.release()
        self.plot1.setData(y=data)
        t = time.time()
        self.t0 = np.hstack((self.t0[1:], t))
        fps = 1.0 / np.diff(self.t0).mean()
        self.fpsLabel.setText("{:.2f}".format(fps))
            

       
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myapp = RedPitayaGui()
    myapp.show()
    sys.exit(app.exec_())   
