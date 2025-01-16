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
        time.sleep(0.5)  # Slight delay to allow the sensor to respond
        response = ser.read_until(b'\n').decode('utf-8').strip()
        return response
    except Exception as e:
        print(f"Error sending command {command}: {e}")
        return None

def check_and_disable_auto_calibration():
    """
    Checks if auto-calibration is enabled and disables it if necessary.
    """
    print("Checking auto-calibration setting...")
    response = send_command("@")  # Command to read auto-calibration status
    if response and "@" in response:  # Check for valid response
        if "1.0" in response:  # Auto-calibration is ON
            print("Auto-calibration is ON. Disabling...")
            disable_response = send_command("@ 0")  # Disable auto-calibration
            if disable_response and "@ 0" in disable_response:
                print("Auto-calibration successfully disabled.")
            else:
                print(f"Failed to disable auto-calibration: {disable_response}")
        else:
            print("Auto-calibration is already OFF.")
    else:
        print(f"Unexpected response while checking auto-calibration: {response}")

def ensure_polling_mode():
    """
    Ensures the sensor is in polling mode (Mode 2).
    """
    print("Ensuring the sensor is in polling mode...")
    response = send_command("K")  # Command to check the current mode
    if response and response.startswith("K"):
        current_mode = int(response.split()[1])
        if current_mode != 2:  # If not in polling mode
            print(f"Current mode is {current_mode}. Switching to polling mode...")
            mode_response = send_command("K 2")  # Switch to Mode 2 (Polling mode)
            if mode_response and mode_response.startswith("K 2"):
                print("Sensor successfully switched to polling mode.")
            else:
                print(f"Failed to switch to polling mode: {mode_response}")
        else:
            print("Sensor is already in polling mode.")
    else:
        print(f"Unexpected response while checking mode: {response}")

def reconnect_sensor():
    """
    Reconnects to the sensor by closing and reopening the serial port.
    """
    global ser
    print("Reconnecting to the sensor...")
    ser.close()
    time.sleep(1)
    ser.open()
    time.sleep(2)  # Allow the sensor to stabilize after reconnecting

# Check and disable auto-calibration at the start
check_and_disable_auto_calibration()

# Ensure the sensor is in polling mode
ensure_polling_mode()

zero_readings_count = 0

# Main loop to read CO₂ levels
while True:
    try:
        # Request CO₂ measurement
        response = send_command("Z")  # Command to get filtered CO₂ measurement
        if response and response.startswith("Z"):
            try:
                co2_ppm = int(response.split()[1]) * 10  # Apply multiplier (default is 10)
                print(f"CO₂ Level: {co2_ppm} ppm")

                if co2_ppm == 0:
                    zero_readings_count += 1
                    if zero_readings_count >= 10:  # If zero ppm for 10 consecutive seconds
                        reconnect_sensor()
                        zero_readings_count = 0  # Reset the counter after reconnecting
                else:
                    zero_readings_count = 0  # Reset counter if valid reading

            except (ValueError, IndexError):
                print(f"Malformed CO₂ response: {response}")
        else:
            print(f"Unexpected response: {response}")

    except Exception as e:
        print(f"Error during communication: {e}")

    time.sleep(1)
