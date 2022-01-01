# Represents the state of the system
import json
import serial
from gpiozero import LED
from enum import Enum
import time

# class attributeStates(Enum):
#     INIT: 0
#     OFF: 1
#     BLINK: 2
#     ON: 3

MAX_SEND_ATTEMPTS = 10  # Max number of times command will be sent if not confirmed
# MAX_CONFIRM_ATTEMPTS = 20  # Max number of inbound message parsed to look for confirmation before resending command
SEND_TIME_DELAY = 0.8

commands = {
    'aux4':
    b'\x10\x02\x00\x02\x00\x10\x00\x00\x00\x00\x10\x00\x00\x00\x00\x34\x10\x03'
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
        self.pool = {"state": "INIT", "version": 0}
        self.spa = {"state": "INIT", "version": 0}
        self.filter = {"state": "INIT", "version": 0}
        self.lights = {"state": "INIT", "version": 0}
        self.aux1 = {"state": "INIT", "version": 0}
        self.aux2 = {"state": "INIT", "version": 0}
        self.service = {"state": "INIT", "version": 0}
        self.aux3 = {"state": "INIT", "version": 0}
        self.aux4 = {"state": "INIT", "version": 0}
        self.aux5 = {"state": "INIT", "version": 0}
        self.aux6 = {"state": "INIT", "version": 0}
        self.valve4 = {"state": "INIT", "version": 0}
        self.spillover = {"state": "INIT", "version": 0}
        self.systemOff = {"state": "INIT", "version": 0}
        self.aux7 = {"state": "INIT", "version": 0}
        self.aux8 = {"state": "INIT", "version": 0}
        self.aux9 = {"state": "INIT", "version": 0}
        self.aux10 = {"state": "INIT", "version": 0}
        self.aux11 = {"state": "INIT", "version": 0}
        self.aux12 = {"state": "INIT", "version": 0}
        self.aux13 = {"state": "INIT", "version": 0}
        self.aux14 = {"state": "INIT", "version": 0}
        self.superChlorinate = {"state": "INIT", "version": 0}
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
    confirm_attempts = 0
    nextSendTime = 0
    sendingMessage = False
    lastModelTime = 0

    def initiateSend(self, commandID, commandState, commandVersion):
        self.ready_to_send = False
        self.sendingMessage = True
        self.parameter = commandID
        self.targetState = commandState
        self.parameterVersion = commandVersion
        self.send_attempts = 0
        # self.checkSend()

    def checkSend(self):
        #Return true if ready to send
        if self.send_attempts >= MAX_SEND_ATTEMPTS:
            #message failed
            print('message failed')
            self.sendingMessage = False
            return False
        elif time.time() < self.nextSendTime:
            #not ready to attempt additional send
            return False
        self.nextSendTime = time.time() + SEND_TIME_DELAY
        self.send_attempts += 1
        print('Send attempt: ', self.send_attempts)
        return True