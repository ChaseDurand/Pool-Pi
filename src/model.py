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

command_start = b'\x10\x02'
command_sender = b'\x00\x02'  #TODO see if this matters or can be anything
command_end = b'\x10\x03'

DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

#TODO unify terminology to make command/message names consistent
commands = {
    'service': b'\x08\x00\x00\x00',
    'pool': b'\x40\x00\x00\x00',
    'spa': b'\x40\x00\x00\x00',
    'spillover': b'\x40\x00\x00\x00',
    'filter': b'\x00\x80\x00\x00',
    'lights': b'\x00\x01\x00\x00',
    'heater1': b'\x00\x00\x04\x00',
    'valve3': b'\x00\x00\x01\x00',
    'aux1': b'\x00\x02\x00\x00',
    'aux2': b'\x00\x04\x00\x00',
    'aux3': b'\x00\x08\x00\x00',
    'aux4': b'\x00\x10\x00\x00\x00',
    'aux5': b'\x00\x20\x00\x00',
    'aux6': b'\x00\x40\x00\x00',
    'aux7': b'',
    'aux8': b'',
    'aux9': b'',
    'aux10': b'',
    'aux11': b'',
    'aux12': b'',
    'aux13': b'',
    'aux14': b'',
    'valve4': b'',
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
        self.checkSystem = "WAITING FOR CHECKSYSTEM"  #TODO check why checksystem stays on init state when LED is off
        #TODO combine pool/spa/spillover controls
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
        self.buffer = bytearray()  #Buffer to store serial frame
        self.buffer_full = False  #Flag to indicate if buffer has a full frame
        self.looking_for_start = True  #Flag to indicate if we are awaiting frame start (DLE STX)
        self.ser = serial.Serial(port='/dev/ttyAMA0',
                                 baudrate=19200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_TWO)
        self.send_enable = LED(
            17
        )  #GPIO connected to MAX485 ~RE and DE. High = sending, low = receiving.
        self.send_enable.off()  #Set to receive mode
        self.ready_to_send = False  #Flag if we have a command to send and have checked to determine we need to send the command

    def send(self, msg):
        # Enable RS485 output, send message, disable RS485 output.
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
    parameter = ''  # Name of parameter command is changing
    targetState = ''  # State we want parameter to be in
    send_attempts = 0  # Number of times command has been sent
    sendingMessage = False  #Flag if we are currently trying to send a command
    lastModelTime = 0  #Timestamp of last model (LED update) seen to ensure we witness a new model before attempting additional send
    fullCommand = b''  #Bytearray of full frame to send
    keepAliveCount = 0  #Number of keep alive frames we have seen in a row

    def initiateSend(self, commandID, commandState):
        # Form full frame to send from start tx, frame type, command, checksum, and end tx.
        partialFrame = command_start + command_sender + commands[
            commandID] + commands[
                commandID]  # Form partial frame from start tx, frame type, and command.
        #Calculate checksum
        checksum = 0
        for byte in partialFrame:
            checksum += byte
        checksum = checksum.to_bytes(2, 'big')
        # TODO add check for x10 in checksum and append x00 if needed
        self.fullCommand = partialFrame + checksum + command_end
        self.keepAliveCount = 0
        self.sendingMessage = True
        self.parameter = commandID
        self.targetState = commandState
        self.send_attempts = 0
        return

    def checkSendAttempts(self):
        # Return true if we have more sending attemtps to try
        # Return false and stop command sending if we have exceeded max send attempts
        if self.send_attempts >= MAX_SEND_ATTEMPTS:
            # Command failed
            print(f'{Fore.RED}Command failed.{Style.RESET_ALL}')
            self.sendingMessage = False
            return False
        self.send_attempts += 1
        print(f'{Fore.YELLOW}Send attempt:	{Style.RESET_ALL}',
              self.send_attempts)
        return True
