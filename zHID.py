
import pywinusb.hid as hid
import threading
from PyQt5.QtCore import QObject, pyqtSignal
class zHID(QObject):
    deviceConnected = pyqtSignal(object)

    def __init__(self, vid = 0x239a, pid=0x0404, dataLength=4) -> None:
        super().__init__()
        self.vid = vid
        self.pid = pid
        self.dataLength = dataLength
        self.device = None
        self.hid_filter = hid.HidDeviceFilter(vendor_id = self.vid, product_id = self.pid)
        
        self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        self.monitor_thread.start()

    def connect(self):
        hid_device = self.hid_filter.get_devices()
        if hid_device:
            self.device = hid_device[0]
            self.device.open()
            print('Device connected')
            self.deviceConnected.emit(True)
        else:
            self.deviceConnected.emit(False)
            return False
    
    def disconnect(self):
        print('Device disconnected')
        self.device.close()
        self.device = None
        self.deviceConnected.emit(False)

    def write(self, data):
        if len(data) != self.dataLength:
            if len(data) < self.dataLength:
                data += [0] * (self.dataLength - len(data))
            else:
                data = data[:self.dataLength]
        if self.device != None:
            self.reports = self.device.find_output_reports() + self.device.find_feature_reports()
            self.reports[0].set_raw_data([0] + data)
            self.reports[0].send()

    def monitor_connection(self):
        while True:
            if self.device and not self.device.is_plugged():
                self.disconnect()
            elif not self.device:
                self.connect()
    
class zWind(zHID):

    def __init__(self, vid = 0x239a, pid=0x0404, dataLength = 64) -> None:
        super().__init__(vid, pid, dataLength)

    def sendTelem(self, speed1, speed2):
        self.write([ord('t'), speed1, speed2])  # Send 3 bytes of data
        
class zFSBPro(zHID):
    def __init__(self, vid = 0x2E8A, pid=0x0402, dataLength = 5) -> None:
        super().__init__(vid, pid, dataLength)

    def sendTelem(self, gainX, gainY, vibration, type):
        self.write([ord('t'), int(gainX), int(gainY), int(vibration), ord(type)])  # Send 4 bytes of data