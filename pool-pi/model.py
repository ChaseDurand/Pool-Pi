# Represents the state of the system
import json
import serial
from gpiozero import LED
from enum import Enum


class attributeStates(Enum):
    INIT: 0
    OFF: 1
    BLINK: 2
    ON: 3


# Records states of the pool
class PoolModel:
    def __init__(self):
        self.display = "WAITING FOR DISPLAY"
        self.airtemp = "WAITING FOR AIRTEMP"
        self.pooltemp = "WAITING FOR POOLTEMP"
        self.datetime = "WAITING FOR DATETIME"
        self.salinity = "WAITING FOR SALINITY"
        self.heater1 = {"state": attributeStates.INIT, "version": 0}
        self.valve3 = {"state": attributeStates.INIT, "version": 0}
        self.checkSystem = {"state": attributeStates.INIT, "version": 0}
        self.pool = {"state": attributeStates.INIT, "version": 0}
        self.spa = {"state": attributeStates.INIT, "version": 0}
        self.filter = {"state": attributeStates.INIT, "version": 0}
        self.lights = {"state": attributeStates.INIT, "version": 0}
        self.aux1 = {"state": attributeStates.INIT, "version": 0}
        self.aux2 = {"state": attributeStates.INIT, "version": 0}
        self.service = {"state": attributeStates.INIT, "version": 0}
        self.aux3 = {"state": attributeStates.INIT, "version": 0}
        self.aux4 = {"state": attributeStates.INIT, "version": 0}
        self.aux5 = {"state": attributeStates.INIT, "version": 0}
        self.aux6 = {"state": attributeStates.INIT, "version": 0}
        self.valve4 = {"state": attributeStates.INIT, "version": 0}
        self.spillover = {"state": attributeStates.INIT, "version": 0}
        self.systemOff = {"state": attributeStates.INIT, "version": 0}
        self.aux7 = {"state": attributeStates.INIT, "version": 0}
        self.aux8 = {"state": attributeStates.INIT, "version": 0}
        self.aux9 = {"state": attributeStates.INIT, "version": 0}
        self.aux10 = {"state": attributeStates.INIT, "version": 0}
        self.aux11 = {"state": attributeStates.INIT, "version": 0}
        self.aux12 = {"state": attributeStates.INIT, "version": 0}
        self.aux13 = {"state": attributeStates.INIT, "version": 0}
        self.aux14 = {"state": attributeStates.INIT, "version": 0}
        self.superChlorinate = {"state": attributeStates.INIT, "version": 0}

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

    def toJSON(self):
        return json.dumps(vars(self))


class SerialHandler:
    def __init__(self):
        self.buffer = bytearray()
        self.buffer_full = False
        self.looking_for_start = True
        self.ser = serial.Serial(port='/dev/ttyAMA0',
                                 baudrate=19200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_TWO)

    def send(self, msg):
        LED(17).on()
        self.ser.write(msg)
        self.ser.flush()
        LED(17).off

    def read(self):
        return self.ser.read()

    def in_waiting(self):
        return self.ser.in_waiting()