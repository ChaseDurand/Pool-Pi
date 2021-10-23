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
        if (looking_for_start == False):
            return
        if (buffer_full == True):
            return
        serChar = ser.read()
        while (serChar != STX):
            serChar = ser.read()
            #add timeout condition
        #we have STX
        buffer += DLE
        buffer += STX
        while (True):
            buffer += ser.read_until(DLE, 80)
            serChar = ser.read() #TODO Some conversion is taking place when storing to buffer and it affects comparison, need to investigate
            buffer += serChar
            if (serChar == ETX):
                break

        #add check for timeout
        looking_for_start = False
        buffer_full = True


def parseBuffer():
    global buffer_full
    global looking_for_start
    global ready_to_send
    global buffer
    if (buffer_full):
        # Confirm checksum
        checksum = 0
        for i in buffer[:-4]:
            checksum += i
        if checksum != buffer[-3]:  #TODO accommodate two byte chcksums
            print(checksum)
            print(buffer[-3])
        # Get message
        if (buffer == KEEP_ALIVE[0]):
            print(KEEP_ALIVE[1])
        else:
            print(buffer)
        buffer.clear()
        looking_for_start = True
        buffer_full = False
        ready_to_send = True


def sendCommand():
    global command_queue
    global ready_to_send
    if (len(command_queue) != 0 and ready_to_send == True):
        # get command from queue and send
        # need flag for indicating command needs to be confirmed
        # need to initialize counters for command confirmation
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
