from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from threading import Lock
import uuid
import logging

async_mode = None
app = Flask(__name__)
app.config["SECRET_KEY"] = uuid.uuid4().hex
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


@app.route("/")
def index():
    return render_template("index.html", async_mode=socketio.async_mode)


@app.route("/simple")
def simple():
    return render_template("simple.html", async_mode=socketio.async_mode)


@socketio.event
def command_event(message):
    """
    Receive command from front end.
    """
    # TODO don't use file to get command to non-web thread.
    f = open("command_queue.txt", "a")
    command = str(message["id"] + "," + str(message["modelVersion"]))
    logging.info(f"Recevied command from user: {message}")
    f.write(command)
    f.close()


@socketio.event
def connect():
    global thread
    logging.info(f"Client connected.")
