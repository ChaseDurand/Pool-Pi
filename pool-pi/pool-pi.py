from commands import *
from threading import Thread
from model import *
from web import *

command_queue = []
ready_to_send = False
sending_attempts = 0
confirm_attempts = 0
MAX_SEND_ATTEMPTS = 5  # Max number of times command will be sent if not confirmed
MAX_CONFIRM_ATTEMPTS = 20  # Max number of inbound message parsed to look for confirmation before resending command

salt_level = 0  #test salt level variable for web proof of concept
flag_data_changed = False  #True if there is new data for site, false if no new data


def readSerialBus(serialHandler):
    # Read data from the serial bus to build full buffer
    # Serial commands begin with DLE STX and terminate with DLE ETX
    # With the exception of searching for the two start bytes, this function only reads one byte to prevent blocking other processes
    # When looking for start of message, looking_for_start is True
    # When buffer is filled with a full command and ready to be parseed, set buffer_full to True
    if (serialHandler.in_waiting() == 0):
        return
    if (serialHandler.buffer_full == True):
        return
    serChar = serialHandler.read()
    if serialHandler.looking_for_start:
        if serChar == DLE:
            serChar = serialHandler.read()
            if serChar == STX:
                # We have found start (DLE STX)
                serialHandler.buffer.clear()
                serialHandler.buffer += DLE
                serialHandler.buffer += STX
                serialHandler.looking_for_start = False
                return
            else:
                # We have found DLE but not DLE STX
                return
        else:
            # We are only interested in DLE to find potential start
            return
    else:
        # We are adding to buffer while looking for DLE ETX
        serialHandler.buffer += serChar
        # Check if we have found DLE ETX
        if ((serChar == ETX)
                and (serialHandler.buffer[-2] == int.from_bytes(DLE, "big"))):
            # We have found DLE ETX
            serialHandler.buffer_full = True
            serialHandler.looking_for_start = True
            return


def parseBuffer(serialHandler, poolModel):
    '''
    The DLE, STX and Command/Data fields are added together to provide the 2-byte Checksum. If 
    any of the bytes of the Command/Data Field or Checksum are equal to the DLE character (10H), a 
    NULL character (00H) is inserted into the transmitted data stream immediately after that byte. That 
    NULL character must then be removed by the receiver.
    '''
    global ready_to_send
    if (serialHandler.buffer_full):
        # Confirm checksum
        if (confirmChecksum(serialHandler.buffer) == False):
            print("Checksum mismatch! ", serialHandler.buffer)
        # Get message
        if (serialHandler.buffer != KEEP_ALIVE[0]):
            #TODO identify and account for possible x00 after x10 (DLE)
            while (True):
                try:
                    index_to_remove = serialHandler.buffer.index(DLE, 2,
                                                                 -2) + 1
                    removed = serialHandler.buffer.pop(index_to_remove)
                    #TODO fix unknown bug here
                    if removed != b'\x00':
                        print('Error, expected 00 but removed', removed)
                except ValueError:
                    break
            command = serialHandler.buffer[2:4]
            data = serialHandler.buffer[4:-4]
            if command == FRAME_UPDATE_DISPLAY[0]:
                parseDisplay(data, poolModel)
            elif command == FRAME_UPDATE_LEDS[0]:
                parseLEDs(data, poolModel)
            else:
                print(command, data)
        serialHandler.buffer.clear()
        serialHandler.looking_for_start = True
        serialHandler.buffer_full = False
        ready_to_send = True


def parseDisplay(data, poolModel):
    global salt_level
    global flag_data_changed
    # Classify display update and print classification
    if DISPLAY_AIRTEMP in data:
        data = data.replace(b'\x5f', b'\xc2\xb0')
        parseAirTemp(data, poolModel)
    elif DISPLAY_POOLTEMP in data:
        data = data.replace(b'\x5f', b'\xc2\xb0')
        parsePoolTemp(data, poolModel)
    elif DISPLAY_GASHEATER in data:
        print('gas heater update:', end='')
    elif DISPLAY_CHLORINATOR_PERCENT in data:
        print('chlorinator percent update:', end='')
    elif DISPLAY_CHLORINATOR_STATUS in data:
        print('chlorinator status update:', end='')
    elif DISPLAY_DATE in data:
        parseDateTime(data, poolModel)
    elif DISPLAY_CHECK in data:
        if DISPLAY_VERY_LOW_SALT in data:
            parseSalinity(data, poolModel)
        else:
            print('check system update', end='')
    elif DISPLAY_SALT_LEVEL in data:
        parseSalinity(data, poolModel)
    else:
        print('unclassified display update', end='')

    # Print data
    try:
        poolModel.display = data.decode('utf-8')
        flag_data_changed = True
        print(poolModel.display)
    except UnicodeDecodeError as e:
        try:
            poolModel.display = data.replace(b'\xba', b'\x3a').decode('utf-8')
            flag_data_changed = True
            print(poolModel.display)  #: is encoded as xBA
        except UnicodeDecodeError as e:
            print(e)
            print(data)
    return


def parseDateTime(data, poolModel):
    global flag_data_changed
    previousDateTIme = poolModel.datetime
    newDateTime = data.replace(b'\xba',
                               b'\x3a').decode('utf-8')  #: is encoded as xBA
    if newDateTime != previousDateTIme:
        flag_data_changed = True
        poolModel.datetime = newDateTime
    print('date time update:', end='')
    return


def parseAirTemp(data, poolModel):
    global flag_data_changed
    previousAirTemp = poolModel.airtemp
    newAirTemp = data.decode('utf-8').split()[2]
    if newAirTemp != previousAirTemp:
        flag_data_changed = True
        poolModel.airtemp = newAirTemp
    print('air temp update:', end='')
    return


def parsePoolTemp(data, poolModel):
    global flag_data_changed
    previousPoolTemp = poolModel.pooltemp
    newPoolTemp = data.decode('utf-8').split()[2]
    if newPoolTemp != previousPoolTemp:
        flag_data_changed = True
        poolModel.pooltemp = newPoolTemp
    print('pooltemp update:', end='')
    return


def parseSalinity(data, poolModel):
    global flag_data_changed
    previousSaltLevel = poolModel.salinity
    if DISPLAY_VERY_LOW_SALT in data:
        newSaltLevel = "Very Low Salt"
    else:
        newSaltLevel = data.decode('utf-8').split()[-3]
    if newSaltLevel != previousSaltLevel:
        flag_data_changed = True
        poolModel.salinity = newSaltLevel
    print('salt level update:', end='')
    return


def parseLEDs(data, poolModel):
    global flag_data_changed
    flag_data_changed = True
    print('led update', data)
    #TODO clean this up to reuse code
    #TODO expand to next 4 bytes to determine blinking status
    #Look at corrosponding LED bit flags to determine which LEDs are on
    for i in range(0, 4):
        for item in LED_MASK[i]:
            if item[0] & data[0]:
                print('     ', item[1])
                if item[0] & data[1]:
                    poolModel.updateParameter(item[1], "ON")
                else:
                    poolModel.updateParameter(item[1], "OFF")
    return


def confirmChecksum(message):
    # Check if the calculated checksum for messages equals the expected sent checksum
    # Return True if checksums match, False if not
    # Checksum is 4th and 3rd to last bytes of command (last bytes prior to DLE ETX)
    # Checksum includes DLE STX and command/data
    target_checksum = message[-4] * (16**2) + message[
        -3]  # Convert two byte checksum to single value #TODO change to int.from_bytes
    checksum = 0
    for i in message[:-4]:
        checksum += i
    if checksum == target_checksum:
        return True
    else:
        return False


def getCommand():
    #TODO
    return


def sendCommand():
    return
    global command_queue
    global ready_to_send
    global poolModel
    if (len(command_queue) != 0 and ready_to_send == True):
        # get command from queue and send
        # need flag for indicating command needs to be confirmed
        # need to initialize counters for command confirmation

        #Temporary hard code for testing waterfall. Need to move command matching logic to getCommand
        command = command_queue.pop()
        #Ensure we're not in init phase
        if poolModel.waterfall == "INIT":
            return
        #If we're trying to turn it on and it's already on, do nothing. Same if off.
        if poolModel.waterfall == "ON" and command[1] == 1:
            return
        if poolModel.waterfall == "OFF" and command[1] == 0:
            return
        if command[0] == "AUX4":
            serialHandler.write(AUX4)
        ready_to_send = False


def updateModel():
    return
    global flag_data_changed
    global poolModel
    # socketio.emit('display', {'data': model.display})

    if not flag_data_changed:
        return
    # socketio.emit('salinity', {'data': salt_level})
    flag_data_changed = False
    #TODO
    return


def sendModel(poolModel):
    global flag_data_changed
    if flag_data_changed == False:
        return
    socketio.emit('model', poolModel.toJSON())
    flag_data_changed = False
    return


def main():
    # TODO get states from memory on startup

    poolModel = PoolModel()
    serialHandler = SerialHandler()
    while (True):
        # Read Serial Bus
        # If new serial data is available, read from the buffer
        readSerialBus(serialHandler)

        # Parse Buffer
        # If a full serial message has been found, decode it
        parseBuffer(serialHandler, poolModel)

        # Update pool model
        # If we have new data, update the local model
        updateModel()

        # Update webview
        sendModel(poolModel)

        # Check for new commands
        getCommand()

        # Send to Serial Bus
        # If we have pending commands from the web, send
        sendCommand()


if __name__ == '__main__':
    Thread(
        target=lambda: socketio.run(app, debug=False, host='0.0.0.0')).start()
    Thread(target=main).start()
