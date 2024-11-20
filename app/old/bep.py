import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_us>
from flask_socketio import SocketIO, emit, disconnect
import serial
import time

# Initialize Flask app, Login Manager, and SocketIO
app = Flask(__name__)
app.secret_key = 'super_secret_key'
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirects to login page if not authenticated
socketio = SocketIO(app)

# User class for authentication
class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    if user_id == "pi":
        user = User()
        user.id = 'pi'
        return user
    return None

# Route enforcement: Redirect all unauthenticated requests to the login page
@app.before_request
def ensure_authenticated():
    # Redirect to login page if not authenticated and accessing protected routes
    if not current_user.is_authenticated and request.endpoint not in ['login', 'static']:
        return redirect(url_for('login'))

# CO ^b^b sensor setup
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
time.sleep(1)
ser.write(b'K 2\r\n')
time.sleep(0.1)

# Background task to read CO ^b^b data and broadcast to authenticated users
def background_co2_read():
    while True:
        try:
            ser.write(b'Z\r\n')
            time.sleep(0.1)
            co2_response = ""
            while ser.in_waiting > 0:
                co2_response += ser.read().decode("utf-8")
            co2_response = co2_response.strip()
            if co2_response.startswith("Z") and len(co2_response) > 1:
                co2_value = int(co2_response[1:].strip())
                print(f"CO ^b^b Concentration: {co2_value} ppm")
                socketio.emit('update_data', {'co2': co2_value}, broadcast=True)
            else:
                print(f"Unexpected response from sensor: {co2_response}")
        except Exception as e:
            print(f"Error reading CO ^b^b sensor: {e}")
        time.sleep(1)

# Ensure only one background task reads the sensor
socketio.start_background_task(target=background_co2_read)

# WebSocket connection management
@socketio.on('connect')
def handle_connect():
    # Check if the user is authenticated
    if not current_user.is_authenticated:
        print("Unauthenticated user attempted WebSocket connection.")
        disconnect()  # Disconnect unauthenticated clients
