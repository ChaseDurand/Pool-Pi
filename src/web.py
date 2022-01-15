from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from threading import Lock
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

#TODO implement heartbeat/connection functionality for front end
#def background_thread():
#    """Example of how to send server generated events to clients."""
#    count = 0
#    while True:
#        socketio.sleep(10)
#        count += 1
#        socketio.emit('my_response', {
#            'data': 'Server generated event',
#            'count': count
#        })


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@app.route('/simple')
def simple():
    return render_template('simple.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {
        'data': message['data'],
        'count': session['receive_count']
    })


@socketio.event
def command_event(message):
    f = open('command_queue.txt', 'a')
    command = str(message['id'] + ',' + str(message['data']) + ',' +
                  message['version'] + ',' + message['confirm'])
    print(command)
    f.write(command)
    f.close()
    emit('my_response', {
        'data': message['data'],
        'count': message['id']
    },
         broadcast=True)


@socketio.event
def connect():
    global thread
    #    with thread_lock:
    #        if thread is None:
    #            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)
