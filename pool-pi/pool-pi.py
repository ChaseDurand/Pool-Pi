from posixpath import split
from commands import *
from threading import Thread
from model import *
from web import *
from parsing import *
from os.path import exists
from os import stat

# command_queue = []
sending_attempts = 0
confirm_attempts = 0
MAX_SEND_ATTEMPTS = 5  # Max number of times command will be sent if not confirmed
MAX_CONFIRM_ATTEMPTS = 20  # Max number of inbound message parsed to look for confirmation before resending command


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
        if ((serChar == ETX) and (serialHandler.buffer[-2] == int.from_bytes(
                DLE,
                "big"))):  #TODO refresh this- looks like im converting twice?
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
    if (serialHandler.buffer_full):
        # Confirm checksum
        if (confirmChecksum(serialHandler.buffer) == False):
            print("Checksum mismatch! ", serialHandler.buffer)
            #If checksum doesn't match, message is invalid.
            #Clear buffer and don't attempt parsing.
            serialHandler.buffer.clear()
            serialHandler.looking_for_start = True
            serialHandler.buffer_full = False
            return

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
        serialHandler.ready_to_send = True


def getCommand(poolModel, serialHandler):
    # global command_queue
    #TODO
    #Get command from queue
    # Threading workaround
    if exists("command_queue.txt") == False:
        return
    # command_queue = pickle.load(open('command_queue.dump', 'rb'))
    if stat('command_queue.txt').st_size != 0:
        f = open('command_queue.txt', 'r+')
        for line in f.readlines():
            if line is not '':
                print(line)
                commandID = line.split(',')[0]
                commandState = line.split(',')[1]
                commandVersion = line.split(',')[2]
                #Check if command is valid
                #If valid, add to send queue
                #If not, provide feedback to user
                if commandVersion == poolModel.getParameterVersion(commandID):
                    #Front end and back end are synced; command is valid
                    print('valid command', commandID, commandState,
                          commandVersion)
                else:
                    print('invalid command!')
        f.truncate(0)
        f.close()
    return


def sendCommand(serialHandler):
    #TODO
    #If we have a command in send queue, send it
    return
    global command_queue
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


def sendModel(poolModel):
    if poolModel.flag_data_changed == True:
        print("Sent model!")
        socketio.emit('model', poolModel.toJSON())
        poolModel.flag_data_changed = False
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
        # If a full serial message has been found, decode it and update model
        parseBuffer(serialHandler, poolModel)

        # Update webview
        sendModel(poolModel)

        # Check for new commands
        getCommand(poolModel, serialHandler)

        # Send to Serial Bus
        # If we have pending commands from the web, send
        sendCommand(serialHandler)


if __name__ == '__main__':
    # thread_web = Thread(
    #     target=lambda: socketio.run(app, debug=False, host='0.0.0.0'))
    # thread_local = Thread(target=main)
    # thread_web.start()
    # thread_local.start()
    # thread_web.join()
    # thread_local.join()
    Thread(
        target=lambda: socketio.run(app, debug=False, host='0.0.0.0')).start()
    Thread(target=main).start()