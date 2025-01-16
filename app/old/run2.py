import serial
import time

# Initialize the serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
time.sleep(2)  # Allow sensor to stabilize

def send_command(command):
    """
    Sends a command to the sensor and reads the response.
    """
    try:
        ser.write(command.encode('utf-8') + b'\r\n')
        time.sleep(0.1)  # Allow time for sensor to respond
        response = ser.read_until(b'\n').decode('utf-8').strip()
        return response
    except Exception as e:
        print(f"Error sending command {command}: {e}")
        return None

# Switch to Command Mode (K 0)
print("Setting sensor to Command Mode...")
response = send_command("K 0")
if response == "K 0":
    print("Sensor is now in Command Mode.")
    # Switch to Polling Mode (K 2)
    print("Switching to Polling Mode...")
    response = send_command("K 2")
    if response == "K 2":
        print("Sensor is now in Polling Mode.")
    else:
        print(f"Failed to set Polling Mode. Response: {response}")
else:
    print(f"Failed to set Command Mode. Response: {response}")

# Main loop to read CO₂ levels
while True:
    try:
        # Request CO₂ measurement
        response = send_command("Z")
        if response and response.startswith("Z"):
            co2_ppm = int(response.split()[1]) * 10  # Apply multiplier (default is 10)
            print(f"CO₂ Level: {co2_ppm} ppm")
        else:
            print(f"Unexpected response: {response}")

    except Exception as e:
        print(f"Error during communication: {e}")

    time.sleep(1)
