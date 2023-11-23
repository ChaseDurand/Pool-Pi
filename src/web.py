from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from threading import Lock
import uuid
import logging
import eventlet
import redis

eventlet.monkey_patch()
async_mode = "eventlet"
app = Flask(__name__)
app.config["SECRET_KEY"] = uuid.uuid4().hex
socketio = SocketIO(app, async_mode=async_mode)

r = redis.Redis(charset="utf-8", decode_responses=True)


@socketio.event
def connect():
    logging.info(f"Client connected.")


@app.route("/")
def index():
    return render_template("index.html", async_mode=socketio.async_mode)


@app.route("/simple")
def simple():
    return render_template("simple.html", async_mode=socketio.async_mode)


@socketio.event
def webCommand(message):
    """
    Publish command from front end to redis channel.
    """
    r.publish("inbox", message)


def checkOutbox():
    logging.info(f"Starting checkOutbox")
    """
    Subscribe to redis channel for messages to relay to front end.
    Used for sending pool model showing current state of the pool.
    """
    pubsub = r.pubsub()
    pubsub.subscribe("outbox")
    while True:
        message = pubsub.get_message()
        if message and (message["type"] == "message"):
            print(message["data"])
            socketio.emit("model", message)
        socketio.sleep(0.01)


def webBackendMain():
    logging.info(f"Starting web backend.")
    socketio.start_background_task(checkOutbox)
    socketio.run(app, host="0.0.0.0")
