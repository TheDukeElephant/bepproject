import serial
import time

# Initialize the serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
time.sleep(1)  # Allow sensor to initialize

def send_command(command):
    """
    Sends a command to the sensor and reads the response.
    """
    try:
        # Send the command with required format
        ser.write(command.encode('utf-8') + b'\r\n')
        time.sleep(0.1)  # Allow time for sensor response
        response = ser.read_until(b'\n').decode('utf-8').strip()  # Read response
        return response
    except Exception as e:
        print(f"Error sending command {command}: {e}")
        return None

# Set sensor to Polling Mode (Mode 2)
print("Setting sensor to polling mode...")
response = send_command("K 2")
if response == "K 2":
    print("Sensor is now in polling mode.")
else:
    print(f"Failed to set polling mode. Response: {response}")

# Confirm the multiplier for CO₂ readings
print("Checking multiplier for CO₂ readings...")
multiplier_response = send_command(".")
try:
    multiplier = int(multiplier_response.split()[1])
    print(f"Multiplier for CO₂ readings: {multiplier}")
except (IndexError, ValueError):
    print(f"Failed to retrieve multiplier. Response: {multiplier_response}")
    multiplier = 1  # Default to 1 if response is unclear

# Main loop to read CO₂ levels
while True:
    try:
        # Request the latest CO₂ measurement
        response = send_command("Z")
        
        if response and response.startswith("Z"):
            # Extract CO₂ value and apply multiplier
            co2_ppm = int(response.split()[1]) * multiplier
            print(f"CO₂ Level: {co2_ppm} ppm")
        else:
            print(f"Unexpected response: {response}")

    except Exception as e:
        print(f"Error during communication: {e}")

    time.sleep(1)  # Wait 1 second before next reading
