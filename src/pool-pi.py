from distutils.log import INFO
from commands import *
from threading import Thread
from model import *
from web import *
from parsing import *
from os import makedirs
from os.path import exists
from os import stat
import logging
from logging.handlers import TimedRotatingFileHandler

#TODO start this on pi startup


def readSerialBus(serialHandler):
    '''
    Read data from the serial bus to build full frame in buffer.
    Serial frames begin with DLE STX and terminate with DLE ETX.
    With the exception of searching for the two start bytes, this function only reads one byte to prevent blocking other processes.
    When looking for start of frame, looking_for_start is True.
    When buffer is filled with a full frame and ready to be parseed, set buffer_full to True.
    '''

    if (serialHandler.in_waiting() == 0
        ):  #Check if we have serial data to read
        return
    if (serialHandler.buffer_full == True
        ):  #Check if we already have a full frame in buffer
        return
    serChar = serialHandler.read()
    if serialHandler.looking_for_start:
        # We are looking for DLE STX to find beginning of frame
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
            # Non-DLE character
            # We are only interested in DLE to find potential start
            return
    else:
        # We have already found the start of the frame
        # We are adding to buffer while looking for DLE ETX
        serialHandler.buffer += serChar
        # Check if we have found DLE ETX
        if ((serChar == ETX)
                and (serialHandler.buffer[-2] == int.from_bytes(DLE, 'big'))):
            # We have found a full frame
            serialHandler.buffer_full = True
            serialHandler.looking_for_start = True
            return


def parseBuffer(poolModel, serialHandler, commandHandler):
    '''
    If we have a full frame in buffer, parse it.
    If frame is keep alive, check to see if we are ready to send a command and if so send it.
    '''
    if (serialHandler.buffer_full):
        frame = serialHandler.buffer
        # Remove any extra x00 after x10
        frame = frame.replace(b'\x10\x00', b'\x10')

        # Ensure no erroneous start/stop within frame
        if b'\x10\x02' in frame[2:-2]:
            logging.error(f'DLE STX in frame: {frame}')
            serialHandler.reset()
            return
        if b'\x10\x03' in frame[2:-2]:
            logging.error(f'DLE ETX in frame: {frame}')
            serialHandler.reset()
            return

        # Compare calculated checksum to frame checksum
        if (confirmChecksum(frame) == False):
            # If checksum doesn't match, message is invalid.
            # Clear buffer and don't attempt parsing.
            serialHandler.reset()
            return

        frameType = frame[2:4]
        data = frame[4:-4]

        # Use frame type to determine parsing function
        if frameType == FRAME_TYPE_KEEPALIVE:
            # Check to see if we have a command to send
            if serialHandler.ready_to_send == True:
                if commandHandler.keep_alive_count == 1:
                    # If this is the second sequential keep alive frame, send command
                    serialHandler.send(commandHandler.full_command)
                    logging.info(
                        f'Sent: {commandHandler.parameter}, {commandHandler.full_command}'
                    )
                    if commandHandler.confirm == False:
                        commandHandler.sending_message = False
                    serialHandler.ready_to_send = False
                else:
                    commandHandler.keep_alive_count = 1
            else:
                commandHandler.keep_alive_count = 0
        else:
            # Message is not keep alive
            commandHandler.keep_alive_count = 0
            if frameType == FRAME_TYPE_DISPLAY:
                parseDisplay(data, poolModel)
                commandHandler.keep_alive_count = 0
            elif frameType == FRAME_TYPE_LEDS:
                parseLEDs(data, poolModel)
            else:
                logging.info(f'Unkown update: {frameType}, {data}')
        # Clear buffer and reset flags
        serialHandler.reset()


def checkCommand(poolModel, serialHandler, commandHandler):
    '''
    If we are trying to send a message, wait for a new pool model to get pool states
    If necessary, queue message to be sent after second keep alive
    Are we currently trying to send a command?
    '''
    if commandHandler.sending_message == False:
        # We aren't trying to send a command
        return

    if serialHandler.ready_to_send == True:
        # We are already ready to send, awaiting keep alive
        return

    if poolModel.last_update_time >= commandHandler.last_model_time:
        # We have a new poolModel
        if poolModel.getParameterState(
                commandHandler.parameter) == commandHandler.target_state:
            # Model matches
            logging.info(f'Command success.')
            commandHandler.sending_message = False
            poolModel.sending_message = False
            poolModel.flag_data_changed = True
        else:
            # New poolModel doesn't match
            if commandHandler.checkSendAttempts() == True:
                commandHandler.last_model_time = time.time()
                serialHandler.ready_to_send = True


def getCommand(poolModel, serialHandler, commandHandler):
    '''
    If we're not currently sending a command, check if there are new commands.
    Get new command from command_queue, validate, and initiate send with commandHandler.
    '''
    #TODO figure out threading issue or move command_queue to tmp directory
    if commandHandler.sending_message == True:
        #We are currently trying to send a command, don't need to check for others
        return
    if exists('command_queue.txt') == False:
        return
    if stat('command_queue.txt').st_size != 0:
        f = open('command_queue.txt', 'r+')
        line = f.readline()
        # TODO check if this if statement is necessary or if it's redundant with st_size check
        try:
            if len(line.split(',')) == 4:
                # Extract csv command info
                commandID = line.split(',')[0]
                commandDesiredState = line.split(',')[1]
                commandVersion = int(line.split(',')[2])
                commandConfirm = line.split(',')[3]

                if commandConfirm == '1':
                    # Command is not a menu button.
                    # Confirmation if command was successful is needed
                    # Check against model to see if command state and version are valid
                    # If valid, add to send queue
                    # If not, provide feedback to user
                    if poolModel.getParameterState(commandID) == 'INIT':
                        logging.error(
                            f'Invalid command: Target parameter {commandID} is in INIT state.'
                        )
                        f.close()
                        return
                    else:
                        if commandVersion == poolModel.getParameterVersion(
                                commandID):
                            #Front end and back end versions are synced
                            #Extra check to ensure we are not already in our desired state
                            if commandDesiredState == poolModel.getParameterState(
                                    commandID):
                                logging.error(
                                    f'Invalid command: Target parameter {commandID} is already in target state {commandDesiredState}.'
                                )
                            else:
                                # Command is valid
                                logging.info(
                                    f'Valid command: {commandID} {commandDesiredState}, version {commandVersion}'
                                )
                                #Push to command handler
                                commandHandler.initiateSend(
                                    commandID, commandDesiredState,
                                    commandConfirm)
                                poolModel.sending_message = True

                        else:
                            logging.error(
                                f'Invalid command: Target parameter {commandID} version is {poolModel.getParameterVersion(commandID)} but command version is {commandVersion}.'
                            )
                else:
                    # Command is a menu button
                    # No confirmation needed. Only send once.
                    # No check against model states/versions needed.
                    # Immediately load for sending.
                    commandHandler.initiateSend(commandID, commandDesiredState,
                                                commandConfirm)
                    serialHandler.ready_to_send = True
            else:
                logging.error(
                    f'Invalid command: Command structure is invalid: {line}')
        except Exception as e:
            logging.error(
                f'Invalid command: Error parsing command: {line}, {e}')
        # Clear file contents
        f.truncate(0)
        f.close()
    return


def sendModel(poolModel):
    # If we have new date for the front end, send data as JSON
    if poolModel.flag_data_changed == True:
        socketio.emit('model', poolModel.toJSON())
        logging.debug('Sent model')
        poolModel.flag_data_changed = False
    return


def main():
    poolModel = PoolModel()
    serialHandler = SerialHandler()
    commandHandler = CommandHandler()
    if exists('command_queue.txt') == True:
        if stat('command_queue.txt').st_size != 0:
            f = open('command_queue.txt', 'r+')
            f.truncate(0)
            f.close()
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
    # Create log file directory if not already existing
    if not exists('logs'):
        makedirs('logs')
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = TimedRotatingFileHandler('logs/pool-pi.log',
                                       when='midnight',
                                       interval=5)
    handler.suffix = '%Y-%m-%d_%H-%M-%S'
    handler.setFormatter(formatter)
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    logging.info('Started pool-pi.py')
    Thread(
        target=lambda: socketio.run(app, debug=False, host='0.0.0.0')).start()
    Thread(target=main).start()
