import json
import serial
from gpiozero import LED
import time
from commands import *
import logging


class PoolModel:
    """
    Records the current states of the pool through LED and display updates
    """

    def __init__(self):
        self.display = "WAITING FOR DISPLAY"
        self.display_mask = [
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]  # 1 if blinking, 0 if not
        self.checksystem = "WAITING FOR CHECKSYSTEM"
        self.systemoff = "WAITING FOR SYSTEMOFF"
        self.superchlorinate = "WAITING FOR SUPERCHLORINATE"
        for parameter in button_toggle:
            setattr(self, parameter, {"state": "INIT", "version": 0})
        self.flag_data_changed = (
            False  # True if there is new data for web, false if no new data
        )
        self.timestamp = 0  # Unix time that the last LED message was received
        self.sending_message = False

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
                setattr(self, parameter, data)

    def getParameterVersion(self, parameter):
        return getattr(self, parameter)["version"]

    def getParameterState(self, parameter):
        attribute = getattr(self, parameter)
        if isinstance(attribute, dict):
            # Attribute is dict and has version
            return getattr(self, parameter)["state"]
        if isinstance(attribute, str):
            # Attribute is string and does not require a version
            return attribute

    def updateTimestamp(self):
        self.timestamp = time.time()
        return

    def toJSON(self):
        """
        Remove data not used in front end then convert to JSON
        """
        jsonItems = vars(self).copy()
        jsonItems.pop("flag_data_changed")
        jsonItems.pop("timestamp")
        jsonItems.pop("systemoff")
        jsonItems.pop("superchlorinate")
        jsonItems.pop("aux7")
        jsonItems.pop("aux8")
        jsonItems.pop("aux9")
        jsonItems.pop("aux10")
        jsonItems.pop("aux11")
        jsonItems.pop("aux12")
        jsonItems.pop("aux13")
        jsonItems.pop("aux14")
        return json.dumps(jsonItems)


class SerialHandler:
    """
    Interface for serial operations
    """

    def __init__(self):
        self.buffer = bytearray()  # Buffer to store serial frame
        self.buffer_full = False  # Flag to indicate if buffer has a full frame
        self.looking_for_start = (
            True  # Flag to indicate if we are awaiting frame start (DLE STX)
        )
        self.ser = serial.Serial(
            port="/dev/ttyAMA0",
            baudrate=19200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
        )
        self.send_enable = LED(17)  # GPIO 17 = Pin 11. High = sending, low = receiving.
        self.send_enable.off()  # Set to receive mode
        self.ready_to_send = False  # Flag if we have a command to send and have checked to determine we need to send the command

    def send(self, msg):
        """
        Send a message via the serial interface.
        Enable RS485 output, send message, disable RS485 output.
        """
        self.send_enable.on()
        self.ser.write(msg)
        self.ser.flush()
        self.send_enable.off()

    def read(self):
        """
        Accessor to return character in serial input
        """
        return self.ser.read()

    def in_waiting(self):
        """
        Accessor to return number of characters in serial input
        """
        return self.ser.in_waiting

    def reset(self):
        """
        Clear serial input and get ready to look for start
        Called after a full message is parsed or when a message is invalid due to error
        """
        self.buffer.clear()
        self.looking_for_start = True
        self.buffer_full = False
        return


# Manages flow when sending commands
class CommandHandler:
    parameter = ""  # Name of parameter command is changing
    target_state = ""  # State we want parameter to be in
    send_attempts = 0  # Number of times command has been sent
    sending_message = False  # Flag if we are currently trying to send a command
    last_model_timestamp_seen = 0  # Timestamp of last model (LED update) seen to ensure we witness a new model before attempting additional send
    full_command = b""  # Bytearray of full frame to send
    keep_alive_count = 0  # Number of keep alive frames we have seen in a row
    confirm = True  # True if command needs to be confirmed, false if not (menu command)

    def initiateSend(self, commandID, commandState, commandConfirm):
        if commandConfirm == "1":
            self.confirm = True
            commandData = button_toggle[commandID]
        else:
            self.confirm = False
            commandData = buttons_menu[commandID]
        # Form full frame to send from start tx, frame type, command, checksum, and end tx.
        partialFrame = (
            DLE + STX + FRAME_TYPE_LOCAL_TOGGLE + commandData + commandData
        )  # Form partial frame from start tx, frame type, and command.
        # Calculate checksum
        checksum = 0
        for byte in partialFrame:
            checksum += byte
        checksum = checksum.to_bytes(2, "big")
        partialFrame = partialFrame + checksum
        # If any x10 appears in frameType, data, or checksum, add additional x00
        self.full_command = (
            partialFrame[0:2]
            + partialFrame[2:].replace(b"\x10", b"\x10\x00")
            + DLE
            + ETX
        )
        self.keep_alive_count = 0
        self.sending_message = True
        self.parameter = commandID
        self.target_state = commandState
        self.send_attempts = 0
        return

    def sendAttemptsRemain(self):
        """
        Return true if we have more sending attempts to try
        Return false and stop command sending if we have exceeded max send attempts
        """
        if self.send_attempts >= MAX_SEND_ATTEMPTS:
            # Command failed
            logging.error(f"Command failed after {MAX_SEND_ATTEMPTS} attempts.")
            self.sending_message = False
            return False
        self.send_attempts += 1
        logging.info(f"Command send attempt {self.send_attempts}.")
        return True
