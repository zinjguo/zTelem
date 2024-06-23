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
import configparser
from PyQt5 import uic
from telemManager import TelemManager
import PyQt5
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QVBoxLayout, QMessageBox, QPushButton, QDialog, \
    QRadioButton, QListView, QScrollArea, QHBoxLayout, QPlainTextEdit, QMenu, QButtonGroup, QFrame, \
    QDialogButtonBox, QSizePolicy, QSpacerItem, QTabWidget, QGroupBox
from PyQt5.QtCore import QSize, QObject, pyqtSignal, Qt, QCoreApplication, QUrl, QRect, QMetaObject, QSize, QByteArray, QTimer, \
    QThread, QMutex, QRegularExpression
from PyQt5.QtGui import QFont, QPixmap, QIcon, QDesktopServices, QPainter, QColor, QKeyEvent, QIntValidator, QCursor, \
    QTextCursor, QRegularExpressionValidator, QKeySequence
from PyQt5.QtWidgets import QGridLayout, QToolButton, QStyle


import argparse
from PyQt5 import QtWidgets

from time import monotonic
import socket
import threading
from utils import *

import traceback


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



config_file = 'config.ini'



def format_dict(data, prefix=""):
    output = ""
    for key, value in data.items():
        if isinstance(value, dict):
            output += format_dict(value, prefix + key + ".")
        else:
            output += prefix + key + " = " + str(value) + "\n"
    return output

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
    window.telemStatus.setText(itemsText)


logging.getLogger().handlers[0].setStream(sys.stdout)
logging.info("zTelem Starting")



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("zTelem.ui", self)
        self.setFixedSize(self.size())
        self.setStatusBar(None)
        
app = QtWidgets.QApplication(sys.argv)
app.setStyle('fusion')
window = MainWindow()


manager = TelemManager()
manager.start()
manager.telemetryReceived.connect(updateTelemetry)


def updateWindStatus(status):
    if status:
        window.windEnableIcon.setPixmap(enable_icon)
    else:
        window.windEnableIcon.setPixmap(disable_icon)
        
def updateFsbStatus(status):
    if status:
        window.fsbEnableIcon.setPixmap(enable_icon)
        window.fsbEnableLabel.setText("zFSB Pro connected")
    else:
        window.fsbEnableIcon.setPixmap(disable_icon)
        window.fsbEnableLabel.setText("zFSB Pro not connected")
        
def toggleWindConnect():
    if manager.windEnabled:
        manager.disconnectWind()
    else:
        manager.connectWind()
        
enable_color = QColor(255, 255, 0)
disable_color = QColor(128, 128, 128)
icon_size = QSize(16, 16)
enable_icon = create_colored_icon(enable_color, icon_size)
disable_icon = create_x_icon(disable_color, icon_size)
window.windEnableIcon.setPixmap(disable_icon)
window.fsbEnableIcon.setPixmap(disable_icon)
manager.windConnected.connect(updateWindStatus)
manager.fsbConnected.connect(updateFsbStatus)


manager.connectWind()
manager.connectFsb()

        
testSend = False
window.currentPlane = "NONE"

def toggleTestSend():
    global testSend
    testSend = not testSend
    
    if testSend == True:
        window.testSend.setText("Stop Test")
        manager.startTestThread()
    else:
        window.testSend.setText("Start Test")
        manager.stopTestThread()

window.testSend.clicked.connect(toggleTestSend)



window.setWindowTitle("zTelem")
window.show()


        
def toggleSimSettings():
    global settingsManager
    if manager.settingsManager.isVisible():
        manager.settingsManager.close()
    else: 
        manager.settingsManager.show("DCS", manager.currentPlane.plane)
        
window.planeSettingsBtn.clicked.connect(toggleSimSettings)


app.exec()

