from flask_socketio import disconnect
from flask_login import current_user
from . import socketio
import logging

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        logging.warning("Unauthenticated user attempted to connect.")
        disconnect()
    else:
        logging.info(f"Client {current_user.id} connected.")
