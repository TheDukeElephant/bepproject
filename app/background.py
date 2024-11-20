import time
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio

def background_co2_read():
    ser = initialize_serial()
    while True:
        try:
            ser.write(b'Z\r\n')
            socketio.sleep(0.1)  # Use socketio.sleep() instead of time.sleep()
            response = ser.read_until().decode('utf-8').strip()
            if response.startswith('Z') and len(response) > 1:
                co2_value = int(response[1:])
                socketio.emit('update_data', {'co2': co2_value}, broadcast=True)
            else:
                socketio.emit('update_data', {'co2': '?'}, broadcast=True)
        except Exception as e:
            print(f"Error reading from serial port: {e}")
            socketio.emit('update_data', {'co2': '?'}, broadcast=True)
        socketio.sleep(1)
