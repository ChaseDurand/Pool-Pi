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
                #we have found start
                buffer += DLE
                buffer += STX
            else:
                #we have not found start
                return
    else:
        #we are adding to buffer and looking for ETX
        buffer += serChar
        if serChar == ETX:
            #confirm DLE ETX sequence
            if buffer[-2] == DLE:
                #We have found DLE ETX
                buffer += ETX
                buffer_full = True
                return
        '''
        serChar = ser.read()
        while (serChar != STX):
            serChar = ser.read()
            #add timeout condition
        #we have STX
        buffer += DLE
        buffer += STX
        while (True):
            buffer += ser.read_until(DLE, 80)  #TODO change back to read()
            serChar = ser.read(
            )  #TODO Some conversion is taking place when storing to buffer and it affects comparison, need to investigate
            buffer += serChar
            if (serChar == ETX):
                break
        #add check for timeout
        looking_for_start = False
        buffer_full = True
        '''


def parseBuffer():
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
            previous_message = NON_KEEP_ALIVE
            print(buffer)
        buffer.clear()
        looking_for_start = True
        buffer_full = False
        ready_to_send = True


def confirmChecksum(message):
    target_checksum = buffer[-4] * (16**2) + buffer[
        -3]  # Convert two byte checksum to single value
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