import time
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio
import Adafruit_DHT  # Example for temperature and humidity sensor (DHT22)

# Initialize DHT Sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # GPIO pin for the DHT sensor

# Default fallback values
FALLBACK_CO2 = 400  # Example fallback CO2 level in ppm
FALLBACK_O2 = 21  # Example fallback O2 level in %
FALLBACK_TEMPERATURE = 22.0  # Example fallback temperature in °C
FALLBACK_HUMIDITY = 50.0  # Example fallback humidity in %

def background_sensor_read():
    ser = initialize_serial()  # Initialize CO₂ sensor
    if ser is None:
        print("Serial port could not be initialized. Using fallback values for CO₂ and O₂.")

    while True:
        try:
            # CO₂ and O₂ Sensor Reading
            co2_value = FALLBACK_CO2
            o2_value = FALLBACK_O2

            if ser is not None:
                try:
                    ser.write(b'Z\r\n')
                    time.sleep(0.1)
                    co2_response = ""
                    while ser.in_waiting > 0:
                        co2_response += ser.read().decode("utf-8")
                    co2_response = co2_response.strip()
                    if co2_response.startswith("Z") and len(co2_response) > 1:
                        co2_value = int(co2_response[1:].strip()) * 10
                        o2_value = int(co2_response[1:].strip()) * 10
                    else:
                        print(f"Unexpected response from sensor: {co2_response}")
                except Exception as e:
                    print(f"Error reading CO₂ sensor: {e}")
            
            # Temperature and Humidity Reading
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if humidity is None or temperature is None:
                print("DHT sensor not responding. Using fallback values.")
                humidity, temperature = FALLBACK_HUMIDITY, FALLBACK_TEMPERATURE

            # Emit the data to connected clients
            socketio.emit('update_dashboard', {
                'co2': co2_value,
                'o2': o2_value,
                'temperature': round(temperature, 2) if temperature != "N/A" else "N/A",
                'humidity': round(humidity, 2) if humidity != "N/A" else "N/A"
            }, broadcast=True)

        except Exception as e:
            print(f"Error reading sensors: {e}")
            # Emit fallback data in case of error
            socketio.emit('update_dashboard', {
                'co2': FALLBACK_CO2,
                'o2': FALLBACK_O2,
                'temperature': FALLBACK_TEMPERATURE,
                'humidity': FALLBACK_HUMIDITY
            }, broadcast=True)

        # Wait 1 second before the next reading
        socketio.sleep(1)
