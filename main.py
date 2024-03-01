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
from PyQt5 import uic
from telemManager import TelemManager
from settingsmanager import *
import xmlutils
import PyQt5
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QVBoxLayout, QMessageBox, QPushButton, QDialog, \
    QRadioButton, QListView, QScrollArea, QHBoxLayout, QPlainTextEdit, QMenu, QButtonGroup, QFrame, \
    QDialogButtonBox, QSizePolicy, QSpacerItem, QTabWidget, QGroupBox
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QCoreApplication, QUrl, QRect, QMetaObject, QSize, QByteArray, QTimer, \
    QThread, QMutex, QRegularExpression
from PyQt5.QtGui import QFont, QPixmap, QIcon, QDesktopServices, QPainter, QColor, QKeyEvent, QIntValidator, QCursor, \
    QTextCursor, QRegularExpressionValidator, QKeySequence
from PyQt5.QtWidgets import QGridLayout, QToolButton, QStyle

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

import re

import argparse
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QVBoxLayout,QMessageBox, QScrollArea
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QFont

#from zTelem_ui import Ui_MainWindow

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









# window = MainWindow()
# window.show()

# manager.telemetryReceived.connect(window.update_telemetry)

# #serialManager.serialReceived.connect(window.update_serial);





def getComPorts():
    window.comSelect.clear()
    window.comSelectWind.clear()
    ports = serial.tools.list_ports.comports()
    com_ports = []
    for port, _, _ in ports:
        com_ports.append(port)
    if com_ports:
        window.comSelect.addItems(com_ports)
        window.comSelectWind.addItems(com_ports)

def load_last_selection():
    config = configparser.ConfigParser()
    config.read(config_file)

    if 'LastSelectionCom' in config:
        last_selection = config['LastSelectionCom'].get('COMPort', '')
        if last_selection:
            index = window.comSelect.findText(last_selection)
            if index != -1:
                window.comSelect.setCurrentIndex(index)
    if 'LastSelectionWind' in config:
        last_selection = config['LastSelectionWind'].get('COMPort', '')
        if last_selection:
            index = window.comSelectWind.findText(last_selection)
            if index != -1:
                window.comSelectWind.setCurrentIndex(index)
                
    if 'autoConnect' in config:
        autoConnect = config['autoConnect'].getboolean('autoConnect', False)
        window.autoConnect.setChecked(autoConnect)

def save_last_selection():
    config = configparser.ConfigParser()
    config['LastSelectionCom'] = {'COMPort': window.comSelect.currentText()}
    config['LastSelectionWind'] = {'COMPort': window.comSelectWind.currentText()}
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
        window.comSelectWind.setEnabled(False)
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
        window.comSelectWind.setEnabled(True)
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

    itemsText = "Wind: " + str(data.get("Wind")) + "\n"
    itemsText += "slip:" + str(data.get('slip', 0)) + "\n"
    itemsText += "Aircraft:" + str(data.get('N', 0)) + "\n"
    itemsText += "True Air Speed (knots):" + str(data.get('TAS', 0)) + "\n"
    itemsText += "Guns:" + str(data.get('Gun', 0)) + "\n"
    itemsText += "AoA:" + str(data.get('AoA', 0)) + "\n"
    itemsText += "altAgl:" + str(data.get('altAgl', 0)) + "\n"
    itemsText += "Serial output: " + str(data.get("serialOutput", 0)) + "\n"
    window.telemStatus.setText(itemsText)


logging.getLogger().handlers[0].setStream(sys.stdout)
logging.info("zTelem Starting")
#serialManager = SerialManager();
#serialManager.start();

manager = TelemManager()
manager.start()
manager.comConnected.connect(updateComStatus)
manager.telemetryReceived.connect(updateTelemetry)


#window = uic.loadUi("zTelem.ui", None)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("zTelem.ui", self)
        self.setFixedSize(450, 320)
        self.setStatusBar(None)
        
app = QtWidgets.QApplication(sys.argv)
app.setStyle('fusion')
window = MainWindow()
        
getComPorts()
load_last_selection()
window.comSelect.activated.connect(save_last_selection)
window.comSelectWind.activated.connect(save_last_selection)
window.autoConnect.clicked.connect(save_last_selection)
window.connectBtn.clicked.connect(lambda: manager.connectCom(window.comSelect.currentText(), window.comSelectWind.currentText()))
window.disconnectBtn.clicked.connect(lambda: manager.disconnectCom())
window.disconnectBtn.setEnabled(False)
window.refreshComBtn.clicked.connect(getComPorts)



window.setWindowTitle("zTelem")
window.show()

defaults_path = utils.get_resource_path('defaults.xml', prefer_root=True)
userconfig_path = 'userconfig.xml'
utils.create_empty_userxml_file(userconfig_path)

# global settings_mgr, telem_manager, config_was_default
xmlutils.update_vars("joystick", userconfig_path, defaults_path)
global settings_mgr
try:
    settings_mgr = SettingsWindow(datasource="Global", device="joystick", userconfig_path=userconfig_path, defaults_path=defaults_path)
except Exception as e:
    logging.error(f"Error Reading user config file..")
    ans = QMessageBox.question(None, "User Config Error", "There was an error reading the userconfig.  The file is likely corrupted.\n\nDo you want to back-up the existing config and create a new default (empty) config?\n\nIf you chose No, TelemFFB will exit.")
    if ans == QMessageBox.Yes:
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')

        # Create the backup file name with the timestamp
        backup_file = os.path.join(('userconfig_' + os.environ['USERNAME'] + "_" + timestamp + '_corrupted.bak'))

        # Copy the file to the backup file
        shutil.copy(userconfig_path, backup_file)

        logging.debug(f"Backup created: {backup_file}")

        os.remove(userconfig_path)
        utils.create_empty_userxml_file(userconfig_path)

        logging.info(f"User config Reset:  Backup file created: {backup_file}")
        settings_mgr = SettingsWindow(datasource="Global", device="joystick", userconfig_path=userconfig_path, defaults_path=defaults_path)
        QMessageBox.information(None, "New Userconfig created", f"A backup has been created: {backup_file}\n")
    else:
        QCoreApplication.instance().quit()
        
        
def toggleSimSettings():
    global settings_mgr
    if settings_mgr.isVisible():
        settings_mgr.hide()
    else: 
        settings_mgr.show()
        
    if settings_mgr.current_aircraft_name != '':
                    settings_mgr.currentmodel_click()
    else:
        settings_mgr.update_table_on_class_change()

    if settings_mgr.current_sim == '' or settings_mgr.current_sim == 'nothing':
        settings_mgr.update_table_on_sim_change()

window.simSettingsBtn.clicked.connect(toggleSimSettings)

app.exec()