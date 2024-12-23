import time
import serial
import socket
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio
import Adafruit_DHT
import board  # Required for CircuitPython
import busio
import digitalio
import adafruit_max31865
import adafruit_ssd1306  # For OLED display
from collections import deque
from PIL import Image, ImageDraw, ImageFont


# Default fallback values
FALLBACK_CO2 = 0.04  # Example fallback CO2 level in ppm
FALLBACK_O2 = 21  # Example fallback O2 level in %
FALLBACK_TEMPERATURE = 10  # Example fallback temperature in °C
FALLBACK_HUMIDITY = 36.0  # Example fallback humidity in %

# Buffer to store recent data for reconnections
data_buffer = deque(maxlen=10)  # Store up to the last 10 updates

# Initialize I2C bus for OLED display
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Initialize SPI bus for MAX31865 sensors
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pins = [board.D5, board.D6, board.D13, board.D19, board.D26]
sensors = [adafruit_max31865.MAX31865(spi, digitalio.DigitalInOut(cs), rtd_nominal=100.0, ref_resistor=430.0) for cs in cs_pins]

# Initialize AM2302 (DHT22) humidity sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # GPIO pin number

# Initialize oxygen sensor (MIX8410)
oxygen_sensor_pin = digitalio.DigitalInOut(board.D14)
oxygen_sensor_pin.direction = digitalio.Direction.INPUT

# Initialize CO2 sensors
co2_sensor_pins = [digitalio.DigitalInOut(pin) for pin in [board.D15, board.D8]]
for co2_sensor_pin in co2_sensor_pins:
    co2_sensor_pin.direction = digitalio.Direction.INPUT

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

def background_sensor_read():
    ser = initialize_serial()  # Initialize CO₂ sensor via UART
    if ser is None:
        print("Serial port could not be initialized. Using fallback values for CO₂ and O₂.")

    while True:
        try:
            # Initialize fallback values
            co2_value = FALLBACK_CO2
            o2_value = read_oxygen()
            temperatures = [read_temperature(sensor) for sensor in sensors]
            humidity = read_humidity()

            # CO₂ Sensor Reading
            if ser is not None:
                try:
                    ser.write(b'Z 2\r\n')  # Command to the sensor (check your sensor's documentation)
                    time.sleep(0.1)  # Allow time for response
                    co2_response = ""
                    while ser.in_waiting > 0:
                        co2_response += ser.read().decode("utf-8")
                    co2_response = co2_response.strip()

                    # Check if the response starts with "Z" (or whatever your sensor uses for valid data)
                    if co2_response.startswith("Z") and len(co2_response) > 1:
                        # If valid response, parse it
                        co2_value_ppm = int(co2_response[1:].strip()) * 10
                        co2_value = round(co2_value_ppm / 10000, 2)  # Convert ppm to percentage and round to 2 decimal places
                        print("Response from CO₂ sensor went well")
                    else:
                        print("Unexpected response from CO₂ sensor: no Z output")
                        pass
                except Exception as e:
                    print(f"Error reading CO₂ sensor: {e}")
                    # Use fallback values for CO₂ sensor
                    co2_value = round(FALLBACK_CO2 / 10000, 2)

            # Prepare sensor data to emit
            sensor_data = {
                'timestamp': int(time.time()),
                'co2': co2_value,
                'o2': o2_value,
                'temperatures': [round(temp, 2) for temp in temperatures],
                'humidity': round(humidity, 2)
            }

            # Store data in buffer
            data_buffer.append(sensor_data)

            # Emit the data to connected clients
            socketio.emit('update_dashboard', sensor_data, to=None)
            print("Emitting data successfully.")

            # Display IP address on OLED using pillow library
            ip_address = get_ip_address()
            image = Image.new('1', (oled.width, oled.height))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            draw.text((0, 0), f"IP: {ip_address}", font=font, fill=255)
            oled.image(image)
            oled.show()

        except Exception as e:
            print(f"Error reading sensors: {e}")
            # If an error occurs, emit only fallback values for the sensor that failed
            fallback_data = {
                'timestamp': int(time.time()),
                'co2': round(FALLBACK_CO2 / 10000, 2),
                'o2': FALLBACK_O2,
                'temperatures': [round(FALLBACK_TEMPERATURE, 2)] * len(sensors),
                'humidity': round(FALLBACK_HUMIDITY, 2)
            }
            socketio.emit('update_dashboard', fallback_data, to=None)
        # Wait 1 second before the next reading
        socketio.sleep(1)


@socketio.on('request_data')
def send_buffered_data():
    """Send buffered data to the client upon request."""
    for data in data_buffer:
        emit('update_dashboard', data)
