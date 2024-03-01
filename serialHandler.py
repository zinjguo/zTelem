import time
from pySerialTransfer import pySerialTransfer as txfer

class SerialHandler:
    def __init__(self):
        self.link = False
        
    connectCallBack = None

    telemCallBack = None
    
    packet = [
        1.0, # gainX
        1.0, # gainY
        1.0, #vibration
    ]
        
    def connect(self, port):
        try:
            self.link = txfer.SerialTransfer(port)
            if(self.link.open() == False):
                print("Error opening " + port)
                return False
            #self.connectCallBack(True)

        except:
            print ("Error connecting to " + port)
            import traceback
            traceback.print_exc()
            
            try:
                self.link.close()
            except:
                pass
            return False
        
        return True

    def disconnect(self):
        self.link.close()
        #self.connectCallBack(False)
        
    def sendTelem(self, packet):
        if self.link.open() == False:
            return False
        size = self.link.tx_obj("t")
        dataSize = self.link.tx_obj(packet, size) - size 
        self.link.send(size + dataSize)
        
        curMillis = time.monotonic()
        # while not self.link.available():
        #     if ((time.monotonic() - curMillis) > 1):
        #         print("Timeout")
        #         return False
        #     if self.link.status < 0:
        #         if self.link.status == txfer.CRC_ERROR:
        #             print('ERROR: CRC_ERROR')
        #         elif self.link.status == txfer.PAYLOAD_ERROR:
        #             print('ERROR: PAYLOAD_ERROR')
        #         elif self.link.status == txfer.STOP_BYTE_ERROR:
        #             print('ERROR: STOP_BYTE_ERROR')
        #         else:
        #             print('ERROR: {}'.format(self.link.status))
        # rec_values = self.link.rx_obj(obj_type=type(packet), start_pos=0,
        #     obj_byte_size=dataSize,
        #     list_format='f')
        # return(rec_values)