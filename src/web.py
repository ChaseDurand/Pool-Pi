from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from threading import Lock
import uuid
import logging

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = uuid.uuid4().hex
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


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
    logging.info(f'Recevied command from user: {message}')
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
    emit('my_response', {'data': 'Connected', 'count': 0})
    logging.info(f'Client connected.')