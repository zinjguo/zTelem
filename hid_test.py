import pywinusb.hid as hid
import time
import threading

class zHID:
    def __init__(self, vid = 0x044F, pid=0x0402) -> None:
        self.vid = vid
        self.pid = pid
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

    def write(self, data):
       if self.device != None:
            self.reports = self.device.find_output_reports() + self.device.find_feature_reports()
            self.reports[0].set_raw_data([0] + data)
            self.reports[0].send()
            print (self.reports)
            #self.device.send_feature_report(data)
       
    def monitor_connection(self):
        while True:
            if self.device and not self.device.is_plugged():
                print('Device disconnected')
                self.device = None
            elif not self.device:
                self.connect()
                
class zWind(zHID):
    def __init__(self, vid = 0x044F, pid=0x0402) -> None:
        super().__init__(vid, pid)

    def write(self, data):
        if len(data) != 5:
            if len(data) < 5:
                data += [0] * (5 - len(data))
            else:
                data = data[:5]
        super().write(data)
        
wind = zWind()
while (True):
    wind.write([ord('t'), 20, 20, 255, ord('t')])
    time.sleep(1)