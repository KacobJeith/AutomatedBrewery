from PyQt5 import QtCore, QtGui, QtWidgets, uic
import pyqtgraph
import time
import threading
from multiprocessing import Pipe
import sys

#imports sensor modules
from FlowSensor import flowSensors
from MainSwitchSensor import mainSwitchSensors
from pHandDOSensor import pHandDOSensors
from RTDSensor import tempSensors
from ValveSwitchSensor import valveSwitchSensors
from VolumeSensor import volumeSensors

#imports control modules
from AlarmControl import AlarmController
from HeatControl import HeatController
from PumpAerationValveControl import PumpAerationValveController
from PID import PID

#Loads the qtCreator file
qtCreatorFile = "../UI/AutomatedBreweryUI/DashboardLarge.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class dashboard(QtWidgets.QMainWindow, Ui_MainWindow):
    #Creates the signals used to pull data from sensors and controllers
    flowSignal = QtCore.pyqtSignal(list,list)
    volumeSignal = QtCore.pyqtSignal(list)
    tempSignal = QtCore.pyqtSignal(list)
    pHandDOSignal = QtCore.pyqtSignal(float,float)
    mainSwitchSignal = QtCore.pyqtSignal(list)
    valveSwitchSignal = QtCore.pyqtSignal(list)

    alarmControlSignal = QtCore.pyqtSignal(list)
    heatControlSignal = QtCore.pyqtSignal(list)
    PAVControlSignal = QtCore.pyqtSignal(list)
    HLTPIDSignal = QtCore.pyqtSignal(list)
    BLKPIDSignal = QtCore.pyqtSignal(list)

    redSwitchStyle = '''
    QPushButton {
        border-radius: 0px;
        background-color: rgb(203,34,91);
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    greenSwitchStyle = '''
    QPushButton {
        border-radius: 0px;
        background-color: rgb(7,155,132);
    }

    QPushButton:pressed {
        background-color: grey;
    }'''
    
    autoGreenSwitchStyle = '''
    QPushButton {
        border: 4px solid rgb(0,138,205);
        border-radius: 0px;
        background-color: rgb(7,155,132);
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    autoRedSwitchStyle = '''
    QPushButton {
        border: 4px solid rgb(0,138,205);
        border-radius: 0px;
        background-color: rgb(203,34,91);
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    pumpAerationOnStyle = '''
    QPushButton {
        border-radius: 20px;
        background-color: rgb(7,155,132);
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    pumpAerationOffStyle = '''
    QPushButton {
        border-radius: 20px;
        background-color: rgb(203,34,91);
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    heatOffStyle = '''
    QPushButton {
        border-radius: 0px;
        background-color: white;
        font: 12pt "Arial";
        border: 2px solid black;
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    heatOnStyle = '''
    QPushButton {
        border-radius: 0px;
        background-color: rgb(226,152,21);
        font: 12pt "Arial";
        color:white;
        border: 2px solid black;
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    heatAutoOnStyle = '''
    QPushButton {
        border: 4px solid rgb(0,138,205);
        border-radius: 0px;
        background-color: rgb(226,152,21);
        font: 12pt "Arial";
        color:white;
        border: 2px solid black;
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    heatAutoOffStyle = '''
    QPushButton {
        border: 4px solid rgb(0,138,205);
        border-radius: 0px;
        background-color: white;
        font: 12pt "Arial";
        border: 2px solid black;
    }

    QPushButton:pressed {
        background-color: grey;
    }'''

    alarmSwitchOffStyle = "color:rgb(203,34,91)"

    alarmSwitchOnStyle = "color:rgb(7,155,132)"

    #Creates the pipes used to talk to the control modules
    heatToHLTPIDPipe, HLTPIDToHeatPipe = Pipe()
    UIToHLTPIDPipe, HLTPIDToUIPipe = Pipe()
    heatToBLKPIDPipe, BLKPIDToHeatPipe = Pipe()
    UIToBLKPIDPipe, BLKPIDToUIPipe = Pipe()
    UIToAlarmPipe, AlarmToUIPipe = Pipe()
    UIToPAVPipe, PAVToUIPipe = Pipe()

    def __init__(self):
        super(dashboard, self).__init__()
        
        #Sets global pyqtgraph settings
        pyqtgraph.setConfigOption('background', 'w')
        pyqtgraph.setConfigOption('foreground', 'k')

        #connects the signals to their respective functions
        self.flowSignal.connect(self.flowUpdate)
        self.volumeSignal.connect(self.volumeUpdate)
        self.tempSignal.connect(self.tempUpdate)
        self.pHandDOSignal.connect(self.pHandDOUpdate)
        self.mainSwitchSignal.connect(self.mainSwitchUpdate)
        self.valveSwitchSignal.connect(self.valveSwitchUpdate)

        #Starts up the UI
        self.setupUi(self)
        self.show()

        #Creates threads for each of the sensors and controllers
        HLTPIDThread = threading.Thread(target = self.startHLTPID)
        BLKPIDThread = threading.Thread(target = self.startBLKPID)
        
        flowThread = threading.Thread(target = self.startFlowSensing)
        volumeThread  = threading.Thread(target = self.startVolumeSensing)
        tempThread = threading.Thread(target = self.startTempSensing)
        pHandDOThread = threading.Thread(target = self.startpHandDOSensing)
        mainSwitchThread = threading.Thread(target = self.startMainSwitchSensing)
        valveSwitchThread = threading.Thread(target = self.startValveSwitchSensing)

        #Connects the valve buttons to the valve control
        self.valve1.clicked.connect(lambda: self.changeValve(1))
        self.valve2.clicked.connect(lambda: self.changeValve(2))
        self.valve4.clicked.connect(lambda: self.changeValve(4))
        self.valve5.clicked.connect(lambda: self.changeValve(5))
        self.valve6.clicked.connect(lambda: self.changeValve(6))
        self.valve9.clicked.connect(lambda: self.changeValve(9))
        self.valve10.clicked.connect(lambda: self.changeValve(10))

        self.valve3u.clicked.connect(lambda: self.changeValve(3))
        self.valve3d.clicked.connect(lambda: self.changeValve(3))
        self.valve7u.clicked.connect(lambda: self.changeValve(7))
        self.valve7d.clicked.connect(lambda: self.changeValve(7))
        self.valve8u.clicked.connect(lambda: self.changeValve(8))
        self.valve8d.clicked.connect(lambda: self.changeValve(8))
        

        #Starts the above threads
        HLTPIDThread.start()
        BLKPIDThread.start()

        flowThread.start()
        volumeThread.start()
        tempThread.start()
        pHandDOThread.start()
        mainSwitchThread.start()
        valveSwitchThread.start()

        self.startHeatControl()
        self.startAlarmControl()
        self.startPAVControl()

    def startHLTPID(self):
        TEMP=1

    def startBLKPID(self):
        TEMP=1

    def startHeatControl(self):
        TEMP=1

    def startAlarmControl(self):
        TEMP=1

    def startPAVControl(self):
        self.PAVControl = PumpAerationValveController()

    def startFlowSensing(self):
        flowSensor = flowSensors(self.flowSignal)

    def startVolumeSensing(self):
        volumeSensor = volumeSensors()
        while True:
            volumes = [volumeSensor.HLTVolume(),volumeSensor.MLTVolume(),volumeSensor.BLKVolume()]
            self.volumeSignal.emit(volumes)
            time.sleep(2)

    def startTempSensing(self):
        tempSensor = tempSensors()
        while True:
            temps = [tempSensor.HLTTemp(),tempSensor.MLTTemp(),tempSensor.BLKTemp()]
            self.tempSignal.emit(temps)
            time.sleep(2)

    def startpHandDOSensing(self):
        pHandDOSensor = pHandDOSensors()
        while True:
            pH = pHandDOSensor.pH()
            DO = pHandDOSensor.DO()
            self.pHandDOSignal.emit(pH,DO)
            time.sleep(2)

    def startMainSwitchSensing(self):
        self.mainSwitchSensor = mainSwitchSensors()
        self.mainSwitchSensor.interruptSetUp(self.interruptedMainSwitch)
        while True:
            mainSwitchStates = self.mainSwitchSensor.allMainSwitchStates()
            self.mainSwitchSignal.emit(mainSwitchStates)
            time.sleep(10)

    def startValveSwitchSensing(self):
        self.valveSwitchSensor = valveSwitchSensors()
        self.valveSwitchSensor.interruptSetUp(self.interruptedValveSwitch)
        while True:
            valveSwitchStates = self.valveSwitchSensor.allValveSwitchStates()
            self.valveSwitchSignal.emit(valveSwitchStates)
            time.sleep(10)

    def flowUpdate(self, flowRateValues, flowTotalValues):
        self.HLT_In.setText("{:.2f} g/m".format(flowRateValues[0][1][-1]))
        self.HLT_Out.setText("{:.2f} g/m".format(flowRateValues[1][1][-1]))
        self.MLT_In.setText("{:.2f} g/m".format(flowRateValues[2][1][-1]))
        self.MLT_Out.setText("{:.2f} g/m".format(flowRateValues[3][1][-1]))
        self.BLK_In.setText("{:.2f} g/m".format(flowRateValues[4][1][-1]))
        self.BLK_Out.setText("{:.2f} g/m".format(flowRateValues[5][1][-1]))

    def volumeUpdate(self, volumeValues):
        self.HLT_Vol.setText("{:.2f} gal".format(volumeValues[0]))
        self.MLT_Vol.setText("{:.2f} gal".format(volumeValues[1]))
        self.BLK_Vol.setText("{:.2f} gal".format(volumeValues[2]))

        #Floors the volume to 10 for the display of how full the kettle is
        if volumeValues[0]>10:volumeValues[0]=10
        if volumeValues[1]>10:volumeValues[1]=10
        if volumeValues[2]>10:volumeValues[2]=10

        #Multiplies the value by 100, since the kettle is up to 10 gallons, but
        #the object bar requires integer values, so it goes up to 1000
        self.HLT.setValue(int(round(volumeValues[0]*100)))
        self.MLT.setValue(int(round(volumeValues[1]*100)))
        self.BLK.setValue(int(round(volumeValues[2]*100)))
        
    def tempUpdate(self, tempValues):
        OldHLTText = self.HLT_Heat.text()
        OldMLTText = self.MLT_Heat.text()
        OldBLKText = self.BLK_Heat.text()

        if tempValues[0]>999:tempValues[0]=999
        if tempValues[1]>999:tempValues[1]=999
        if tempValues[2]>999:tempValues[2]=999

        NewHLTText=OldHLTText[:14]+"{: >3d}".format(int(round(tempValues[0])))+OldHLTText[17:]
        NewMLTText=OldMLTText[:14]+"{: >3d}".format(int(round(tempValues[1])))+OldMLTText[17:]
        NewBLKText=OldBLKText[:14]+"{: >3d}".format(int(round(tempValues[2])))+OldBLKText[17:]

        self.HLT_Heat.setText(NewHLTText)
        self.MLT_Heat.setText(NewMLTText)
        self.BLK_Heat.setText(NewBLKText)   

    def pHandDOUpdate(self, pH, DO):
        self.pH.setText("{:.2f}".format(pH))
        self.DO.setText("{:.2f}".format(DO))

    def mainSwitchUpdate(self, mainSwitchValues):
        #Updates the heat select
        if mainSwitchValues[0]=="Auto": TEMP=1
        if mainSwitchValues[0]=="BLK":
            self.BLK_Heat.setStyleSheet(self.heatOnStyle)
            self.HLT_Heat.setStyleSheet(self.heatOffStyle)
        if mainSwitchValues[0]=="HLT":
            self.BLK_Heat.setStyleSheet(self.heatOffStyle)
            self.HLT_Heat.setStyleSheet(self.heatOnStyle)

        #Updates the pumps and aeration
        if mainSwitchValues[1]=="Off":self.waterPump.setStyleSheet(self.pumpAerationOffStyle)
        if mainSwitchValues[1]=="On":self.waterPump.setStyleSheet(self.pumpAerationOnStyle)
        if mainSwitchValues[1]=="Auto":TEMP = 1

        if mainSwitchValues[2]=="Off":self.wortPump.setStyleSheet(self.pumpAerationOffStyle)
        if mainSwitchValues[2]=="On":self.wortPump.setStyleSheet(self.pumpAerationOnStyle)
        if mainSwitchValues[2]=="Auto":TEMP = 1

        if mainSwitchValues[3]=="Off":self.aeration.setStyleSheet(self.redSwitchStyle)
        if mainSwitchValues[3]=="On":self.aeration.setStyleSheet(self.greenSwitchStyle)
        if mainSwitchValues[3]=="Auto":TEMP = 1

        #Updates the master heat switch
        if mainSwitchValues[4] == "Off":self.master_Heat.setStyleSheet(self.heatOffStyle)
        if mainSwitchValues[4] == "On":self.master_Heat.setStyleSheet(self.heatOnStyle)

        #Updates the alarm switch
        if mainSwitchValues[5] == "Off":
            self.alarm_Text.setStyleSheet(self.alarmSwitchOffStyle)
            self.alarm_Text.setText("Off")
        if mainSwitchValues[5] == "On":
            self.alarm_Text.setStyleSheet(self.alarmSwitchOnStyle)
            self.alarm_Text.setText("On")

    def valveSwitchUpdate(self, valveSwitchStates):
        autoValveStates = self.PAVControl.valveStates
        for i in range(1,11):
            if i in [1,2,4,5,6,9,10]:
                if valveSwitchStates[i-1]=="On": getattr(self,"valve"+str(i)).setStyleSheet(self.greenSwitchStyle)
                if valveSwitchStates[i-1]=="Off": getattr(self,"valve"+str(i)).setStyleSheet(self.redSwitchStyle)
                if valveSwitchStates[i-1]=="Auto":
                    if autoValveStates[i-1] == 0: getattr(self,"valve"+str(i)).setStyleSheet(self.autoRedSwitchStyle)
                    if autoValveStates[i-1] == 1: getattr(self,"valve"+str(i)).setStyleSheet(self.autoGreenSwitchStyle)
            else:
                if valveSwitchStates[i-1]=="On":                
                    getattr(self,"valve"+str(i)+"u").setStyleSheet(self.greenSwitchStyle)
                    getattr(self,"valve"+str(i)+"d").setStyleSheet(self.redSwitchStyle)
                if valveSwitchStates[i-1]=="Off":
                    getattr(self,"valve"+str(i)+"u").setStyleSheet(self.redSwitchStyle)
                    getattr(self,"valve"+str(i)+"d").setStyleSheet(self.greenSwitchStyle)
                if valveSwitchStates[i-1]=="Auto":
                    if autoValveStates[i-1] == 0:
                        getattr(self,"valve"+str(i)+"u").setStyleSheet(self.autoRedSwitchStyle)
                        getattr(self,"valve"+str(i)+"d").setStyleSheet(self.autoGreenSwitchStyle)
                    if autoValveStates[i-1] == 1:
                        getattr(self,"valve"+str(i)+"u").setStyleSheet(self.autoGreenSwitchStyle)
                        getattr(self,"valve"+str(i)+"d").setStyleSheet(self.autoRedSwitchStyle)

    def interruptedMainSwitch(self,pin):
        mainSwitchStates = self.mainSwitchSensor.allMainSwitchStates()
        self.mainSwitchSignal.emit(mainSwitchStates)

    def interruptedValveSwitch(self,pin):
        valveSwitchStates = self.valveSwitchSensor.allValveSwitchStates()
        self.valveSwitchSignal.emit(valveSwitchStates)

    def changeValve(self,valve):
        #Pulls the current state of the valve
        currentState = self.PAVControl.valveStates[valve-1]
        if currentState == 0: newState = 1
        if currentState == 1: newState = 0

        #Sets the valve to the new state
        setattr(self.PAVControl,"valve"+str(valve),newState)

        #Updates the dashboard
        self.valveSwitchUpdate(self.valveSwitchSensor.allValveSwitchStates())
        
    
if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	window = dashboard()
	sys.exit(app.exec_())	
	
	
