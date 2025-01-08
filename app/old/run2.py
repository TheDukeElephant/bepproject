import serial
import time

# Initialize the serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
time.sleep(1)

# Optional: Send initialization command only once
ser.write(b'K 2\r\n')
time.sleep(0.5)  # Allow time for the sensor to initialize

while True:
    try:
        # Send the test command to get CO₂ data
        ser.write(b'Z 2\r\n')  # Command to the CO₂ sensor
        time.sleep(0.1)  # Wait for the sensor to respond (increased from 0.01)

        # Read the response from the sensor
        response = ""
        start_time = time.time()
        while time.time() - start_time < 1:  # Read for up to 1 second
            if ser.in_waiting > 0:
                response += ser.read(ser.in_waiting).decode("utf-8")

        response = response.strip()  # Clean up the response

        if response:
            print(f"Response from CO₂ sensor: {response}")
        else:
            print("No response received from CO₂ sensor")

    except Exception as e:
        print(f"Error communicating with CO₂ sensor: {e}")

    time.sleep(1)  # Wait 1 second before the next command
