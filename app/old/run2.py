"""
DEPRECATED: Use 'run.py' or updated scripts instead.
Retained for historical reference only.
"""

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

def flush_serial_buffer():
    """
    Flushes any remaining data in the serial buffer to avoid misinterpretation.
    """
    ser.reset_input_buffer()
    ser.reset_output_buffer()

def disable_auto_calibration():
    """
    Disables auto-calibration if it is enabled.
    """
    print("Disabling auto-calibration...")
    for _ in range(3):  # Retry up to 3 times
        response = send_command("@ 0")  # Disable auto-calibration
        if response and "@ 0" in response:
            print("Auto-calibration successfully disabled.")
            return
        else:
            print(f"Retrying auto-calibration disable. Response: {response}")
    print("Failed to disable auto-calibration after 3 attempts.")

def force_polling_mode():
    """
    Forces the sensor into polling mode (Mode 2).
    """
    print("Forcing the sensor into polling mode...")
    for _ in range(3):  # Retry up to 3 times
        response = send_command("K 2")  # Set Mode 2 (Polling Mode)
        if response and response.startswith("K 2"):
            print("Sensor successfully set to polling mode.")
            return
        else:
            print(f"Retrying mode set to polling. Response: {response}")
    print("Failed to set polling mode after 3 attempts.")

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

# Initial setup
flush_serial_buffer()
disable_auto_calibration()
force_polling_mode()

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