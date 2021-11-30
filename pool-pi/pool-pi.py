import serial
from gpiozero import LED
from commands import *
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from threading import Lock
from threading import Thread

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        # socketio.emit('my_response', {
        #     'data': 'Server generated event',
        #     'count': salt_level
        # })
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
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit(
        'my_response', {
            'data': 'In rooms: ' + ', '.join(rooms()),
            'count': session['receive_count']
        })


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit(
        'my_response', {
            'data': 'In rooms: ' + ', '.join(rooms()),
            'count': session['receive_count']
        })


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {
        'data': 'Room ' + message['room'] + ' is closing.',
        'count': session['receive_count']
    },
         to=message['room'])
    close_room(message['room'])


@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {
        'data': message['data'],
        'count': session['receive_count']
    },
         to=message['room'])


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response', {
        'data': 'Disconnected!',
        'count': session['receive_count']
    },
         callback=can_disconnect)


@socketio.event
def my_ping():
    emit('my_pong')


# @socketio.event
# def salinity():
#     emit('salinity')


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


# async_mode = None
# app = Flask(__name__)
# socket_ = SocketIO(app, async_mode=async_mode)

# @app.route("/")
# def index():
#     now = datetime.datetime.now()
#     timeString = now.strftime("%Y-%m-%d %H:%M")
#     templateData = {'title': 'Hello!', 'time': timeString}
#     return render_template('index.html',
#                            **templateData,
#                            sync_mode=socket_.async_mode)

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
    if DISPLAY_AIRTEMP in data:
        print('air temp update:', end='')
        data = data.replace(b'\x5f', b'\xc2\xb0')
    elif DISPLAY_POOLTEMP in data:
        print('pooltemp update:', end='')
        data = data.replace(b'\x5f', b'\xc2\xb0')
    elif DISPLAY_GASHEATER in data:
        print('gas heater update:', end='')
    elif DISPLAY_CHLORINATOR_PERCENT in data:
        print('chlorinator percent update:', end='')
    elif DISPLAY_CHLORINATOR_STATUS in data:
        print('chlorinator status update:', end='')
    elif DISPLAY_DATE in data:
        print('date update:', end='')
    elif DISPLAY_CHECK in data:
        print('check system update', end='')
    elif DISPLAY_SALT_LEVEL in data:
        #parse salt level and store
        previous_salt_level = salt_level
        salt_level = data.decode('utf-8').split()[-3]
        if salt_level != previous_salt_level:
            flag_data_changed = True
        print('salt level update:', end='')
        print(salt_level, 'PPM')
    else:
        print('unclassified display update', end='')
    try:
        print(data.decode('utf-8'))
    except UnicodeDecodeError as e:
        try:
            print(data.replace(b'\xba',
                               b'\x3a').decode('utf-8'))  #: is encoded as xBA
        except UnicodeDecodeError as e:
            print(e)
            print(data)
    return


def parseLEDs(data):
    print('led update', data)
    #TODO clean this up to reuse code
    #TODO expand to next 4 bytes to determine blinking status
    #Look at corrosponding LED bit flags to determine which LEDs are on
    for item in LED_1:
        if item[0] & data[0]:
            print('     ', item[1])
    for item in LED_2:
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
    global flag_data_changed
    if not flag_data_changed:
        return
    socketio.emit('salinity', {'data': salt_level})
    flag_data_changed = False
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
    Thread(
        target=lambda: socketio.run(app, debug=False, host='0.0.0.0')).start()
    Thread(target=main).start()
