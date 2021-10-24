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
previous_message = NON_KEEP_ALIVE

ser = serial.Serial(port='/dev/ttyAMA0',
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO)


def readSerialBus():
    # Read data from the serial bus to build full buffer
    # Serial commands begin with DLE STX and terminate with DLE ETX
    # With the exception of searching for the two start bytes, this function only reads one byte to prevent blocking other processes
    # When looking for start of message, looking_for_start is True
    # When buffer is filled with a full command and ready to be parseed, set buffer_full to True
    global looking_for_start
    global buffer
    global buffer_full
    if (ser.in_waiting == 0):
        return
    if (buffer_full == True):
        return
    serChar = ser.read()
    if looking_for_start:
        if serChar == DLE:
            serChar = ser.read()
            if serChar == STX:
                # We have found start (DLE STX)
                buffer.clear()
                buffer += DLE
                buffer += STX
                looking_for_start = False
                return
            else:
                # We have found DLE but not DLE STX
                return
        else:
            # We are only interested in DLE to find potential start
            return
    else:
        # We are adding to buffer while looking for DLE ETX
        buffer += serChar
        # Check if we have found DLE ETX
        if ((serChar == ETX) and (buffer[-2] == int.from_bytes(DLE, "big"))):
            # We have found DLE ETX
            buffer_full = True
            looking_for_start = True
            return


def parseBuffer():

    #TODO identify and account for possible x00
    '''
    The DLE, STX and Command/Data fields are added together to provide the 2-byte Checksum. If 
    any of the bytes of the Command/Data Field or Checksum are equal to the DLE character (10H), a 
    NULL character (00H) is inserted into the transmitted data stream immediately after that byte. That 
    NULL character must then be removed by the receiver.
    '''
    global buffer_full
    global looking_for_start
    global ready_to_send
    global buffer
    global previous_message
    if (buffer_full):
        # Confirm checksum
        if (confirmChecksum(buffer) == False):
            print("Checksum mismatch! ", buffer)
        # Get message
        if (buffer == KEEP_ALIVE[0]):
            if previous_message != KEEP_ALIVE:
                print(KEEP_ALIVE[1])
                previous_message = KEEP_ALIVE
        else:
            command = buffer[2:4]
            data = buffer[4:-4]
            previous_message = NON_KEEP_ALIVE
            if command == FRAME_UPDATE_DISPLAY[0]:
                print('Display:', data)
            else:
                print(command, buffer)
        buffer.clear()
        looking_for_start = True
        buffer_full = False
        ready_to_send = True


def confirmChecksum(message):
    # Check if the calculated checksum for messages equals the expected sent checksum
    # Return True if checksums match, False if not
    # Checksum is 4th and 3rd to last bytes of command (last bytes prior to DLE ETX)
    # Checksum includes DLE STX and command/data
    target_checksum = buffer[-4] * (16**2) + buffer[
        -3]  # Convert two byte checksum to single value #TODO change to int.from_bytes
    checksum = 0
    for i in message[:-4]:
        checksum += i
    if checksum == target_checksum:
        return True
    else:
        return False


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
    #TODO
    return


def updateModel():
    #TODO
    return


def main():
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


if __name__ == '__main__':
    main()
