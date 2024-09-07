import sqlite3
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QGroupBox
from PyQt5.QtCore import Qt
from ui_planeSettings import Ui_planesSettings
from PyQt5.QtWidgets import QCheckBox
from superqt import QLabeledRangeSlider, QLabeledSlider
from ui_addPlaneDialog import Ui_addPlaneDialog

class Plane:
    def __init__(self, sim="DCS", plane="Default", gainXConstant=85, gainYConstant=85, gainConstantEnable=1, gainXMin=10, gainXMax=10, gainYMin=0, gainYMax=255, gainVs=10, gainVne=200, gainEnable=1, gunEnable=1, gunGain=255, AOAEnable=1, AOAGain=255, AOAMin = 8, AOAMax=13, windEnable=1, windMin=5, windMax=180):
        self.sim = str(sim)
        self.plane = str(plane)
        self.gainXConstant = int(gainXConstant)
        self.gainYConstant = int(gainXConstant)
        self.gainConstantEnable = bool(gainConstantEnable)
        self.gainXMin = int(gainXMin)
        self.gainXMax = int(gainXMax)
        self.gainYMin = int(gainYMin)
        self.gainYMax = int(gainYMax)
        self.gainVs = int(gainVs)
        self.gainVne = int(gainVne)
        self.gainEnable = bool(gainEnable)
        self.gunEnable = bool(gunEnable)
        self.gunGain = int(gunGain)
        self.AOAEnable = bool(AOAEnable)
        self.AOAGain = int(AOAGain)
        self.AOAMin = int(AOAMin)
        self.AOAMax = int(AOAMax)
        self.windEnable = bool(windEnable)
        self.windMin = int(windMin)
        self.windMax = int(windMax)
    
    def __str__(self):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        return ", ".join([f"{member}: {getattr(self, member)}" for member in members])
    def __len__(self):
        return len([attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")])
    
            
class DbHandler:
    def __init__(self):
        self.conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.dbVersion = 2
        self.createSchema()
        self.upgradeSchema()

    def getData(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def insertData(self, query):
        self.cursor.execute(query)
        self.conn.commit()
        
    def deleteData(self, query):
        self.cursor.execute(query)
        self.conn.commit()
        
    def insertPlane(self, plane:Plane):
        members = [attr for attr in dir(plane) if not callable(getattr(plane, attr)) and not attr.startswith("__")]
        columns = ", ".join(members)
        values = ", ".join([f":{member}" for member in members])
        self.cursor.execute(f"""INSERT INTO planes ({columns}) 
                            VALUES ({values})""", 
                            {'sim': plane.sim, 'plane': plane.plane, 
                             'gainXConstant': plane.gainXConstant, 'gainYConstant': plane.gainYConstant, 'gainConstantEnable': plane.gainConstantEnable,
                             'gainXMin': plane.gainXMin, 'gainXMax': plane.gainXMax, 
                             'gainYMin': plane.gainYMin, 'gainYMax': plane.gainYMax, 'gainVs': plane.gainVs, 'gainVne': plane.gainVne, 
                             'gainEnable': plane.gainEnable, 'gunEnable': plane.gunEnable, 'gunGain': plane.gunGain, 'AOAEnable': plane.AOAEnable, 
                             'AOAGain': plane.AOAGain, 'AOAMin': plane.AOAMin, 'AOAMax': plane.AOAMax, 'windEnable': plane.windEnable, 
                             'windMin': plane.windMin, 'windMax': plane.windMax})
        self.conn.commit()
        
    def getPlane(self, sim="DCS", plane="Default"):
        self.cursor.execute("SELECT * FROM planes WHERE sim = ? AND plane = ?", (sim, plane))
        row = self.cursor.fetchone()
        if (row):
            plane = Plane()
            for key in row.keys():
                setattr(plane, key, row[key])
            return plane
        else:
            return False
        
    def getPlanes(self, sim="All"):
        sql = "SELECT * FROM planes"
        
        if sim == "DCS":
            sql = "SELECT * FROM planes WHERE sim = 'DCS'"
        elif sim == "IL-2":
            sql = "SELECT * FROM planes WHERE sim = 'IL-2'"
        elif sim == "MSFS":
            sql = "SELECT * FROM planes WHERE sim = 'MSFS'"
        elif sim == "XPlane":
            sql = "SELECT * FROM planes WHERE sim = 'XPlane'"

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        planes = []
        for row in rows:
            plane = Plane()
            for key in row.keys():
                setattr(plane, key, row[key])
            planes.append(plane)
        return planes
    
    def updatePlane(self, plane:Plane):
        print(plane)
        members = [attr for attr in dir(plane) if not callable(getattr(plane, attr)) and not attr.startswith("__")]
        columns = ", ".join([f"{member} = :{member}" for member in members])
        self.cursor.execute(f"""UPDATE planes 
                            SET {columns} 
                            WHERE sim = :sim AND plane = :plane""", 
                            {'sim': plane.sim, 'plane': plane.plane, 
                             'gainXConstant': plane.gainXConstant, 'gainYConstant': plane.gainYConstant, 'gainConstantEnable': plane.gainConstantEnable,
                             'gainXMin': plane.gainXMin, 'gainXMax': plane.gainXMax, 
                             'gainYMin': plane.gainYMin, 'gainYMax': plane.gainYMax, 'gainVs': plane.gainVs, 'gainVne': plane.gainVne, 
                             'gainEnable': plane.gainEnable, 'gunEnable': plane.gunEnable, 'gunGain': plane.gunGain, 'AOAEnable': plane.AOAEnable, 
                             'AOAGain': plane.AOAGain, 'AOAMin': plane.AOAMin, 'AOAMax': plane.AOAMax, 'windEnable': plane.windEnable, 
                             'windMin': plane.windMin, 'windMax': plane.windMax})
        self.conn.commit()

    def __del__(self):
        self.conn.close()
    
    def insertTestData(self):
        for i in range(20):
            plane = Plane()
            plane.plane = f"Plane {i}"
            self.insertPlane(plane)
        
    def createSchema(self):
        currentDbVersion = self.cursor.execute('pragma user_version').fetchone()[0]
        if(currentDbVersion == 0):
            plane = Plane()
            members = [attr for attr in dir(plane) if not callable(getattr(plane, attr)) and not attr.startswith("__")]
            # Get the values of each attribute of plane
            schemaColumns = ""
            for member in members:
                value = getattr(plane, member)
                if type(value).__name__ == "str":
                    schemaColumns += f"{member} TEXT, "
                elif type(value).__name__ == "int":
                    schemaColumns += f"{member} INTEGER, "
        
            self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS planes (
                {schemaColumns}
                PRIMARY KEY (sim, plane), 
                UNIQUE(sim, plane) ON CONFLICT REPLACE
            )''')
            
            self.cursor.execute(f'pragma user_version = {self.dbVersion}')
            
            result = self.cursor.fetchall();   
            if len(result) == 0:
                self.insertPlane(Plane())
            
            self.conn.commit()
        

    def upgradeSchema(self):
        currentDbVersion = self.cursor.execute('pragma user_version').fetchone()[0]

        if currentDbVersion == 1:
            newVersion = 2
            # Check if the gainConstantEnable column does not exist and then add it
            self.cursor.execute("SELECT * FROM pragma_table_info('planes') WHERE name='gainConstantEnable'")
            if not self.cursor.fetchone():
                # Adding the gainConstantEnable column, assuming it's of type INTEGER (use TEXT, REAL, etc., as needed)
                self.cursor.execute('ALTER TABLE planes ADD COLUMN gainConstantEnable INTEGER DEFAULT 0')
                print("Added 'gainConstantEnable' column to 'planes' table.")

            # Update the database version after the upgrade
            self.cursor.execute(f'pragma user_version = {newVersion}')
            self.conn.commit()
            print(f"Database schema upgraded to version {newVersion}.")
    
class AddPlaneDialog(QtWidgets.QDialog, Ui_addPlaneDialog):
    def __init__(self):
        super(AddPlaneDialog, self).__init__()
        self.setupUi(self)
        self.setModal(True)

            
    def show(self, planeName):
        super().show()
        print(planeName)
        if(planeName != "None"):
            self.planeName.setText(planeName)
        
    

class PlaneSettingsManager(QtWidgets.QDialog, Ui_planesSettings):
    def __init__(self, parent):
        self.db = DbHandler()
        super(PlaneSettingsManager, self).__init__()
        self.setupUi(self)
        self.simList.addItems(["DCS"])
        self.simList.setVisible(False)
        self.simList.currentIndexChanged.connect(lambda: self.updatePlanesList(self.simList.currentText()))
        self.exit.clicked.connect(self.close)
        self.planesList.currentIndexChanged.connect(lambda: self.buildPlaneSettingsUi(self.planesList.currentText()))
        self.saveBtn.clicked.connect(self.saveSettings)
        self.setStyleSheet("* {font-size: 7pt;}")
        self.parentWindow = parent
        self.addPlaneDialog = AddPlaneDialog()
        self.addPlane.clicked.connect(lambda: self.addPlaneDialog.show(self.parentWindow.currentPlane.plane))
        self.addPlaneDialog.accepted.connect(lambda: self.addPlaneFromDialog(self.addPlaneDialog.planeName.text()))
        self.removePlane.clicked.connect(self.deleteCurrentPlane)
    
    
    def show(self, sim="All", planeName="Default") -> None:
        super().show()
        self.simList.setCurrentText(sim)
        self.updatePlanesList(sim)
        print(f"Plane:{sim} - {planeName}")
        self.planesList.setCurrentText(f"{sim} - {planeName}")
        
    
    def updatePlanesList(self, sim):
        self.planesList.clear()
        planes = self.db.getPlanes(sim)
        for plane in planes:
            self.planesList.addItem(f"{plane.sim} - {plane.plane}")
    
    def buildPlaneSettingsUi(self, planeText):
        #first, remove all widgets from settings layout
        for i in reversed(range(self.settingsLayout.count())): 
            self.settingsLayout.itemAt(i).widget().setParent(None)
        
        if(planeText == ""):
            return
        sim, plane = planeText.split(" - ", 1)
        
        #To Do: Need to handle All
        if sim == "All":
            sim = "DCS"
        result = self.db.getPlane(sim, plane)

        effectsGroup = QGroupBox()
        effectsGroup.setTitle("Effects")
        self.settingsLayout.addWidget(effectsGroup)

        effectsLayout = QHBoxLayout()
        effectsGroup.setLayout(effectsLayout)

        gainCheckbox = QCheckBox("Dynamic Sensitivity")
        gainCheckbox.setObjectName("gainCheckbox")
        gainCheckbox.setChecked(result.gainEnable)
        effectsLayout.addWidget(gainCheckbox)

        gainConstantCheckbox = QCheckBox("Constant Sensitivity")
        gainConstantCheckbox.setObjectName("gainContantCheckbox")
        gainConstantCheckbox.setChecked(result.gainConstantEnable)
        effectsLayout.addWidget(gainConstantCheckbox)

        if gainCheckbox.isChecked():
            gainConstantCheckbox.setEnabled(False)
        
        AOACheckbox = QCheckBox("AOA Shake")
        AOACheckbox.setObjectName("AOACheckbox")
        AOACheckbox.setChecked(result.AOAEnable)
        effectsLayout.addWidget(AOACheckbox)

        gunShakeCheckbox = QCheckBox("Gun Shake")
        gunShakeCheckbox.setObjectName("gunShakeCheckbox")
        gunShakeCheckbox.setChecked(result.gunEnable)
        effectsLayout.addWidget(gunShakeCheckbox)

        windCheckbox = QCheckBox("Wind Simulator")
        windCheckbox.setObjectName("windCheckbox")
        windCheckbox.setChecked(result.windEnable)
        effectsLayout.addWidget(windCheckbox)
        
        gainXRange = QLabeledRangeSlider(Qt.Orientation.Horizontal)
        gainXRange.setRange(0, 255)
        gainXRange.setValue([result.gainXMin, result.gainXMax])
        gainXRange.setEdgeLabelMode(QLabeledRangeSlider.LabelPosition.NoLabel)
        gainXRange.setObjectName("gainXRange")
        
        gainYRange = QLabeledRangeSlider(Qt.Orientation.Horizontal)
        gainYRange.setObjectName("gainYRange")
        gainYRange.setRange(0, 255)
        gainYRange.setValue([result.gainYMin, result.gainYMax])
        gainYRange.setEdgeLabelMode(QLabeledRangeSlider.LabelPosition.NoLabel)

        
        speedRange = QLabeledRangeSlider(Qt.Orientation.Horizontal)
        speedRange.setObjectName("speedRange")
        speedRange.setRange(0, 600)
        speedRange.setValue([result.gainVs, result.gainVne])
        speedRange.setEdgeLabelMode(QLabeledRangeSlider.LabelPosition.NoLabel)
                
        gainLayout = QVBoxLayout()
        gainXLabel = QLabel("Set Min and Max Sensitivity for X Axis")
        
        gainYLabel = QLabel("Set Min and Max Sensitivity for Y Axis")
        
        gainXVLayout = QVBoxLayout()
        gainXVLayout.addWidget(gainXLabel)
        gainXVLayout.addWidget(gainXRange)
        
        gainYVLayout = QVBoxLayout()
        gainYVLayout.addWidget(gainYLabel)
        gainYVLayout.addWidget(gainYRange)
        
        gainXYHLayout = QHBoxLayout()
        gainXYHLayout.addLayout(gainXVLayout)
        gainXYHLayout.addLayout(gainYVLayout)
        
        gainLayout.addLayout(gainXYHLayout)
        
        speedLabel = QLabel("Set Min and Max Speed when Gain Control is Active")
        gainLayout.addWidget(speedLabel)
        gainLayout.addWidget(speedRange)
        
        gainGroup = QGroupBox()
        gainGroup.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        gainGroup.setTitle("Dynamic Sensitivity Settings")
        gainGroup.setObjectName("gainGroup")
        gainGroup.setLayout(gainLayout)
        self.settingsLayout.addWidget(gainGroup)

        if(result.gainEnable == False):
            gainGroup.setEnabled(False)
        
        gainXConstantLabel = QLabel("Set Constant Sensitivity for X Axis")
        gainXConstantSlider = QLabeledSlider(Qt.Orientation.Horizontal)
        gainXConstantSlider.setObjectName("gainXConstantSlider")
        gainXConstantSlider.setRange(0, 255)
        gainXConstantSlider.setValue(result.gainXConstant)

        gainYConstantLabel = QLabel("Set Constant Sensitivity for Y Axis")
        gainYConstantLabel.setStyleSheet("QLabel {margin: 0}")
        gainYConstantSlider = QLabeledSlider(Qt.Orientation.Horizontal)
        gainYConstantSlider.setObjectName("gainYConstantSlider")
        gainYConstantSlider.setRange(0, 255)
        gainYConstantSlider.setValue(result.gainYConstant)
        
        gainXConstantHLayout = QHBoxLayout()
        gainXConstantHLayout.addWidget(gainXConstantLabel)
        gainXConstantHLayout.addWidget(gainXConstantSlider)
        
        gainYConstantHLayout = QHBoxLayout()
        gainYConstantHLayout.addWidget(gainYConstantLabel)
        gainYConstantHLayout.addWidget(gainYConstantSlider)
        
        gainConstantLayout = QVBoxLayout()
        gainConstantLayout.addLayout(gainXConstantHLayout)
        gainConstantLayout.addLayout(gainYConstantHLayout)
        
        gainConstantGroup = QGroupBox()
        gainConstantGroup.setObjectName("gainConstantGroup")
        gainConstantGroup.setTitle("Constant Sensitivity Settings")
        gainConstantGroup.setLayout(gainConstantLayout)
        self.settingsLayout.addWidget(gainConstantGroup)

        if(result.gainEnable):
            gainConstantGroup.setEnabled(False)    
        
        AOAshakeLayout = QVBoxLayout()
        AOAshakeGroup = QGroupBox()
        AOAshakeGroup.setTitle("AOA Shake Settings")
        AOAshakeGroup.setLayout(AOAshakeLayout)
        self.settingsLayout.addWidget(AOAshakeGroup)    
       
        AOAIntensitiy = QLabeledSlider(Qt.Orientation.Horizontal)
        AOAIntensitiy.setObjectName("AOAIntensitiy")
        AOAIntensitiy.setRange(0, 255)
        AOAIntensitiy.setValue(result.AOAGain)
        AOARange = QLabeledRangeSlider(Qt.Orientation.Horizontal)
        AOARange.setObjectName("AOARange")
        AOARange.setRange(0, 255)
        AOARange.setValue([result.AOAMin, result.AOAMax])
        AOARange.setEdgeLabelMode(QLabeledRangeSlider.LabelPosition.NoLabel)
        
        AOAHLayout = QHBoxLayout()
        AOAHLayout.addWidget(AOAIntensitiy)
        
        AOAHLayout2 = QHBoxLayout()
        AOAHLayout2.addWidget(QLabel("Set Min and Max AOA for Shake"))
        AOAHLayout2.addWidget(AOARange)
        
        AOAVLayout = QVBoxLayout()
        AOAVLayout.addLayout(AOAHLayout)
        AOAVLayout.addLayout(AOAHLayout2)


        gunShakeLayout = QVBoxLayout()
        gunShakeGroup = QGroupBox()
        gunShakeGroup.setTitle("Gun Shake Settings")
        gunShakeGroup.setLayout(gunShakeLayout)
        self.settingsLayout.addWidget(gunShakeGroup)

        gunShakeGain = QLabeledSlider(Qt.Orientation.Horizontal)
        gunShakeGain.setObjectName("gunShakeGain")
        gunShakeGain.setRange(0, 255)
        gunShakeGain.setValue(result.gunGain)
        gunShakeHLayout = QHBoxLayout()
        gunShakeHLayout.addWidget(gunShakeGain)

        AOAshakeLayout.addLayout(AOAVLayout)
        gunShakeLayout.addLayout(gunShakeHLayout)
        
        windLayout = QHBoxLayout()
        windGroup = QGroupBox()
        windGroup.setFixedSize(560,80)
        windGroup.setTitle("Wind Settings")
        windGroup.setLayout(windLayout)

        windRangeSlider = QLabeledRangeSlider(Qt.Orientation.Horizontal)
        windRangeSlider.setObjectName("windRangeSlider")
        windRangeSlider.setRange(0, 600)
        windRangeSlider.setValue([result.windMin, result.windMax])
        windRangeSlider.setEdgeLabelMode(QLabeledRangeSlider.LabelPosition.NoLabel)
        
        windLayout.addWidget(windRangeSlider)
        self.settingsLayout.addWidget(windGroup)

        gainCheckbox.stateChanged.connect(lambda: self.toggleGainSettings(gainCheckbox.isChecked()))
        gainConstantCheckbox.stateChanged.connect(lambda: self.toggleGainConstantSettings(gainConstantCheckbox.isChecked()))
    
    def toggleGainSettings(self, checked):
        self.findChild(QGroupBox, "gainGroup").setEnabled(checked)
        self.findChild(QGroupBox, "gainConstantGroup").setEnabled(not checked)
        self.findChild(QCheckBox, "gainContantCheckbox").setEnabled(not checked)
        #self.toggleGainConstantSettings(not checked)
    
    def toggleGainConstantSettings(self, checked):
        self.findChild(QGroupBox, "gainConstantGroup").setEnabled(checked)
        
    def saveSettings(self):
        plane = Plane()
        plane.sim, plane.plane = self.planesList.currentText().split(" - ", 1)
        plane.gainXConstant = self.findChild(QLabeledSlider, "gainXConstantSlider").value()
        plane.gainYConstant = self.findChild(QLabeledSlider, "gainYConstantSlider").value()
        plane.gainConstantEnable = self.findChild(QCheckBox, "gainContantCheckbox").isChecked()
        plane.gainXMin, plane.gainXMax = self.findChild(QLabeledRangeSlider, "gainXRange").value()
        plane.gainYMin, plane.gainYMax = self.findChild(QLabeledRangeSlider, "gainYRange").value()
        plane.gainVs, plane.gainVne = self.findChild(QLabeledRangeSlider, "speedRange").value()
        plane.gainEnable = self.findChild(QCheckBox, "gainCheckbox").isChecked()
        plane.gunEnable = self.findChild(QCheckBox, "gunShakeCheckbox").isChecked()
        plane.gunGain = self.findChild(QLabeledSlider, "gunShakeGain").value()
        plane.AOAEnable = self.findChild(QCheckBox, "AOACheckbox").isChecked()
        plane.AOAGain = self.findChild(QLabeledSlider, "AOAIntensitiy").value()
        plane.AOAMin, plane.AOAMax = self.findChild(QLabeledRangeSlider, "AOARange").value()
        plane.windEnable = self.findChild(QCheckBox, "windCheckbox").isChecked()
        plane.windMin, plane.windMax = self.findChild(QLabeledRangeSlider, "windRangeSlider").value()
        self.db.updatePlane(plane)
        self.parentWindow.currentPlane = Plane()
        self.parentWindow.currentPlane.plane = "NEEDS UPDATE" #Just a random name so TelemManager willt trigger a plane update to load new settings
    
    def deleteCurrentPlane(self):
        plane = Plane()
        plane.sim, plane.plane = self.planesList.currentText().split(" - ", 1)
        self.db.deleteData(f"DELETE FROM planes WHERE sim = '{plane.sim}' AND plane = '{plane.plane}'")
        self.updatePlanesList(self.simList.currentText())
    
    def addPlaneFromDialog(self, planeName):
        plane = Plane()
        plane.plane = planeName
        self.db.insertPlane(plane)
        self.updatePlanesList(self.simList.currentText())
        self.planesList.setCurrentText(f"DCS - {planeName}")
        self.buildPlaneSettingsUi(self.planesList.currentText())
           
    def deletePlane(self):
        planeName = self.planesList.currentText()
        sim, plane = planeName.split(" - ", 1)
        self.db.deleteData(f"DELETE FROM planes WHERE sim = '{sim}' AND plane = '{plane}'")
        self.updatePlanesList(self.simList.currentText())
        self.buildPlaneSettingsUi(self.planesList.currentText())