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
        time.sleep(0.001)  # Allow time for sensor to respond
        response = ser.read_until(b'\n').decode('utf-8').strip()
        return response
    except Exception as e:
        print(f"Error sending command {command}: {e}")
        return None

# Calibrate the sensor for 400 ppm in fresh air
def calibrate_sensor():
    print("Starting calibration to 400 ppm...")
    calibration_response = send_command("G")  # Send fresh air zero-point calibration command
    if calibration_response and calibration_response.startswith("G"):
        print(f"Calibration successful: {calibration_response}")
    else:
        print(f"Calibration failed or unexpected response: {calibration_response}")

# Perform calibration
calibrate_sensor()

# Main loop to read CO₂ levels
while True:
    try:
        # Request CO₂ measurement
        response = send_command("Z")  # Command to get filtered CO₂ measurement
        if response and response.startswith("Z"):
            co2_ppm = int(response.split()[1]) * 10  # Apply multiplier (default is 10)
            print(f"CO₂ Level: {co2_ppm} ppm")
        else:
            print(f"Unexpected response: {response}")

    except Exception as e:
        print(f"Error during communication: {e}")

    time.sleep(1)
