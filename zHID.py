
import pywinusb.hid as hid
import threading
from PyQt5.QtCore import QObject, pyqtSignal
class zHID(QObject):
    deviceConnected = pyqtSignal(object)

    def __init__(self, vid = 0x239a, pid=0x0404, dataLength=64, string="") -> None:
        super().__init__()
        self.vid = vid
        self.pid = pid
        self.string = string  

        self.dataLength = dataLength
        self.device = None
        self.hid_filter = hid.HidDeviceFilter(vendor_id = self.vid, product_id = self.pid)


        
        self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        self.monitor_thread.start()

    def connect(self):
        hid_devices = self.hid_filter.get_devices()
        if hid_devices:
            if self.string != "":
                for device in hid_devices:
                    try:
                        # Check the product string descriptor.
                        if device.product_name == self.string:
                            self.device = device
                    except Exception as e:
                        print("Error reading device descriptor:", e)
                        print("No matching HID device found with {self.string}!")
            else:
                self.device = hid_devices[0]
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
            if self.string == "":
                sendReport = [0] + data
            else:
                sendReport = [2, 4] + data
            self.reports[0].set_raw_data(sendReport)
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
    def __init__(self, vid = 0x2E8A, pid=0x0402, dataLength = 62, string = "zFSB") -> None:
        super().__init__(vid, pid, dataLength, string)

    def sendTelem(self, gainX, gainY, vibration, type):
        self.write([int(gainX), int(gainY), int(vibration), ord(type)])  # Send 4 bytes of data