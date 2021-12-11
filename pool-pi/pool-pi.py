import serial
from gpiozero import LED
from commands import *
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from threading import Lock
from threading import Thread
import uuid

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = uuid.uuid4().hex
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response', {
            'data': 'Server generated event',
            'count': count
        })


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {
        'data': message['data'],
        'count': session['receive_count']
    })


@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {
        'data': message['data'],
        'count': session['receive_count']
    },
         broadcast=True)


@socketio.event
def my_toggle_event(message):
    emit('my_response', {
        'data': message['data'],
        'count': 'received!!!'
    },
         broadcast=True)


@socketio.event
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)


buffer = bytearray()
buffer_full = False
command_queue = []
ready_to_send = False
send_enable = LED(17)
send_enable.off()
sending_attempts = 0
confirm_attempts = 0
looking_for_start = True
MAX_SEND_ATTEMPTS = 5  # Max number of times command will be sent if not confirmed
MAX_CONFIRM_ATTEMPTS = 20  # Max number of inbound message parsed to look for confirmation before resending command
previous_message = NON_KEEP_ALIVE

salt_level = 0  #test salt level variable for web proof of concept
flag_data_changed = False  #True if there is new data for site, false if no new data

poolModel = {
    "display": "WAITING FOR DISPLAY",
    "airtemp": "WAITING FOR AIRTEMP",
    "pooltemp": "WAITING FOR POOLTEMP",
    "datetime": "WAITING FOR DATETIME",
    "salinity": "WAITING FOR SALINITY",
    "waterfall": "INIT"
}

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
            #TODO identify and account for possible x00 after x10 (DLE)
            while (True):
                try:
                    index_to_remove = buffer.index(DLE, 2, -2) + 1
                    removed = buffer.pop(index_to_remove)
                    #TODO fix unknown bug here
                    if removed != b'\x00':
                        print('Error, expected 00 but removed', removed)
                except ValueError:
                    break
            command = buffer[2:4]
            data = buffer[4:-4]
            previous_message = NON_KEEP_ALIVE
            if command == FRAME_UPDATE_DISPLAY[0]:
                parseDisplay(data)
            elif command == FRAME_UPDATE_LEDS[0]:
                parseLEDs(data)
            else:
                print(command, data)
        buffer.clear()
        looking_for_start = True
        buffer_full = False
        ready_to_send = True


def parseDisplay(data):
    global salt_level
    global flag_data_changed
    global poolModel
    # Classify display update and print classification
    if DISPLAY_AIRTEMP in data:
        data = data.replace(b'\x5f', b'\xc2\xb0')
        parseAirTemp(data)
    elif DISPLAY_POOLTEMP in data:
        data = data.replace(b'\x5f', b'\xc2\xb0')
        parsePoolTemp(data)
    elif DISPLAY_GASHEATER in data:
        print('gas heater update:', end='')
    elif DISPLAY_CHLORINATOR_PERCENT in data:
        print('chlorinator percent update:', end='')
    elif DISPLAY_CHLORINATOR_STATUS in data:
        print('chlorinator status update:', end='')
    elif DISPLAY_DATE in data:
        parseDateTime(data)
    elif DISPLAY_CHECK in data:
        if DISPLAY_VERY_LOW_SALT in data:
            parseSalinity(data)
        else:
            print('check system update', end='')
    elif DISPLAY_SALT_LEVEL in data:
        parseSalinity(data)
    else:
        print('unclassified display update', end='')

    # Print data
    try:
        poolModel["display"] = data.decode('utf-8')
        flag_data_changed = True
        print(poolModel["display"])
    except UnicodeDecodeError as e:
        try:
            poolModel["display"] = data.replace(b'\xba',
                                                b'\x3a').decode('utf-8')
            flag_data_changed = True
            print(poolModel["display"])  #: is encoded as xBA
        except UnicodeDecodeError as e:
            print(e)
            print(data)
    return


def parseDateTime(data):
    global poolModel
    global flag_data_changed
    previousDateTIme = poolModel['datetime']
    newDateTime = data.replace(b'\xba',
                               b'\x3a').decode('utf-8')  #: is encoded as xBA
    if newDateTime != previousDateTIme:
        flag_data_changed = True
        poolModel['datetime'] = newDateTime
    print('date time update:', end='')
    return


def parseAirTemp(data):
    global poolModel
    global flag_data_changed
    previousAirTemp = poolModel['airtemp']
    newAirTemp = data.decode('utf-8').split()[2]
    if newAirTemp != previousAirTemp:
        flag_data_changed = True
        poolModel['airtemp'] = newAirTemp
    print('air temp update:', end='')
    return


def parsePoolTemp(data):
    global poolModel
    global flag_data_changed
    previousPoolTemp = poolModel['pooltemp']
    newPoolTemp = data.decode('utf-8').split()[2]
    if newPoolTemp != previousPoolTemp:
        flag_data_changed = True
        poolModel['pooltemp'] = newPoolTemp
    print('pooltemp update:', end='')
    return


def parseSalinity(data):
    global poolModel
    global flag_data_changed
    previousSaltLevel = poolModel['salinity']
    if DISPLAY_VERY_LOW_SALT in data:
        newSaltLevel = "Very Low Salt"
    else:
        newSaltLevel = data.decode('utf-8').split()[-3]
    if newSaltLevel != previousSaltLevel:
        flag_data_changed = True
        poolModel['salinity'] = newSaltLevel
    print('salt level update:', end='')
    return


def parseLEDs(data):
    global poolModel
    global flag_data_changed
    flag_data_changed = True
    print('led update', data)
    #TODO clean this up to reuse code
    #TODO expand to next 4 bytes to determine blinking status
    #Look at corrosponding LED bit flags to determine which LEDs are on
    for item in LED_1:
        if item[0] & data[0]:
            print('     ', item[1])
    for item in LED_2:
        if item[1] == 'AUX 4':
            if item[0] & data[1]:
                poolModel['waterfall'] = 'ON'
            else:
                poolModel['waterfall'] = 'OFF'
        if item[0] & data[1]:
            print('     ', item[1])
    for item in LED_3:
        if item[0] & data[2]:
            print('     ', item[1])
    for item in LED_4:
        if item[0] & data[3]:
            print('     ', item[1])
    return


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


def sendModel():
    global flag_data_changed
    global poolModel
    if flag_data_changed == False:
        return
    # print(poolModel)
    # print(json.dump(poolModel))
    socketio.emit('model', poolModel)
    flag_data_changed = False
    return


def main():
    # TODO get states from memory on startup
    while (True):
        # Read Serial Bus
        # If new serial data is available, read from the buffer
        readSerialBus()

        # Parse Buffer
        # If a full serial message has been found, decode it
        parseBuffer()

        # Update pool model
        # If we have new data, update the local model
        updateModel()

        # Update webview
        sendModel()

        # Check for new commands
        getCommand()

        # Send to Serial Bus
        # If we have pending commands from the web, send
        sendCommand()


if __name__ == '__main__':
    Thread(
        target=lambda: socketio.run(app, debug=False, host='0.0.0.0')).start()
    Thread(target=main).start()
