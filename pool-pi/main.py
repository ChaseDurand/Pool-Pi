import serial
from gpiozero import LED
from commands import *

buffer = bytearray()
buffer_full = False
command_queue = []
ready_to_send = False
send_enable = LED(2)
send_enable.off()
sending_attempts = 0
confirm_attempts = 0
looking_for_start = True
MAX_SEND_ATTEMPTS = 5  # Max number of times command will be sent if not confirmed
MAX_CONFIRM_ATTEMPTS = 20  # Max number of inbound message parsed to look for confirmation before resending command

ser = serial.Serial(port='/dev/ttyAMA0',
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO)


def readSerialBus():
    global looking_for_start
    global buffer
    global buffer_full
    if (ser.in_waiting != 0):
        # We have data to read form the serial line
        serChar = ser.read()
        if (looking_for_start):
            if (serChar == DLE):
                #buffer.append(serChar)
                buffer += serChar
                serChar = ser.read()
                if (serChar == STX):
                    # We have found the start!
                    #buffer.append(serChar)
                    buffer += serChar
                    looking_for_start = False
                else:
                    # Haven't actually found start,
                    buffer.clear()
        else:
            #Looking for end
            if (serChar == DLE):
                #buffer.append(serChar)
                buffer += serChar
                serChar = ser.read()
                if (serChar == ETX):
                    # We have found the end!
                    #buffer.append(serChar)
                    buffer += serChar
                    looking_for_start = True
                    buffer_full = True
                else:
                    # Haven't actually found end
                    #buffer.append(serChar)
                    buffer += serChar
            else:
                buffer += serChar
                #buffer.append(serChar)


def parseBuffer():
    global buffer_full
    global looking_for_start
    global ready_to_send
    global buffer
    if (buffer_full):
        # Confirm checksum
        # Get message
        print(buffer)
        buffer.clear()
        looking_for_start == True
        buffer_full = False
        ready_to_send = True


def sendCommand():
    global command_queue
    global ready_to_send
    if (len(command_queue) != 0 and ready_to_send == True):
        # do stuff
        send_enable.on()
        ser.write()
        ser.flush()
        send_enable.off()
        ready_to_send = False


def getCommand():
    return


def updateModel():
    return


while (True):
    # Read Serial Bus
    readSerialBus()

    # Parse Buffer
    parseBuffer()

    # Update pool model
    updateModel()

    # Check for new commands
    getCommand()

    # Send to Serial Bus
    sendCommand()
