import serial
import time

# Initialize the serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
time.sleep(1)  # Allow time for serial initialization

# Function to send commands and handle responses
def send_command(command):
    """
    Sends a command to the sensor and returns the response.
    """
    try:
        ser.write(command.encode('utf-8') + b'\r\n')  # Send command with \r\n
        time.sleep(0.1)  # Wait for response
        response = ser.read_until(b'\n').decode('utf-8').strip()  # Read until newline
        return response
    except Exception as e:
        print(f"Error sending command {command}: {e}")
        return None

# Ensure the sensor is in polling mode (Mode 2)
print("Setting sensor to polling mode...")
response = send_command("K 2")
if response and response.startswith("K"):
    print(f"Sensor mode set to: {response}")
else:
    print(f"Failed to set mode. Response: {response}")

# Main loop to read CO₂ levels
while True:
    try:
        # Request filtered CO₂ reading
        response = send_command("Z")
        
        if response and response.startswith("Z"):
            # Extract the value and apply scaling factor
            co2_ppm = int(response.split()[1]) * 10  # Multiply by scaling factor
            print(f"CO₂ Level: {co2_ppm} ppm")
        else:
            print(f"Unexpected response: {response}")

    except Exception as e:
        print(f"Error during communication: {e}")

    time.sleep(1)  # Wait before next reading
