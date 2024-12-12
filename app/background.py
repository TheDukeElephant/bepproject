import time
import serial
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio
import Adafruit_DHT
import board  # Required for CircuitPython
from collections import deque


# Initialize DHT Sensor
#dht_device = None  # Initialize to None to avoid reference errors

# Try to initialize the DHT sensor
# try:
#     dht_device = Adafruit_DHT.DHT22(board.D4)  # Use GPIO pin 4
# except Exception as e:
#     print(f"Error initializing DHT sensor: {e}")

# Default fallback values
FALLBACK_CO2 = 0.04  # Example fallback CO2 level in ppm
FALLBACK_O2 = 21  # Example fallback O2 level in %
FALLBACK_TEMPERATURE = 18.6  # Example fallback temperature in °C
FALLBACK_HUMIDITY = 36.0  # Example fallback humidity in %

# Buffer to store recent data for reconnections
data_buffer = deque(maxlen=10)  # Store up to the last 10 updates

def background_sensor_read():
    ser = initialize_serial()  # Initialize CO₂ sensor via UART
    if ser is None:
        print("Serial port could not be initialized. Using fallback values for CO₂ and O₂.")

    while True:
        try:
            # Initialize fallback values
            co2_value = FALLBACK_CO2
            o2_value = FALLBACK_O2
            temperature = FALLBACK_TEMPERATURE
            humidity = FALLBACK_HUMIDITY

            # CO₂ and O₂ Sensor Reading
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
                        o2_value_ppm = int(co2_response[1:].strip()) * 10
                        o2_value = 16 + round(o2_value_ppm / 3000, 2)# Adjust if O2 data is different
                        #print("Response from CO₂ sensor went well")
                    else:
                        
                        print("Unexpected response from CO₂ sensor: no Z output")
                        pass
                except Exception as e:
                    print(f"Error reading CO₂ sensor: {e}")
                    # Use fallback values for CO₂ sensor
                    co2_value = round(FALLBACK_CO2 / 10000, 2)
                    o2_value = FALLBACK_O2

            # Temperature and Humidity Reading
            """ if dht_device is not None:
                try:
                    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, board.D4)
                    if humidity is None or temperature is None:
                        print("Failed to read from DHT sensor, using fallback values.")
                        temperature = FALLBACK_TEMPERATURE
                        humidity = FALLBACK_HUMIDITY
                except RuntimeError as error:
                    print(f"DHT sensor read error: {error}")
                    # Use fallback values in case of a runtime error
                    temperature = FALLBACK_TEMPERATURE
                    humidity = FALLBACK_HUMIDITY
                except Exception as error:
                    print(f"Critical error with DHT sensor: {error}")
                    # Disable further readings if the sensor fails
                    dht_device = None
                    # Use fallback values for DHT sensor
                    temperature = FALLBACK_TEMPERATURE
                    humidity = FALLBACK_HUMIDITY
 """
            # Prepare sensor data to emit
            sensor_data = {
                'timestamp': int(time.time()),
                'co2': co2_value,
                'o2': o2_value,
                'temperature': round(temperature, 2),
                'humidity': round(humidity, 2)
            }

            # Store data in buffer
            data_buffer.append(sensor_data)

            # Emit the data to connected clients
            socketio.emit('update_dashboard', sensor_data, to=None)
            #print("Emitting data successfully.")

        except Exception as e:
            print(f"Error reading sensors: {e}")
            # If an error occurs, emit only fallback values for the sensor that failed
            fallback_data = {
                'timestamp': int(time.time()),
                'co2': round(FALLBACK_CO2 / 10000, 2),
                'o2': FALLBACK_O2,
                'temperature': round(FALLBACK_TEMPERATURE, 2),
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
