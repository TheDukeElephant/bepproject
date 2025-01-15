import time
import serial
import socket
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio
import Adafruit_DHT
import atexit
import board  
import busio
import digitalio
import adafruit_max31865
import adafruit_ssd1306  
import subprocess
from collections import deque
from PIL import Image, ImageDraw, ImageFont
import csv
import subprocess
import RPi.GPIO as GPIO

# Define the output file path
OUTPUT_FILE = "sensor_data.csv"

#interval how often the control function is run (in seconds)
CONTROL_INTERVAL = 10
# Default fallback values which will all be filtered out in js
FALLBACK_CO2 = 40  # Example fallback CO2 level in ppm
FALLBACK_O2 = 23  # Example fallback O2 level in %
FALLBACK_TEMPERATURE = 960  # Example fallback temperature in °C
FALLBACK_HUMIDITY = 101.0  # Example fallback humidity in %

# Buffer to store recent data for reconnections
data_buffer = deque(maxlen=10)  # Store up to the last 10 updates

# Initialize I2C bus and OLED display
i2c = None
oled = None
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
    print("OLED display initialized successfully.")
except Exception as e:
    print(f"Error initializing OLED display: {e}")
    oled = None

# Initialize SPI bus for MAX31865 sensors
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pins = [board.D5, board.D6, board.D13, board.D19, board.D26]
sensors = [adafruit_max31865.MAX31865(spi, digitalio.DigitalInOut(cs), rtd_nominal=100.0, ref_resistor=430.0) for cs in cs_pins]

# Initialize AM2302 (DHT22) humidity sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # GPIO pin number

# Initialize oxygen sensor (MIX8410)
#oxygen_sensor_pin = digitalio.DigitalInOut(board.D14)
#oxygen_sensor_pin.direction = digitalio.Direction.INPUT

# Initialize CO2 sensors
#co2_sensor_pins = [digitalio.DigitalInOut(pin) for pin in [board.D15, board.D8]]
#for co2_sensor_pin in co2_sensor_pins:
#    co2_sensor_pin.direction = digitalio.Direction.INPUT



def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting IP address: {e}")
        ip_address = "N/A"
    finally:
        s.close()
    return ip_address

def get_wifi_ssid():
    try:
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
        ssid = result.stdout.strip()
        if ssid:
            return ssid
        else:
            return "N/A"
    except Exception as e:
        print(f"Error getting Wi-Fi SSID: {e}")
        return "N/A"
    
def read_temperature(sensor):
    try:
        temperature = sensor.temperature
        return temperature
    except Exception as e:
        print(f"Error reading temperature from MAX31865: {e}")
        return FALLBACK_TEMPERATURE

def read_humidity():
    try:
        humidity, _ = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None:
            return humidity
        else:
            raise ValueError("Failed to read humidity")
    except Exception as e:
        print(f"Error reading humidity from AM2302: {e}")
        return FALLBACK_HUMIDITY

def read_oxygen():
    try:
        # Read the analog value from the MIX8410 sensor
        oxygen_value = oxygen_sensor_pin.value
        return oxygen_value
    except Exception as e:
        print(f"Error reading oxygen from MIX8410: {e}")
        return FALLBACK_O2
    
def standby_oled():
    """Display 'Standby...' on the OLED screen."""
    if oled:
        try:
            # Clear the screen
            oled.fill(0)
            oled.show()
            
            # Create an image to display 'Standby...'
            image = Image.new('1', (oled.width, oled.height))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Display 'Standby...' on the OLED screen
            draw.text((0, 30), "Standby...", font=font, fill=255)
            oled.image(image)
            oled.show()
            print("OLED set to 'Standby...'")
        except Exception as e:
            print(f"Error displaying 'Standby...' on OLED: {e}")


#When turning off the python script, display will say: Standby...
atexit.register(standby_oled)

# Write a header row to the output file if it doesn't already exist
def initialize_output_file():
    try:
        with open(OUTPUT_FILE, 'a') as file:
            writer = csv.writer(file)
            # Write header only if the file is empty
            if file.tell() == 0:
                writer.writerow(['timestamp', 'co2', 'o2', 'temperature_1', 'temperature_2',
                                 'temperature_3', 'temperature_4', 'average_temperature', 'humidity'])
    except Exception as e:
        print(f"Error initializing output file: {e}")

# Save sensor data to the output file
def save_to_file(sensor_data):
    try:
        with open(OUTPUT_FILE, 'a') as file:
            writer = csv.writer(file)
            writer.writerow([
                sensor_data['timestamp'],
                sensor_data['co2'],
                sensor_data['o2'],
                *sensor_data['temperatures'],
                sensor_data['humidity']
            ])
    except Exception as e:
        print(f"Error saving to output file: {e}")

# Initialize the output file at the start of the script
initialize_output_file()

def control_temperature(average_temperature):
    """Turn the temperature on or off based on temperature."""
    temperature_pin = 27  # Get the humidifier GPIO pin

    if average_temperature < 36.9:
        GPIO.output(temperature_pin, GPIO.LOW)  # Turn ON the humidifier (LOW for ON)
        print("Temperature heating turned ON")
    elif average_temperature > 37.1:
        GPIO.output(temperature_pin, GPIO.HIGH)  # Turn OFF the humidifier (HIGH for OFF)
        print("Temperature heating turned OFF")


def background_sensor_read():
    ser = initialize_serial()  # Initialize CO₂ sensor via UART
    last_temperature_control_time = time.time()  # Initialize the last control time

    while True:
        try:
            # Reinitialize the serial connection if it becomes invalid
            if ser is None or not ser.is_open:
                print("Reinitializing serial connection...")
                ser = initialize_serial()

            # Initialize fallback values
            co2_value = FALLBACK_CO2
            o2_value = FALLBACK_O2  # Use a constant fallback since it's not dynamically read
            temperatures = [read_temperature(sensor) for sensor in sensors]
            humidity = read_humidity()
            
            # Calculate average temperature
            average_temperature = round((temperatures[2] + temperatures[3]) / 2, 2)

            # Control temperature every 10 seconds
            current_time = time.time()
            if current_time - last_temperature_control_time >= CONTROL_INTERVAL:
                control_temperature(average_temperature)
                last_temperature_control_time = current_time

            # CO₂ Sensor Reading
            if ser is not None:
                try:
                    ser.write(b'Z 2\r\n')  # Send the CO₂ data request command
                    time.sleep(0.1)  # Allow time for response

                    co2_response = ""
                    while ser.in_waiting > 0:
                        co2_response += ser.read().decode("utf-8")
                    co2_response = co2_response.strip()

                    print(f"Raw CO₂ sensor response: {co2_response}")  # Debugging log

                    if co2_response.startswith("Z") and len(co2_response) > 1:
                        co2_value_ppm = int(co2_response[1:].strip()) * 10
                        co2_value = round(co2_value_ppm / 10000, 2)  # Convert ppm to percentage
                        print("Response from CO₂ sensor went well")
                    else:
                        print(f"Unexpected response from CO₂ sensor: {co2_response}")
                except Exception as e:
                    print(f"Error reading CO₂ sensor: {e}")
                    ser.close()  # Close the serial port on failure
                    ser = None  # Mark the connection as invalid
                    co2_value = round(FALLBACK_CO2 / 10000, 2)

            # Prepare sensor data to emit
            sensor_data = {
                'timestamp': int(time.time()),
                'co2': co2_value,
                'o2': o2_value,
                'temperatures': [round(temp, 2) for temp in temperatures] + [round((temperatures[2] + temperatures[3]) / 2, 2)],
                'humidity': round(humidity, 2)
            }

            # Save the data to the file
            save_to_file(sensor_data)

            # Store data in buffer
            data_buffer.append(sensor_data)

            # Emit the data to connected clients
            socketio.emit('update_dashboard', sensor_data, to=None)
            print("Emitting data successfully.")

            # Check for "Not connected" conditions
            display_temp = "Not connected" if sensor_data['temperatures'][5] > 950 else f"{sensor_data['temperatures'][5]} C"
            display_humidity = "Not connected" if sensor_data['humidity'] > 100 else f"{sensor_data['humidity']} %"
            display_o2 = "Not connected" if sensor_data['o2'] > 21 else f"{sensor_data['o2']} %"
            display_co2 = "Not connected" if sensor_data['co2'] > 21 else f"{sensor_data['co2']} %"

            # Display data on the OLED if available
            if oled:
                ip_address = get_ip_address()
                wifi_ssid = get_wifi_ssid()
                image = Image.new('1', (oled.width, oled.height))
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                # Display information on the OLED screen
                draw.text((0, 0), f"SSID: {wifi_ssid}", font=font, fill=255)
                draw.text((0, 10), f"IP: {ip_address}", font=font, fill=255)
                draw.text((0, 20), f"Temp: {display_temp}", font=font, fill=255)
                draw.text((0, 30), f"Humidity: {display_humidity}", font=font, fill=255)
                draw.text((0, 40), f"O2: {display_o2}", font=font, fill=255)
                draw.text((0, 50), f"CO2: {display_co2}", font=font, fill=255)
                
                oled.image(image)
                oled.show()

        except Exception as e:
            print(f"Error reading sensors: {e}")
            # Fallback data on failure
            fallback_data = {
                'timestamp': int(time.time()),
                'co2': round(FALLBACK_CO2 / 10000, 2),
                'o2': FALLBACK_O2,
                'temperatures': [round(FALLBACK_TEMPERATURE, 2)] * len(sensors),
                'humidity': round(FALLBACK_HUMIDITY, 2)
            }
            save_to_file(fallback_data)  # Save fallback data as well
            socketio.emit('update_dashboard', fallback_data, to=None)

        # Emit data every second
        socketio.sleep(1)




@socketio.on('request_data')
def send_buffered_data():
    """Send buffered data to the client upon request."""
    for data in data_buffer:
        emit('update_dashboard', data)
