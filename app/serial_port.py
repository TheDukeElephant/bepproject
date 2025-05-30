import serial
import time
import logging

def initialize_serial():
    try:
        ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
        time.sleep(1)
        ser.write(b'K 2\r\n')
        time.sleep(0.1)
        return ser
    except Exception as e:
        logging.error(f"Error initializing serial port: {e}")
        return None
