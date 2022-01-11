from commands import *
from threading import Thread
from model import *
from web import *
from parsing import *
from os.path import exists
from os import stat
import time
from colorama import Fore, Style
import logging

#TODO start this on pi startup

#TODO proper logging/text output
# possibly with binascii hexlify to avoid ascii conversions for non-screen updates


def readSerialBus(serialHandler):
    '''
    Read data from the serial bus to build full frame in buffer.
    Serial frames begin with DLE STX and terminate with DLE ETX.
    With the exception of searching for the two start bytes, this function only reads one byte to prevent blocking other processes.
    When looking for start of frame, looking_for_start is True.
    When buffer is filled with a full frame and ready to be parseed, set buffer_full to True.
    '''

    if (serialHandler.in_waiting() == 0
        ):  #Check is we have serial data to read
        return
    if (serialHandler.buffer_full == True
        ):  #Check if we already have a full buffer
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


def parseBuffer(poolModel, serialHandler, commandHandler):
    # If we have a full frame in buffer, parse it.
    # If frame is keep alive, check to see if we are ready to send a command and if so send it.
    '''
    Frame structure:
    | Start  | Frame Type |     Data     | Checksum  |  End   |
    | x10x02 | <2 bytes>  | <0-? bytes>  | <2 bytes> | x10x03 |

    The Start, Frame Type, and Data fields are added together to provide the 2-byte Checksum. If 
    any of the bytes of the Frame Type, Data fields, or Checksum are equal to the DLE character (x10), a 
    NULL character (x00) is inserted into the transmitted data stream immediately after that byte. That 
    NULL character must be removed by the receiver.
    '''
    if (serialHandler.buffer_full):
        # Confirm checksum
        frame = serialHandler.buffer
        #Replace any x00 after x10
        frame = frame.replace(b'\x10\x00', b'\x10')
        if (confirmChecksum(frame) == False):
            #If checksum doesn't match, message is invalid.
            #Clear buffer and don't attempt parsing.
            print(f'{Fore.RED}Checksum mismatch! {Style.RESET_ALL}', frame)
            serialHandler.buffer.clear()
            serialHandler.looking_for_start = True
            serialHandler.buffer_full = False
            serialHandler.clear_input()
            return
        if b'\x10\x02' in frame[2:-2]:
            print(f'{Fore.RED}DLE STX in frame! {Style.RESET_ALL}', frame)
            serialHandler.buffer.clear()
            serialHandler.looking_for_start = True
            serialHandler.buffer_full = False
            serialHandler.clear_input()
            return
        if b'\x10\x03' in frame[2:-2]:
            print(f'{Fore.RED}DLE ETX in frame! {Style.RESET_ALL}', frame)
            serialHandler.buffer.clear()
            serialHandler.looking_for_start = True
            serialHandler.buffer_full = False
            serialHandler.clear_input()
            return

        frameType = frame[2:4]
        data = frame[4:-4]

        # Use frame type to determine parsing function
        if frameType == FRAME_TYPE_KEEPALIVE:
            # Message is keep alive
            # Check to see if we have a command to send
            if serialHandler.ready_to_send == True:
                if commandHandler.keepAliveCount == 1:
                    # If this is the second sequential keep alive frame, send command
                    serialHandler.send(commandHandler.fullCommand)
                    if commandHandler.confirm == False:
                        commandHandler.sendingMessage = False
                    serialHandler.ready_to_send = False
                else:
                    commandHandler.keepAliveCount = 1
            else:
                commandHandler.keepAliveCount = 0
        else:
            # Message is not keep alive
            commandHandler.keepAliveCount = 0
            if frameType == FRAME_TYPE_DISPLAY:
                parseDisplay(data, poolModel)
                commandHandler.keepAliveCount = 0
            elif frameType == FRAME_TYPE_LEDS:
                parseLEDs(data, poolModel)
            else:
                print(frameType, data)
        # Clear buffer and reset flags
        serialHandler.buffer.clear()
        serialHandler.looking_for_start = True
        serialHandler.buffer_full = False


def checkCommand(poolModel, serialHandler, commandHandler):
    # If we are trying to send a message, check most recent pool model
    # If necessary, queue message attempt
    # Are we currently trying to send a command?
    if commandHandler.sendingMessage == False:
        #We aren't trying to send a command
        return

    if serialHandler.ready_to_send == True:
        #We are ready to send, awaiting keep alive
        return

    if poolModel.last_update_time >= commandHandler.lastModelTime:
        #We have a new poolModel
        if poolModel.getParameterState(
                commandHandler.parameter) == commandHandler.targetState:
            #Model matches
            print(f'{Fore.GREEN}Command success!{Style.RESET_ALL}')
            commandHandler.sendingMessage = False
        else:
            #New poolModel doesn't match
            if commandHandler.checkSendAttempts() == True:
                commandHandler.lastModelTime = time.time()
                serialHandler.ready_to_send = True


def getCommand(poolModel, serialHandler, commandHandler):
    # If we're not currently sending a command, check if there are new commands.
    # Get new command from command_queue, validate, and initiate send with commandHandler.
    #TODO figure out threading issue or move command_queue to tmp directory
    #TODO add handling for buttons and arrows
    #TODO add handling for unlock code
    if commandHandler.sendingMessage == True:
        #We are currently trying to send a command, don't need to check for others
        return
    if exists("command_queue.txt") == False:
        return
    if stat('command_queue.txt').st_size != 0:
        f = open('command_queue.txt', 'r+')
        line = f.readline()
        # TODO check if this if statement is necessary or if it's redundant with st_size check
        if line is not '':
            # Extract csv command info
            commandID = line.split(',')[0]
            commandState = line.split(',')[1]
            commandVersion = int(line.split(',')[2])
            commandConfirm = line.split(',')[3]

            if commandConfirm == '1':
                # Not a menu button. We need to confirm the command was successful
                #Check if command is valid
                #If valid, add to send queue
                #If not, provide feedback to user
                if poolModel.getParameterState(commandID) == "INIT":
                    print('Invalid command! Target command is in init state')
                    f.close()
                    return
                else:
                    if commandVersion == poolModel.getParameterVersion(
                            commandID):
                        #Front end and back end versions are synced
                        #Extra check to ensure we are not already in our desired state
                        if commandState == poolModel.getParameterState(
                                commandID):
                            print('Invalid command! State mismatch',
                                  poolModel.getParameterState(commandID),
                                  commandState)
                        else:
                            # Command is valid
                            print('Valid command', commandID, commandState,
                                  commandVersion)
                            #Push to command handler
                            commandHandler.initiateSend(
                                commandID, commandState, commandConfirm)

                    else:
                        print('Invalid command! Version mismatch',
                              poolModel.getParameterVersion(commandID),
                              commandVersion)
            else:
                # Menu button. Do not need to confirm command.
                # Immediately load for sending.
                commandHandler.initiateSend(commandID, commandState,
                                            commandConfirm)
                serialHandler.ready_to_send = True
        f.truncate(0)
        f.close()
    return


def sendModel(poolModel):
    # If we have new date for the front end, send data as JSON
    if poolModel.flag_data_changed == True:
        print("Sent model!")
        socketio.emit('model', poolModel.toJSON())
        poolModel.flag_data_changed = False
    return


def main():
    poolModel = PoolModel()
    serialHandler = SerialHandler()
    commandHandler = CommandHandler()
    logger = logging.getLogger("poolpi-logger")
    while (True):
        # Read Serial Bus
        # If new serial data is available, read from the buffer
        readSerialBus(serialHandler)

        # Parse Buffer
        # If a full serial frame has been found, decode it and update model.
        # If we have a command ready to be sent, send.
        parseBuffer(poolModel, serialHandler, commandHandler)

        # If we are sending a command, check if command needs to be sent.
        # Check model for updates to see if command was accepted.
        checkCommand(poolModel, serialHandler, commandHandler)

        # Send updates to front end.
        sendModel(poolModel)

        # If we're not sending, check for new commands from front end.
        getCommand(poolModel, serialHandler, commandHandler)


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
