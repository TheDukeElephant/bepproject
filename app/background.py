import serial
import time
import platform
from . import socketio

# Determine the appropriate serial port
if platform.system() == "Windows":
    SERIAL_PORT = "COM1"  # Replace with the actual COM port if you have a serial device connected
else:
    SERIAL_PORT = "/dev/serial0"

try:
    ser = serial.Serial(SERIAL_PORT, baudrate=9600, timeout=1)
    time.sleep(1)
    ser.write(b'K 2\r\n')
    time.sleep(0.1)
except serial.SerialException as e:
    ser = None
    print(f"Error initializing serial port: {e}")

def background_co2_read():
    while True:
        if ser is None:
            print("Serial port is unavailable. Emitting placeholder value.")
            socketio.emit('update_data', {'co2': '?'}, to='/')
        else:
            try:
                ser.write(b'Z\r\n')
                time.sleep(0.1)
                response = ser.read_until().decode('utf-8').strip()
                if response.startswith('Z') and len(response) > 1:
                    co2_value = int(response[1:])
                    socketio.emit('update_data', {'co2': co2_value}, to='/')
                else:
                    socketio.emit('update_data', {'co2': '?'}, to='/')
            except Exception as e:
                print(f"Error reading from serial port: {e}")
                socketio.emit('update_data', {'co2': '?'}, to='/')
        time.sleep(1)

