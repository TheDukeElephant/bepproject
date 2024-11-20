import time
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio
import Adafruit_DHT  # Example for temperature and humidity sensor (DHT22)

# Initialize DHT Sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # GPIO pin for the DHT sensor


def background_sensor_read():
    ser = initialize_serial()  # Initialize CO₂ sensor
    while True:
        try:
            # CO₂ Sensor Reading
            ser.write(b'Z\r\n')
            time.sleep(0.1)
            co2_response = ""
            while ser.in_waiting > 0:
                co2_response += ser.read().decode("utf-8")
            co2_response = co2_response.strip()
            if co2_response.startswith("Z") and len(co2_response) > 1:
                co2_value = int(co2_response[1:].strip())
                print(f"CO2 Concentration: {co2_value} ppm")
                socketio.emit('update_data', {'co2': co2_value}, broadcast=True)
            else:
                print(f"Unexpected response from sensor: {co2_response}")

            # Temperature and Humidity Reading
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if humidity is None or temperature is None:
                humidity, temperature = "N/A", "N/A"

            # Emit the data to connected clients
            print(f"Emitting data: CO2: {co2_value}, Temp: {temperature}, Humidity: {humidity}")
            socketio.emit('update_dashboard', {
               'co2': co2_value,
               'temperature': round(temperature, 2) if temperature != "N/A" else "N/A",
               'humidity': round(humidity, 2) if humidity != "N/A" else "N/A"
            }, broadcast=True)


        except Exception as e:
            print(f"Error reading sensors: {e}")
            # Emit placeholder data in case of error
            socketio.emit('update_dashboard', {
                'co2': '?',
                'temperature': 'N/A',
                'humidity': 'N/A'
            }, broadcast=True)

        # Wait 1 second before the next reading
        socketio.sleep(1)
