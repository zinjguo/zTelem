import serial
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QVBoxLayout,QMessageBox, QScrollArea
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QFont
import threading
import json
import socket
import logging
import utils
import time
import numpy as np
from time import monotonic
from serialHandler import SerialHandler
import math
from typing import List, Dict

# Highpass filter dispenser
HPFs: Dict[str, utils.HighPassFilter] = utils.Dispenser(utils.HighPassFilter)

# Lowpass filter dispenser
LPFs: Dict[str, utils.LowPassFilter] = utils.Dispenser(utils.LowPassFilter)


class TelemManager(QObject, threading.Thread):
    telemetryReceived = pyqtSignal(object)

    comConnected = pyqtSignal(object)

    timedOut : bool = True
    lastFrameTime : int = 0
    numFrames : int = 0

    serialEnabled = False
    windEnabled = False

    lastGun = 0;

    ser = SerialHandler()
    serWind = SerialHandler()


    def __init__(self) -> None:
        QObject.__init__(self)
        threading.Thread.__init__(self)

        self.daemon = True


    def connectCom(self, port, windPort=0):
        self.serialEnabled = self.ser.connect(port)
        
        if windPort != 0:
            self.windEnabled = self.serWind.connect(windPort)
            
            
        if self.serialEnabled or (windPort != 0 and self.windEnabled):
            self.comConnected.emit("connected")
        else:
            self.comConnected.emit("error")
                   
        return self.serialEnabled

    def disconnectCom(self):
        self.ser.disconnect()
        self.serWind.disconnect()
        self.serialEnabled = False
        self.windEnabled = False
        self.comConnected.emit("disconnected")
        return self.serialEnabled

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
            
            curFrameTime = time.monotonic() * 1000
            if (curFrameTime - self.lastFrameTime > 1000/72):
                if (self.windEnabled):
                    if ("TAS" in items):
                        
                        mapped_value = self.map_range(items["TAS"], 50, 180, 10, 256)
                        #print(f"Sending Wind: {mapped_value}")
                        _rec_list = self.serWind.sendTelem([float(mapped_value), float(0), float(0)])
                        if _rec_list:
                            items['windSerialOutput'] = _rec_list


                if (self.serialEnabled) and ("TAS" in items) and ("ACCs" in items) and (items['N'] == "P-51D" or items['N'] == "P-51D-30-NA" or items['N'] == "FW-190D9"):
                    minSpeed = 10
                    maxSpeed = 200

                    gainX = 1
                    gainY = 1

                    #gainX = self.map_range(items['TAS'], minSpeed, maxSpeed, .35, 2.5)
                    gainX = .25
                    gainY = self.map_range(items['TAS'], minSpeed, maxSpeed, .25, 1.75)

                
                    if self.lastGun != items['Gun']:
                        vibration = 5
                        self.lastGun = items['Gun']
                    else :
                        gunFire = False
                        vibration = 0

                    if items['AoA'] > 9 and items['altAgl'] > 10:
                        vibration = self.map_range(items['AoA'], 9, 13, 1, 5)


                    _rec_list = self.ser.sendTelem([float(gainX), float(gainY), float(vibration)])
                    # if _rec_list:

                    #     _rec_list = list(np.around(np.array(_rec_list), 2))
                    #     items['serialOutput'] = _rec_list

                    #print(_rec_list)
                    self.lastFrameTime = curFrameTime


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

    def get_aircraft_config(self, aircraft_name, data_source):
        params = {}
        cls_name = "UNKNOWN"
        input_modeltype = ''
        try:
            if data_source == "MSFS2020":
                send_source = "MSFS"
            else:
                send_source = data_source

            if '.' in send_source:
                input = send_source.split('.')
                sim_temp = input[0]
                the_sim = sim_temp.replace('2020', '')
                input_modeltype = input[1]
            else:
                the_sim = send_source

            cls_name, pattern, result = xmlutils.read_single_model(the_sim, aircraft_name, input_modeltype, args.type)
            settings_mgr.current_pattern = pattern
            if cls_name == '': cls_name = 'Aircraft'
            for setting in result:
                k = setting['name']
                v = setting['value']
                u = setting['unit']
                if u is not None:
                    vu = v + u
                else:
                    vu = v
                if setting['value'] != '-':
                    params[k] = vu
                    logging.debug(f"Got from Settings Manager: {k} : {vu}")
                else:
                    logging.debug(f"Ignoring blank setting from Settings Manager: {k} : {vu}")
                # print(f"SETTING:\n{setting}")
            params = utils.sanitize_dict(params)
            self.settings_manager.update_state_vars(
                current_sim=the_sim,
                current_aircraft_name=aircraft_name,
                current_class=cls_name,
                current_pattern=pattern)

            return params, cls_name

            # logging.info(f"Got settings from settingsmanager:\n{formatted_result}")
        except Exception as e:
            logging.warning(f"Error getting settings from Settings Manager:{e}")