import Adafruit_DHT
import time

# Define the sensor type and GPIO pin number
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  # Use the GPIO pin where the DHT22 data pin is connected

def read_sensor():
    """Reads the temperature and humidity values from the sensor."""
    humidity, temperature_celsius = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

    if humidity is not None and temperature_celsius is not None:
        # Convert Celsius to Fahrenheit
        temperature_fahrenheit = (temperature_celsius * 9 / 5) + 32
        # Convert Celsius to Kelvin
        temperature_kelvin = temperature_celsius + 273.15
        # Convert Celsius to Rankine
        temperature_rankine = (temperature_celsius + 273.15) * 9 / 5

        print(f"Celsius = {temperature_celsius:.2f} °C")
        print(f"Fahrenheit = {temperature_fahrenheit:.2f} °F")
        print(f"Kelvin = {temperature_kelvin:.2f} K")
        print(f"Rankine = {temperature_rankine:.2f} °R")
        print(f"Humidity = {humidity:.2f} %")
    else:
        print("Failed to retrieve data from humidity sensor")

if __name__ == "__main__":
    print("DHT22 sensor testing on Raspberry Pi")
    while True:
        read_sensor()
        time.sleep(2)  # Delay between readings
