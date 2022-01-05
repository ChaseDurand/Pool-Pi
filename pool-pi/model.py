# Represents the state of the system
import json
import serial
from gpiozero import LED
from enum import Enum
import time
from colorama import Fore, Style

# class attributeStates(Enum):
#     INIT: 0
#     OFF: 1
#     BLINK: 2
#     ON: 3

MAX_SEND_ATTEMPTS = 10  # Max number of times command will be sent if not confirmed

commands = {
    'spa':
    b'\x10\x02\x00\x02\x00\x10\x00\x00\x00\x00\x10\x00\x00\x00\x00\x34\x10\x03',
    'aux4':
    b'\x10\x02\x00\x02\x00\x10\x00\x00\x00\x00\x10\x00\x00\x00\x00\x34\x10\x03',
    'spa': b'',
    'filter': b'',
    'lights': b'',
    'aux1': b'',
    'aux2': b'',
    'service':
    b'\x10\x02\x00\x02\x08\x00\x00\x00\x08\x00\x00\x00\x00\x24\x10\x03',
    'aux3':
    b'\x10\x02\x00\x02\x00\x08\x00\x00\x00\x08\x00\x00\x00\x24\x10\x03',
    'aux4':
    b'\x10\x02\x00\x02\x00\x10\x00\x00\x00\x00\x10\x00\x00\x00\x00\x34\x10\x03',
    'aux5': b'',
    'aux6': b'',
    'aux7': b'',
    'aux8': b'',
    'aux9': b'',
    'aux10': b'',
    'aux11': b'',
    'aux12': b'',
    'aux13': b'',
    'aux14': b'',
    'valve4': b'',
    'spillover': b'',
    'systemOff': b'',
    'superChlorinate': b''
}


# Records states of the pool
class PoolModel:
    def __init__(self):
        self.display = "WAITING FOR DISPLAY"
        self.airtemp = "WAITING FOR AIRTEMP"
        self.pooltemp = "WAITING FOR POOLTEMP"
        self.datetime = "WAITING FOR DATETIME"
        self.salinity = "WAITING FOR SALINITY"
        self.heater1 = {"state": "INIT", "version": 0}
        self.valve3 = {"state": "INIT", "version": 0}
        self.checkSystem = "WAITING FOR CHECKSYSTEM"  #TODO check why checksystem stays on init state when LED is off
        self.pool = {
            "state": "INIT",
            "version": 0
        }  #TODO combine pool/spa/spillover controls
        for parameter in commands:
            setattr(self, parameter, {"state": "INIT", "version": 0})
        self.flag_data_changed = False  #True if there is new data for web, false if no new data
        self.last_update_time = 0  #Time that model was last updated (when last LED message was parsed)

    def updateParameter(self, parameter, data):
        attribute = getattr(self, parameter)
        if isinstance(attribute, dict):
            # Attribute is dict and has version
            if attribute["state"] != data:
                attribute["state"] = data
                attribute["version"] += 1
        if isinstance(attribute, str):
            # Attribute is string and does not require a version
            if attribute != data:
                attribute = data

    def getParameterVersion(self, parameter):
        return getattr(self, parameter)["version"]

    def getParameterState(self, parameter):
        return getattr(self, parameter)["state"]

    def updateTime(self):
        self.last_update_time = time.time()
        return

    def toJSON(self):
        return json.dumps(vars(self))
        #TODO strip flag_data_changed before sending to front end


class SerialHandler:
    def __init__(self):
        self.buffer = bytearray()
        self.buffer_full = False
        self.looking_for_start = True
        self.ser = serial.Serial(port='/dev/ttyAMA0',
                                 baudrate=19200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_TWO)
        self.send_enable = LED(17)
        self.send_enable.off()
        self.ready_to_send = False

    def send(self, msg):
        self.send_enable.on()
        self.ser.write(msg)
        self.ser.flush()
        print(msg)
        self.send_enable.off()

    def read(self):
        return self.ser.read()

    def in_waiting(self):
        return self.ser.in_waiting


class CommandHandler:
    sending_queue = []
    parameter = ''
    targetState = ''
    parameterVersion = ''
    send_attempts = 0
    nextSendTime = 0
    sendingMessage = False
    lastModelTime = 0

    def initiateSend(self, commandID, commandState, commandVersion):
        self.sendingMessage = True
        self.parameter = commandID
        self.targetState = commandState
        self.parameterVersion = commandVersion
        self.send_attempts = 0
        return

    def checkSend(self):
        #Return true if ready to send
        if self.send_attempts >= MAX_SEND_ATTEMPTS:
            #message failed
            print('message failed')
            self.sendingMessage = False
            return False
        self.send_attempts += 1
        print(f'{Fore.RED}Send attempt:	{Style.RESET_ALL}', self.send_attempts)
        return True
