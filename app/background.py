import serial
import time
from . import socketio

# CO₂ sensor setup
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
time.sleep(1)
ser.write(b'K 2\r\n')
time.sleep(0.1)

def background_co2_read():
    while True:
        try:
            ser.write(b'Z\r\n')
            time.sleep(0.1)
            response = ser.read_until().decode('utf-8').strip()
            if response.startswith('Z'):
                co2_value = int(response[1:])
                socketio.emit('update_data', {'co2': co2_value}, broadcast=True)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
