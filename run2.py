import serial
import time
while True:
    try:
        # Open the serial port
        ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
        time.sleep(1)

        # Send initialization command
        ser.write(b'K 2\r\n')
        time.sleep(0.5)

        # Send test command to get CO2 data
        ser.write(b'Z 2\r\n')
        time.sleep(0.1)
        response = ser.read(100).decode('utf-8').strip()

        print(f"Response from CO₂ sensor: {response}")
    except Exception as e:
        print(f"Error communicating with CO₂ sensor: {e}")
    time.sleep(1)