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

com_port = "COM14"
baud_rate = 115200
serialEnabled = False

try:
    ser = txfer.SerialTransfer(com_port)
    ser.open();
    print(f"Serial port {com_port} opened successfully.")
    serialEnabled = True
    
    # Continue with your serial communication code here

except:
    traceback.print_exc()
    
    try:
        link.close()
    except:
        pass
    

import pygame
import pygame._sdl2.audio as sdl2_audio
#pygame.mixer.init()
#print(sdl2_audio.get_audio_device_names(False))
pygame.mixer.init(devicename='Pedal Shakers (USB2.0 Device)')

#pygame.mixer.init(devicename='Headphones (F900S)')

shakeEffect = pygame.mixer.Sound('rumble.wav')

volume = 0
#shakeEffect.set_volume(volume)
channel = pygame.mixer.Channel(1)
channel.set_volume(0)

def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 
        
def map_range(x, in_min, in_max, out_min, out_max):
  value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
  return clamp(value, out_min, out_max) 
  

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

from time import monotonic
import socket
import threading
import utils

import traceback
import os


def format_dict(data, prefix=""):
    output = ""
    for key, value in data.items():
        if isinstance(value, dict):
            output += format_dict(value, prefix + key + ".")
        else:
            output += prefix + key + " = " + str(value) + "\n"
    return output



		
class SerialManager(QObject, threading.Thread):
    serialReceived = pyqtSignal(object)
    
    def __init___(self) -> None:
        QObject.__init__(self)
        threading.Thread.__init__(self, daemon=True)

        self.daemon = True
       
    def run(self):
        MAX_BUFFER_SIZE = 2 * 1024
        buffer = ""
        while True:
            # Read data from the serial port
            
            if serialEnabled:
                data = ser.read(ser.in_waiting or 1).decode("utf-8")

                if data:
                    # Append the received data to the buffer
                    buffer += data
                    
                    # Check if the delimiter "EOL" is present in the buffer
                    if "<EOL>" in buffer:
                        # Extract the text before the delimiter
                        message, buffer = buffer.split("<EOL>", 1)
                        self.serialReceived.emit(message)
                    elif len(buffer) > 2 * 1024:  # If buffer exceeds 2KB without receiving "<EOL>"
                        buffer = ""  # Clear the buffer and restart the loop        
            
        
        


class TelemManager(QObject, threading.Thread):
    telemetryReceived = pyqtSignal(object)

    timedOut : bool = True
    lastFrameTime : float
    numFrames : int = 0
    

    def __init__(self) -> None:
        QObject.__init__(self)
        threading.Thread.__init__(self)

        self.daemon = True

        
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)

        s.settimeout(0.1)
        port = 38681
        s.bind(("", port))
        logging.info(f"Listening on UDP :{port}")
        

        #udp data
        while True:
            try:
                data = s.recvfrom(4096)
                while utils.sock_readable(s):
                    data = s.recvfrom(4096) # get last frame in OS buffer, to minimize latency
                
            except socket.timeout:
                self.timedOut = True
                channel.set_volume(0)
                channel.stop();
                
                continue
                
            #print(ser.in_waiting);

            if not channel.get_busy():
                channel.play(shakeEffect, loops=-1)

            
            self.timedOut = False
            # print(data)
            self.lastFrameTime = monotonic()
            data = data[0].decode("utf-8").split(";")
            items = {}

            if data[0] == "DISCONNECT":
                logging.info("Telemetry disconnected")
                channel.set_volume(0)
                channel.stop();

            for i in data:
                try:
                    k,v = i.split("=")
                    values = v.split("~")
                    items[k] = [utils.to_number(v) for v in values] if len(values)>1 else utils.to_number(v)
                except:
                    pass
            try:
                items["MechInfo"] = json.loads(items["MechInfo"])
            except: pass


            self.telemetryReceived.emit(items)
           

            if ("slip" in items) and ("altAgl" in items) and (items["altAgl"] > 10):
                v = items["slip"]
                if v > 0 :
                    slip_mapped = map_range(abs(v), 0, 10, 0, .8)
                    channel.set_volume(0, slip_mapped)
                if v < 0 :
                    slip_mapped = map_range(abs(v), 0, 10, 0, .8)
   
                    channel.set_volume(slip_mapped, 0)
            else:
                channel.set_volume(0)
                channel.stop()
                
            
            if (serialEnabled) and ("TAS" in items) and ("ACCs" in items) and (items['N'] == "P-51D" or items['N'] == "P-51D-30-NA" or items['N'] == "FW-190D9"):
                minSpeed = 50;
                maxSpeed = 200;
                
                gainX = 1;
                gaintY = 1;
                
                gainY = map_range(items['TAS'], minSpeed, maxSpeed, .35, 2.5)
                
                #data = struct.pack("fff", gainX, gainY, items['TAS'])

                #Send the serialized data
                #logging.info("Sending")
                #ser.write(data)
                curFrameTime = time.monotonic();
                if (curFrameTime - self.lastFrameTime > 1000/80):
                    _list = [gainX, gainY, items['TAS']]
                    sendSize = 0
                    sendSize = ser.tx_obj(_list)
                    ser.send(sendSize)
                    self.lastFrameTime = curFrameTime
                
                # while not ser.available():
                    # if ser.status < 0:
                        # if ser.status == txfer.CRC_ERROR:
                            # print('ERROR: CRC_ERROR')
                        # elif ser.status == txfer.PAYLOAD_ERROR:
                            # print('ERROR: PAYLOAD_ERROR')
                        # elif ser.status == txfer.STOP_BYTE_ERROR:
                            # print('ERROR: STOP_BYTE_ERROR')
                        # else:
                            # print('ERROR: {}'.format(ser.status))
            


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("zTelem")
        self.resize(800, 600)
        layout = QVBoxLayout()
                
        serialLabel = QLabel("Serial Monitor")
        self.serialMonitor = QLabel("Waiting for data...")
        
        
        layout.addWidget(serialLabel)
        layout.addWidget(self.serialMonitor)
        self.serialMonitor.setFixedHeight(200)
        self.serialMonitor.setAlignment(Qt.AlignTop)
        
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
        



def main():
    app = QApplication(sys.argv)
    

    logging.getLogger().handlers[0].setStream(sys.stdout)
    logging.info("zTelem Starting")
    
	

    #serialManager = SerialManager();
    #serialManager.start();    
    
    manager = TelemManager()
    manager.start()
    
    
    window = MainWindow()
    window.show()    

    manager.telemetryReceived.connect(window.update_telemetry)
       
    #serialManager.serialReceived.connect(window.update_serial);
    


    app.exec_()

if __name__ == "__main__":
    main()
