# 
# This file is part of the TelemFFB distribution (https://github.com/walmis/TelemFFB).
# Copyright (c) 2023 Valmantas Palikša.
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import json
import logging
import sys
sys.path.insert(0, '') 
import struct
import time
import traceback
from pySerialTransfer import pySerialTransfer as txfer
import serial.tools.list_ports
import configparser
from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from telemManager import TelemManager
      

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

import re
  
import argparse
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QVBoxLayout,QMessageBox, QScrollArea
from PySide6.QtCore import QObject, Signal, Qt, QThread
from PySide6.QtGui import QFont

from time import monotonic
import socket
import threading
import utils

import traceback
import os


config_file = 'config.ini'

serialEnabled = False


def format_dict(data, prefix=""):
    output = ""
    for key, value in data.items():
        if isinstance(value, dict):
            output += format_dict(value, prefix + key + ".")
        else:
            output += prefix + key + " = " + str(value) + "\n"
    return output

	



# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("zTelem")
        self.resize(800, 600)
        layout = QVBoxLayout()
                
        serialLabel = QLabel("Serial Monitor")
        self.serialMonitor = QLabel("Waiting for data...")
        
        
        label = QLabel("DCS Telemetry")
         
        layout.addWidget(label);
        
        self.lbl_telem_data = QLabel("Waiting for data...")
        self.lbl_telem_data.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_telem_data.setWordWrap(True)
        layout.addWidget(self.lbl_telem_data)
        layout.addStretch()
       
        
        
  
        widget = QWidget()
        widget.setLayout(layout)
        
        
        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(widget)
        
        self.setCentralWidget(scrollArea)
        
        
        
    def update_serial(self, serialText : str):
        self.serialMonitor.setText(serialText);

        # Set the central widget of the Window.

    def update_telemetry(self, data : dict):

        items = ""
        for k,v in data.items():
            if k == "MechInfo":
                v = format_dict(v, "MechInfo.")
                items += f"{v}"
            else:
                if type(v) == float:
                    items += f"{k}: {v:.2f}\n"
                else:
                    items += f"{k}: {v}\n"
        # itemsText = ""

        #items_text = "slip:" + str(data.get('slip', 0)) + "\n"
        #items_text += "True Air Speed (knots):" + str(data.get('TAS', 0)) + "\n"
        self.lbl_telem_data.setText(str(data.get('TAS', 0)))
        





# window = MainWindow()
# window.show()    

# manager.telemetryReceived.connect(window.update_telemetry)
    
# #serialManager.serialReceived.connect(window.update_serial);





def getComPorts():
    window.comSelect.clear()
    ports = serial.tools.list_ports.comports()
    com_ports = []
    for port, _, _ in ports:
        com_ports.append(port)
    if com_ports:
        window.comSelect.addItems(com_ports)
        
def load_last_selection():
    config = configparser.ConfigParser()
    config.read(config_file)

    if 'LastSelection' in config:
        last_selection = config['LastSelection'].get('COMPort', '')
        if last_selection:
            index = window.comSelect.findText(last_selection)
            if index != -1:
                window.comSelect.setCurrentIndex(index)
    if 'autoConnect' in config:
        autoConnect = config['autoConnect'].getboolean('autoConnect', False)
        window.autoConnect.setChecked(autoConnect)
                
def save_last_selection():
    config = configparser.ConfigParser()
    config['LastSelection'] = {'COMPort': window.comSelect.currentText()}
    config['autoConnect'] = {'autoConnect': window.autoConnect.isChecked()}

    with open(config_file, 'w') as configfile:
        config.write(configfile)
        
def updateComStatus(status):
    if status == 'connected':
        window.status.setText("Connected")
        window.connectBtn.setEnabled(False)
        window.disconnectBtn.setEnabled(True)
        window.autoConnect.setEnabled(False)
        window.comSelect.setEnabled(False)
    elif status == 'error':
        window.status.setText("Error connecting to port")
        window.connectBtn.setEnabled(True)
        window.disconnectBtn.setEnabled(False)
        window.autoConnect.setEnabled(True)
        window.comSelect.setEnabled(True)
    elif status == 'disconnected':
        window.status.setText("Disconnected")
        window.connectBtn.setEnabled(True)
        window.autoConnect.setEnabled(True)
        window.comSelect.setEnabled(True)
        window.disconnectBtn.setEnabled(False)

def updateTelemetry(data : dict):
    items = ""
    for k,v in data.items():
        if k == "MechInfo":
            v = format_dict(v, "MechInfo.")
            items += f"{v}"
        else:
            if type(v) == float:
                items += f"{k}: {v:.2f}\n"
            else:
                items += f"{k}: {v}\n"
    itemsText = ""

    itemsText = "slip:" + str(data.get('slip', 0)) + "\n"
    itemsText += "Aircraft:" + str(data.get('N', 0)) + "\n"
    itemsText += "True Air Speed (knots):" + str(data.get('TAS', 0)) + "\n"
    window.telemStatus.setText(itemsText)
    

logging.getLogger().handlers[0].setStream(sys.stdout)
logging.info("zTelem Starting")
#serialManager = SerialManager();
#serialManager.start();    

manager = TelemManager()
manager.start()
manager.comConnected.connect(updateComStatus)
manager.telemetryReceived.connect(updateTelemetry)

loader = QUiLoader()
app = QtWidgets.QApplication(sys.argv)
window = loader.load("zTelem.ui", None)

getComPorts()
load_last_selection()
window.comSelect.activated.connect(save_last_selection)
window.autoConnect.clicked.connect(save_last_selection)
window.connectBtn.clicked.connect(lambda: manager.connectCom(window.comSelect.currentText()))
window.disconnectBtn.clicked.connect(lambda: manager.disconnectCom())
window.disconnectBtn.setEnabled(False)
window.refreshComBtn.clicked.connect(getComPorts)



window.setWindowTitle("zTelem")
window.show()

app.exec()

