from PyQt5.QtCore import QObject, pyqtSignal
import threading
import json
import socket
import logging
from utils import *
import utils
import time
import numpy as np
from time import monotonic
import math
from typing import List, Dict
from db import Plane, DbHandler, PlaneSettingsManager

from zHID import zWind, zFSBPro

class TestThread(threading.Thread):
    _parent = None
    
    sendCount = 0
    def __init__(self, parent=None):
        super(TestThread, self).__init__()
        self.daemon = True
        self._parent = parent
        self._run = True
        
    def run(self):
        while self._run == True:
            self.sendCount += 1
            #print("current count: ", self.sendCount)
            #self._parent.ser.sendTelem([int(126), int(255), int(255), ord('s')])
            
            #self._parent.serWind.sendTelem([int(100), int(255), int(1)])
            self._parent.wind.sendTelem(125, 125)
            self._parent.fsb.sendTelem(int(126), int(255), int(255), 'r')
            time.sleep(.013888)
            
    def stop(self):
        self._run = False


class TelemManager(QObject, threading.Thread):
    telemetryReceived = pyqtSignal(object)

    comConnected = pyqtSignal(object)
    
    windConnected = pyqtSignal(object)
    
    fsbConnected = pyqtSignal(object)

    timedOut : bool = True
    lastFrameTime : int = 0
    numFrames : int = 0

    windEnabled = False
    fsbEnabled = False

    lastGun = 0

    
    def startTestThread(self):
        self.testThread = TestThread(self)
        self.testThread.start()
    
    def stopTestThread(self):
        self.testThread.stop()
        #self.testThread = None

    def __init__(self) -> None:
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.testThread = TestThread(self)
        self.daemon = True
        self.settingsManager = PlaneSettingsManager(self)
        self.currentPlane = self.settingsManager.db.getPlane("DCS", "Default")

    def connectWind(self):
        self.wind = zWind()
        self.wind.connect()
        if (self.wind.device != None):
            self.windConnected.emit(True)
            self.windEnabled = True
            return True
        else:
            self.windConnected.emit(False)
            self.windEnabled = False
            return False
    
    def disconnectWind(self):
        self.windConnected.emit(False)
        self.windEnabled = False
        
    def connectFsb(self):
        self.fsb = zFSBPro()
        self.fsb.connect()
        if (self.fsb.device != None):
            self.fsbConnected.emit(True)
            self.fsbEnabled = True
            return True
        else:
            self.fsbConnected.emit(False)
            self.fsbEnabled = False
            return False
    
    def disconnectFsb(self):
        self.fsbConnected.emit(False)
        self.fsbEnabled = False

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

                continue



            self.timedOut = False
            # print(data)
            data = data[0].decode("utf-8").split(";")
            items = {}

            if data[0] == "DISCONNECT":
                logging.info("Telemetry disconnected")
                self.currentPlane = Plane()

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
            
            if "N" in items:
                planeName = items["N"]
            else:
                planeName = False

            
            
            if(self.currentPlane.plane != planeName and planeName != False):
            
                
                result = self.settingsManager.db.getPlane("DCS", planeName)
                
                if result != False:
                    self.currentPlane = result
                else:
                    self.currentPlane.plane = self.settingsManager.db.getPlane("DCS", "Default")
                
                
            
            currentMillis = time.monotonic() * 1000;   
            if self.currentPlane and currentMillis - self.lastFrameTime > 1000/90:
                self.lastFrameTime = currentMillis
                
                if self.currentPlane.gainEnable:
                    gainXMin = self.currentPlane.gainXMin
                    gainXMax = self.currentPlane.gainXMax
                    gainYMin = self.currentPlane.gainYMin
                    gainYMax = self.currentPlane.gainYMax
                    gainVs = self.currentPlane.gainVs
                    gainVne = self.currentPlane.gainVne
                
                gainXConstant = self.currentPlane.gainXConstant
                gainYConstant = self.currentPlane.gainYConstant
            
                if self.currentPlane.gunEnable:
                    gunVibration = self.currentPlane.gunGain
                    
                if self.currentPlane.AOAEnable:
                    AOAMin = self.currentPlane.AOAMin
                    AOAMax = self.currentPlane.AOAMax
                
                windEnable = False    
                if self.currentPlane.windEnable:
                    windEnable = self.currentPlane.windEnable
                    windMin = self.currentPlane.windMin
                    windMax = self.currentPlane.windMax
                    
                if (self.fsbEnabled):
                    vibrationType = 't'
                    if self.currentPlane.gainEnable and ("TAS" in items):
                        gainX = self.map_range(items['TAS'], gainVs, gainVne, gainXMin, gainXMax)
                        gainY = self.map_range(items['TAS'], gainVs, gainVne, gainYMin, gainYMax)
                        print(f"GainX: {gainX}, GainY: {gainY}")
                    else:
                        gainX = gainXConstant
                        gainY = gainYConstant
                    
                    if "Gun" in items and self.lastGun != items['Gun'] and self.currentPlane.gunEnable:
                        vibration = 255
                        vibrationType = 'c'
                        self.lastGun = items['Gun']
                    else:
                        gunFire = False
                        vibration = 0
                        
                    if "AoA" in items and self.currentPlane.AOAEnable:
                        if items['AoA'] > AOAMin and items['altAgl'] > 10:
                            vibration = int(self.map_range(items['AoA'], AOAMin, AOAMax, 60, 255))
                            vibrationType='r'
                    
                    print(gainY)
                    self.fsb.sendTelem(int(gainX), int(gainY), int(vibration), vibrationType)

                        
                if (self.windEnabled and windEnable):
                    if ("TAS" in items):
                        leftFanSlipMod = 1;
                        rightFanSlipMod = 1;
                        # if "slip" in items:
                        #     slip = self.map_range(items['slip'], -1, 1, -1, 1)
                            
                        #     if slip < 0:
                        #         leftFanSlipMod = 1 - abs(slip);
                        #     else:
                        #         rightFanSlipMod = 1 - abs(slip);
                                
                        leftFan = int(self.map_range(items["TAS"], windMin, windMax, 10, 255) * leftFanSlipMod) 
                        rightFan = int(self.map_range(items["TAS"], windMin, windMax, 10, 255) * rightFanSlipMod) 
                        #print(f"Fan Speeds: {leftFan}, {rightFan}, slip: {slip}, leftSlip: {leftFanSlipMod}, rightSlip: {rightFanSlipMod}")
                        self.wind.sendTelem(leftFan, rightFan)

            self.telemetryReceived.emit(items)


    def clamp(self, n, min, max):
        if n < min:
            return min
        elif n > max:
            return max
        else:
            return n

    def map_range(self, x, in_min, in_max, out_min, out_max):
        value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        return self.clamp(value, out_min, out_max)
