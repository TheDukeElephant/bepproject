import time
import serial

from . import socketio

def background_co2_read():
    error_logged = False
    ser = None
    try:
        ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
        time.sleep(1)
        ser.write(b'K 2\r\n')
        time.sleep(0.1)
    except Exception as e:
        print(f"Error initializing serial port: {e}")

    while True:
        if ser is None:
            if not error_logged:
                print("Serial port is unavailable. Emitting placeholder value.")
                error_logged = True
            socketio.sleep(1)  # Replace `time.sleep()` with `socketio.sleep()`
            socketio.emit('update_data', {'co2': '?'}, to='/')
        else:
            try:
                ser.write(b'Z\r\n')
                socketio.sleep(0.1)
                response = ser.read_until().decode('utf-8').strip()
                if response.startswith('Z') and len(response) > 1:
                    co2_value = int(response[1:])
                    socketio.emit('update_data', {'co2': co2_value}, to='/')
                else:
                    socketio.emit('update_data', {'co2': '?'}, to='/')
            except Exception as e:
                print(f"Error reading from serial port: {e}")
                socketio.emit('update_data', {'co2': '?'}, to='/')
            socketio.sleep(1)
