from simconnect import *
from ctypes import byref, cast, sizeof
import time
import threading
import logging

REQ_ID = 0xfeed

surface_types = {
    0: "Concrete",
    1: "Grass",
    2: "Water",
    3: "Grass_bumpy",
    4: "Asphalt",
    5: "Short_grass",
    6: "Long_grass",
    7: "Hard_turf",
    8: "Snow",
    9: "Ice",
    10: "Urban",
    11: "Forest",
    12: "Dirt",
    13: "Coral",
    14: "Gravel",
    15: "Oil_treated",
    16: "Steel_mats",
    17: "Bituminus",
    18: "Brick",
    19: "Macadam",
    20: "Planks",
    21: "Sand",
    22: "Shale",
    23: "Tarmac",
    24: "Wright flyer track",
}

class SimVar:
    def __init__(self, name, var, sc_unit, unit=None, type=DATATYPE_FLOAT64, scale=None, mutator=None):
        self.name = name
        self.var = var
        self.scale = scale
        self.mutator = mutator
        self.sc_unit = sc_unit
        self.unit = unit
        self.datatype = type
        self.parent = None
        self.index = None # index for multivariable simvars
        if self.sc_unit.lower() in ["bool", "enum"]:
            self.datatype = DATATYPE_INT32

    def _calculate(self, input):
        if self.mutator:
            input = self.mutator(input)
        if self.scale:
            input = input*self.scale
        return input

    def __repr__(self) -> str:
        return f"SimVar({self.name} '{self.var}')"

    @property
    def c_type(self):
        types = {
            DATATYPE_FLOAT64: c_double,
            DATATYPE_FLOAT32: c_float,
            DATATYPE_INT32: c_long,
            DATATYPE_STRING32: c_char*32,
            DATATYPE_STRING128: c_char*128
        }
        return types[self.datatype]

class SimVarArray:
    def __init__(self, name, var, unit, type=DATATYPE_FLOAT64, scale=None, min=0, max=1, keywords=None):
        self.name = name
        self.unit = unit
        self.type = type
        self.scale = scale
        self.vars = []
        self.values = []
        self.min = min
        if keywords is not None:
            for key in keywords:
                index = keywords.index(key)
                simvar = var.replace("<>", key)
                v = SimVar(name, simvar, unit, None, type, scale)
                v.index = index
                v.parent = self
                self.vars.append(v)
                self.values.append(0)
        else:
            for index in range(min, max+1):
                if index < min:
                    self.values.append(0)
                else:
                    v = SimVar(name, f"{var}:{index}", unit, None, type, scale)
                    v.index = index
                    v.parent = self
                    self.vars.append(v)
                    self.values.append(0)

EV_PAUSED = 65499 # id for paused event
EV_STARTED = 65498 # id for started event
EV_STOPPED = 65497  # id for stopped event
EV_SIMSTATE = 65496
class SimConnectManager(threading.Thread):
    sim_vars = [
        SimVar("T", "ABSOLUTE TIME","Seconds" ),
        SimVar("N", "TITLE", "", type=DATATYPE_STRING128),
        SimVar("G", "G FORCE", "Number"),
        SimVarArray("AccBody", "ACCELERATION BODY <>", "feet per second squared", scale=0.031081, keywords=("X", "Y", "Z")), #scale fps/s to g
        SimVar("Gdot", "SEMIBODY LOADFACTOR YDOT", "Number"),
        SimVar("TAS", "AIRSPEED TRUE", "meter/second"),
        SimVar("AirDensity", "AMBIENT DENSITY", "kilograms per cubic meter"),
        SimVar("AoA", "INCIDENCE ALPHA", "degrees"),
        SimVar("StallAoA", "STALL ALPHA", "degrees"),
        #SimVar("ZeroLiftAoA", "ZERO LIFT ALPHA", "degrees"),
        SimVar("SideSlip", "INCIDENCE BETA", "degrees"),
        SimVar("ElevDefl", "ELEVATOR DEFLECTION", "degrees"),
        SimVar("ElevDeflPct", "ELEVATOR DEFLECTION PCT", "Percent Over 100"),
        SimVar("ElevTrim", "ELEVATOR TRIM POSITION", "degrees"),
        SimVar("ElevTrimPct", "ELEVATOR TRIM PCT", "Percent Over 100"),
        SimVar("AileronDefl", "AILERON AVERAGE DEFLECTION", "degrees"),
        SimVarArray("AileronDeflPctLR", "AILERON <> DEFLECTION PCT", keywords=("LEFT", "RIGHT"), unit="Percent Over 100"),
        SimVar("AileronTrim", "AILERON TRIM", "degrees"),
        SimVar("AileronTrimPct", "AILERON TRIM PCT", "Percent Over 100"),
        SimVar("PropThrust1", "PROP THRUST:1", "kilograms", scale=10), #scaled to newtons
        SimVarArray("PropThrust", "PROP THRUST", "kilograms", min=1, max=4, scale=10),#scaled to newtons
        SimVarArray("PropRPM", "PROP RPM", "RPM", min=1, max=4),
        SimVar("RotorRPM", "ROTOR RPM:1", "RPM"),
        SimVar("DynPressure", "DYNAMIC PRESSURE", "pascal"),
        SimVar("APMaster", "AUTOPILOT MASTER", "Bool"),
        SimVar("RudderDefl", "RUDDER DEFLECTION", "degrees"),
        SimVar("RudderDeflPct", "RUDDER DEFLECTION PCT", "Percent Over 100"),
        SimVar("RudderTrimPct", "RUDDER TRIM PCT", "Percent Over 100"),
        SimVar("Pitch", "PLANE PITCH DEGREES", "degrees"),
        SimVar("Roll", "PLANE BANK DEGREES", "degrees"),
        SimVar("CyclicTrimX", "ROTOR LATERAL TRIM PCT", "Percent Over 100"),
        SimVar("CyclicTrimY", "ROTOR LONGITUDINAL TRIM PCT", "Percent Over 100"),
        SimVar("Heading", "PLANE HEADING DEGREES TRUE", "degrees"),
        SimVar("PitchRate", "ROTATION VELOCITY BODY X", "degrees per second"), # todo replace usage with VelRotBody array
        SimVar("RollRate", "ROTATION VELOCITY BODY Z", "degrees per second"), # todo replace usage with VelRotBody array
        SimVarArray("VelRotBody", "ROTATION VELOCITY BODY <>", "degrees per second", keywords=("X", "Y", "Z")),
        SimVar("PitchAccel", "ROTATION ACCELERATION BODY X", "degrees per second squared"), # todo replace usage with AccRotBody array
        SimVar("RollAccel", "ROTATION ACCELERATION BODY Z", "degrees per second squared"), # todo replace usage with AccRotBody array
        SimVarArray("AccRotBody", "ROTATION ACCELERATION BODY <>", "degrees per second squared", keywords=("X", "Y", "Z")),
        SimVarArray("DesignSpeed", "DESIGN SPEED <>", "meter/second", keywords=("VC", "VS0", "VS1")),
        SimVarArray("Brakes", "BRAKE <> POSITION", "Position", keywords=("LEFT", "RIGHT")),
        #SimVar("LinearCLAlpha", "LINEAR CL ALPHA", "Per Radian"),
        #SimVar("SigmaSqrt", "SIGMA SQRT", "Per Radian"),
        SimVar("SimDisabled", "SIM DISABLED", "Bool"),
        SimVar("SimOnGround", "SIM ON GROUND", "Bool"),
        SimVar("Parked", "PLANE IN PARKING STATE", "Bool"),
        SimVar("Slew", "IS SLEW ACTIVE", "Bool"),
        SimVar("SurfaceType", "SURFACE TYPE", "Enum", mutator=lambda x: surface_types.get(x, "unknown")),
        SimVar("SimconnectCategory", "CATEGORY", "", type=DATATYPE_STRING128),
        SimVar("EngineType", "ENGINE TYPE", "Enum"),
        SimVarArray("EngVibration", "ENG VIBRATION", "Number", min=1, max=4),
        SimVarArray("EngRPM", "GENERAL ENG PCT MAX RPM", "percent", min=1, max=4),
        SimVar("NumEngines", "NUMBER OF ENGINES", "Number", type=DATATYPE_INT32),
        SimVarArray("AmbWind", "AMBIENT WIND <>", "meter/second", keywords= ("X", "Y", "Z")),
        SimVarArray("VelWorld", "VELOCITY WORLD <>", "meter/second", keywords= ("X", "Y", "Z")),
        SimVarArray("WeightOnWheels", "CONTACT POINT COMPRESSION", "Number", min=0, max=2),
        SimVarArray("Flaps", "TRAILING EDGE FLAPS <> PERCENT", "Percent Over 100", keywords=("LEFT", "RIGHT")),
        SimVarArray("Gear", "GEAR <> POSITION", "Percent Over 100", keywords=("LEFT", "RIGHT")),
        SimVarArray("RetractableGear", "IS GEAR RETRACTABLE", "bool"),
        SimVarArray("Spoilers", "SPOILERS <> POSITION", "Percent Over 100", keywords=("LEFT", "RIGHT")),
        SimVarArray("Afterburner", "TURB ENG AFTERBURNER", "Number", min=1, max=2),
        SimVar("AfterburnerPct", "TURB ENG AFTERBURNER PCT ACTIVE", "Percent Over 100"),
        SimVar("ACisFBW", "FLY BY WIRE FAC SWITCH", "bool"),
        SimVar("StallWarning", "STALL WARNING", "bool"),
        SimVar("h145SEMAx", "L:DEBUG_SEMA_PCT_X", sc_unit="percent over 100"),
        SimVar("h145SEMAy", "L:DEBUG_SEMA_PCT_Y", sc_unit="percent over 100"),
        SimVar("h145AfcsSemaPedalX", "L:DEBUG_AFCS_SYS_SEMA_YAW", sc_unit="position"),
        SimVar("h145AfcsMaster", "L:H145_SDK_AFCS_MASTER", "number"),
        SimVar("h145TrimRelease", "L:H145_SDK_AFCS_CYCLIC_TRIM_IS_RELEASED", "bool"),
        SimVar("h160TrimRelease", "L:H160_SDK_AFCS_CYCLIC_TRIM_IS_RELEASED", "bool"),
        SimVar("h145CollectiveRelease", "L:H145_SDK_AFCS_COLLECTIVE_TRIM_IS_RELEASED", "bool"),
        SimVar("h160CollectiveRelease", "L:H160_SDK_AFCS_COLLECTIVE_TRIM_IS_RELEASED", "bool"),
        SimVar("h145CollectiveAfcsMode", "L:H145_SDK_AFCS_MODE_COLLECTIVE", "enum"),
        SimVar("h160CollectiveAfcsMode", "L:H160_SDK_AFCS_MODE_COLLECTIVE", "enum"),
        SimVar("h145HandsOnCyclic", "L:H145_SDK_AFCS_CYCLIC_USER_PUSHING_ON_SPRINGS", "enum"),
        SimVar("h160HandsOnCyclic", "L:H160_SDK_AFCS_CYCLIC_USER_PUSHING_ON_SPRINGS", "enum"),
        SimVar("CollectivePos", "COLLECTIVE POSITION", "percent over 100"),
        SimVar("TailRotorPedalPos", "TAIL ROTOR BLADE PITCH PCT", "percent over 100"),
        SimVar("HPGVRSDatum", "L:DEBUG_VRS2_DATUM", "enum"),
        SimVar("HPGVRSIsInVRS", "L:DEBUG_VRS2_IS_IN_VRS", "enum"),
    ]
    
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.sc = None
        self._quit = False

        self._sim_paused = False
        self._sim_started = 0
        self._sim_state = 0
        self._final_frame_sent = 0
        self._events_to_send = []
        self._simdatums_to_send = []


        self.subscribed_vars = []

    def _subscribe(self):
        def_id = 0x1234

        i = 0
        for sv in (self.sim_vars):
            if isinstance(sv, SimVarArray):
                for sv in sv.vars:
                    logging.debug(f"Subscribe SimVar {i} {sv}")
                    self.sc.AddToDataDefinition(def_id, sv.var, sv.sc_unit, sv.datatype, 0, i)
                    self.subscribed_vars.append(sv)
                    i+=1
            else:    
                logging.debug(f"Subscribe SimVar {i} {sv}")
                self.sc.AddToDataDefinition(def_id, sv.var, sv.sc_unit, sv.datatype, 0, i)
                self.subscribed_vars.append(sv)
                i+=1

        self.sc.RequestDataOnSimObject(
            REQ_ID,  # request identifier for response packets
            def_id,  # the data definition group
            OBJECT_ID_USER,
            PERIOD_SIM_FRAME,
            DATA_REQUEST_FLAG_TAGGED,# DATA_REQUEST_FLAG_CHANGED | DATA_REQUEST_FLAG_TAGGED,
            0,  # number of periods before starting events
            1,  # number of periods between events, e.g. with PERIOD_SIM_FRAME
            0,  # number of repeats, 0 is forever
        )
    # blocks and reads telemetry

    def set_simdatum_to_msfs(self, simvar, value, units=None):
        self._simdatums_to_send.append((simvar, value, units))

    def send_event_to_msfs(self, event, data: int = 0):
        self._events_to_send.append((event, data))

    def tx_simdatums_to_msfs(self):
        while self._simdatums_to_send:
            simvar, value, units = self._simdatums_to_send.pop(0)
            try:
                self.sc.set_simdatum(simvar, value, units=units)
            except Exception as e:
                logging.error(f"Error sending {simvar} value {value} to MSFS: {e}")
                # self.telem_data['error'] = 1


    def tx_events_to_msfs(self):
        while self._events_to_send:
            event, data = self._events_to_send.pop(0)
            logging.debug(f"event {event}   data {data}")
            if event.startswith('L:'):
                self.set_simdatum_to_msfs(event, data, units="number")
            else:
                try:
                    self.sc.send_event(event, data)
                    # self.telem_data[event] = data
                except Exception as e:
                    logging.error(f"Error setting event:{event} value:{data} to MSFS: {e}")
                    # self.telem_data['error'] = 1

    def _read_telem(self) -> bool:
        pRecv = RECV_P()
        nSize = DWORD()
        while not self._quit:
            self.tx_events_to_msfs()  # tx any pending sim events that are queued
            self.tx_simdatums_to_msfs()  # tx any pending simdatum sets that are queued
            try:
                #print('Trying')
                self.sc.GetNextDispatch(byref(pRecv), byref(nSize))
            except OSError as e:
                #print(e)
                time.sleep(0.001)
                continue

            recv = ReceiverInstance.cast_recv(pRecv)
            #print(f"got {recv.__class__.__name__}")
            if isinstance(recv, RECV_EXCEPTION):
                logging.error(f"SimConnect exception {recv.dwException}, sendID {recv.dwSendID}, index {recv.dwIndex}")
            elif isinstance(recv, RECV_QUIT):
                logging.info("Quit received")
                self.emit_event("Quit")
                break
            elif isinstance(recv, RECV_OPEN):
                self.emit_event("Open")
                
            elif isinstance(recv, RECV_EVENT):
                if recv.uEventID == EV_PAUSED:
                    logging.debug(f"EVENT PAUSED,  EVENT: {recv.uEventID}, DATA: {recv.dwData}")
                    self._sim_paused = recv.dwData
                    self.emit_event("Paused", recv.dwData)
                elif recv.uEventID == EV_STARTED:
                    logging.debug(f"EVENT STARTED,  EVENT: {recv.uEventID}, DATA: {recv.dwData}")
                    self._sim_started = 1
                    self.emit_event("SimStart")
                elif recv.uEventID == EV_STOPPED:
                    logging.debug(f"EVENT STOPPED, EVENT: {recv.uEventID}, DATA: {recv.dwData}")
                    self._sim_started = 0
                    self.emit_event("SimStop")
                elif recv.uEventID == EV_SIMSTATE:
                    logging.debug(f"EVENT SIMSTATE, EVENT: {recv.uEventID}, DATA: {recv.dwData}")
                    self._sim_state = recv.dwData
                    self.emit_event("SimState", recv.dwData)

            elif isinstance(recv, RECV_SIMOBJECT_DATA):
                logging.debug(f"Received SIMOBJECT_DATA with {recv.dwDefineCount} data elements, flags {recv.dwFlags}")
                #print(f"Received SIMOBJECT_DATA with {recv.dwDefineCount} data elements, flags {recv.dwFlags}")
                if recv.dwRequestID == REQ_ID:
                    #print(f"Matched request 0x{req_id:X}")
                    data = {}
                    data["SimPaused"] = self._sim_paused
                    # data["FlightStarted"] = self._sim_state
                    offset = RECV_SIMOBJECT_DATA.dwData.offset
                    for _ in range(recv.dwDefineCount):
                        idx = cast(byref(recv, offset), POINTER(DWORD))[0]
                        offset += sizeof(DWORD)
                        # DATATYPE_FLOAT64 => c_double
                        var : SimVar = self.subscribed_vars[idx]
                        c_type = var.c_type
                        if var.datatype == DATATYPE_STRING128: #fixme: other string types
                            val = str(cast(byref(recv, offset), POINTER(c_type))[0].value, "utf-8")
                        else:
                            val = cast(byref(recv, offset), POINTER(c_type))[0]
                        offset += sizeof(c_type)
                        val = var._calculate(val)
                        
                        if var.parent: # var is part of array
                            var.parent.values[var.index-var.parent.min] = val
                            data[var.parent.name] = var.parent.values
                        else:
                            data[var.name] = val
                            
                    # if not self._sim_paused and not data["Parked"] and not data["Slew"]:     # fixme: figure out why simstart/stop and sim events dont work right
                    #     self.emit_packet(data)
                    #     self._final_frame_sent = 0
                    if self._sim_paused or data["Parked"] or data["Slew"]:     # fixme: figure out why simstart/stop and sim events dont work right
                        data["STOP"] = 1

                    self.emit_packet(data)

            else:
                print("Received", recv)

    def emit_packet(self, data):
        pass

    def emit_event(self, event, *args):
        pass

    def quit(self):
        self._quit = True

    def run(self):
        while not self._quit:
            try:
                logging.info("Trying SimConnect")
                with SimConnect("TelemFFB") as self.sc:
                    self.sc.SubscribeToSystemEvent(EV_PAUSED, "Pause")
                    self.sc.SubscribeToSystemEvent(EV_STARTED, "SimStart")
                    self.sc.SubscribeToSystemEvent(EV_STOPPED, "SimStop")
                    self.sc.SubscribeToSystemEvent(EV_SIMSTATE, "Sim")

                    self._subscribe()
                    self._read_telem()

            except OSError:
                time.sleep(10)
                pass

# run test
if __name__ == "__main__":
    class SimConnectTest(SimConnectManager):
        def emit_packet(self, data):
            print(data)

    s = SimConnectTest()
    s.start()
    while True:
        time.sleep(1)