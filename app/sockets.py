from flask_socketio import emit, disconnect
from flask_login import current_user
from . import socketio

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        disconnect()
    else:
        print(f"Client {current_user.id} connected.")
