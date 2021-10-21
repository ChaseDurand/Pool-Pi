import serial
import binascii
import string
from gpiozero import LED

buffer = []
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
                    partiy=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO)

DLE = binascii.unhexlify('10')
STX = binascii.unhexlify('02')
ETX = binascii.unhexlify('03')

while (True):
    # Read Serial Bus
    if (ser.in_waiting() != 0):
        # We have data to read form the serial line
        serChar = ser.read()

        if (looking_for_start):
            if (serChar == DLE):
                buffer.append(serChar)
                serChar = ser.read()
                if (serChar == STX):
                    # We have found the start!
                    buffer.append(serChar)
                    looking_for_start = False
                else:
                    # Haven't actually found start,
                    buffer.clear()
        else:
            #Looking for end
            if (serChar == DLE):
                buffer.append(serChar)
                serChar = ser.read()
                if (serChar == ETX):
                    # We have found the end!
                    buffer.append(serChar)
                    looking_for_start = True
                    buffer_full = True
                else:
                    # Haven't actually found end
                    buffer.append(serChar)
            else:
                buffer.append(serChar)

    # Parse Buffer
    if (buffer_full):
        print(buffer)
        buffer.clear()
        looking_for_start == True
        buffer_full = False

    # Send to Serial Bus
    if (len(command_queue) != 0 and ready_to_send == True):
        # do stuff
        ser.write()
        ser.flush()