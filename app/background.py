import time
import serial
import socket
from flask_socketio import emit
from app.serial_port import initialize_serial
from . import socketio
import Adafruit_DHT
import atexit
import threading
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
from . import DFRobot_Oxygen
from .DFRobot_Oxygen import DFRobot_Oxygen_IIC  # Updated import
import logging
#from config import TEMP_LOWER_BOUND, TEMP_UPPER_BOUND, FALLBACK_CO2, FALLBACK_O2
from config import Config  # Updated import

# output file kiezen naam
OUTPUT_FILE = "sensor_data.csv"


threads_started = False

CONTROL_INTERVAL_TEMP = 10

CONTROL_INTERVAL_CO2 = 30
TIME_CO2_SOLENOID_ON = 0.1
FALLBACK_TEMPERATURE = 960 
FALLBACK_HUMIDITY = 101.0  


data_buffer = deque(maxlen=10) 


i2c = None
oled = None
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
    logging.info("OLED display initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing OLED display: {e}")
    oled = None

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pins = [board.D5, board.D6, board.D13, board.D19, board.D26]
sensors = [adafruit_max31865.MAX31865(spi, digitalio.DigitalInOut(cs), rtd_nominal=100.0, ref_resistor=430.0) for cs in cs_pins]


DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  

# Initialize the DFRobot Gravity Oxygen Sensor
oxygen_sensor = DFRobot_Oxygen_IIC(busio.I2C(board.SCL, board.SDA), 0x73)  # Updated class name


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception as e:
        logging.error(f"Error getting IP address: {e}")
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
        logging.error(f"Error getting Wi-Fi SSID: {e}")
        return "N/A"
    
def read_temperature(sensor):
    try:
        temperature = sensor.temperature
        return temperature
    except Exception as e:
        logging.error(f"Error reading temperature from MAX31865: {e}")
        return FALLBACK_TEMPERATURE

def read_humidity():
    try:
        humidity, _ = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None:
            return humidity
        else:
            raise ValueError("Failed to read humidity")
    except Exception as e:
        logging.error(f"Error reading humidity from AM2302: {e}")
        return FALLBACK_HUMIDITY

def read_oxygen():
    try:
        oxygen_value = oxygen_sensor.get_oxygen_concentration()
        return oxygen_value
    except Exception as e:
        logging.error(f"Error reading oxygen from DFRobot Gravity Oxygen Sensor: {e}")
        return FALLBACK_O2
    
def standby_oled():

    if oled:
        try:
            # scherm reset
            oled.fill(0)
            oled.show()
            
            
            image = Image.new('1', (oled.width, oled.height))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            
            draw.text((0, 30), "Standby...", font=font, fill=255)
            oled.image(image)
            oled.show()
            logging.info("OLED set to 'Standby...'")
        except Exception as e:
            logging.error(f"Error displaying 'Standby...' on OLED: {e}")


#standby functie voor als je het script sluit
atexit.register(standby_oled)


def initialize_output_file():
    try:
        with open(OUTPUT_FILE, 'a') as file:
            writer = csv.writer(file)
            
            if file.tell() == 0:
                writer.writerow(['timestamp', 'co2', 'o2', 'temperature_1', 'temperature_2',
                                 'temperature_3', 'temperature_4', 'average_temperature', 'humidity'])
    except Exception as e:
        logging.error(f"Error initializing output file: {e}")

# data opslaan belangrijk voor de grafieken van de incubator
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
        logging.error(f"Error saving to output file: {e}")

# output file nodig voor het opslaan van de waardes
initialize_output_file()

def control_temperature(average_temperature):
    """
    Turns the heater on or off based on temperature bounds from config.
    """
    temperature_pin = 27  

    if average_temperature < Config.TEMP_LOWER_BOUND:
        GPIO.output(temperature_pin, GPIO.LOW)  
        logging.info("Temperature heating turned ON")
    elif average_temperature > Config.TEMP_UPPER_BOUND:
        GPIO.output(temperature_pin, GPIO.HIGH) 
        logging.info("Temperature heating turned OFF")

def control_co2(co2_value):
    """
    Activates CO2 solenoid for short bursts if below threshold.
    """
    temperature_pin = 4  

    if co2_value > 0.01 and co2_value < 5:
        GPIO.output(temperature_pin, GPIO.LOW)  
        logging.info("CO2 solenoid turned ON")
        time.sleep(TIME_CO2_SOLENOID_ON)
        GPIO.output(temperature_pin, GPIO.HIGH) 
        logging.info("CO2 solenoid turned OFF")
    elif co2_value > 5:
        GPIO.output(temperature_pin, GPIO.HIGH) 
        logging.info("CO2 solenoid turned OFF")


def temperature_control_thread():
    while True:
        try:
            
            temperatures = [read_temperature(sensor) for sensor in sensors]
            average_temperature = round((temperatures[2] + temperatures[3]) / 2, 2)
            
            control_temperature(average_temperature)
            time.sleep(CONTROL_INTERVAL_TEMP) 
        except Exception as e:
            logging.error(f"Error in temperature control thread: {e}")


def co2_control_thread():
    while True:
        try:
            ser = initialize_serial()
            if ser is not None:
                co2_value = get_co2_value_from_serial(ser)
            else:
                co2_value = Config.FALLBACK_CO2

            control_co2(co2_value)
            time.sleep(CONTROL_INTERVAL_CO2)  
        except Exception as e:
            logging.error(f"Error in CO2 control thread: {e}")


def background_sensor_read():
    #zet uart aan
    ser = initialize_serial()  
    last_temperature_control_time_temp = time.time()  
    last_temperature_control_time_co2 = time.time()  
    global threads_started
    
    if not threads_started:
        # multithreading want is beter
        threading.Thread(target=temperature_control_thread, daemon=True).start()
        threading.Thread(target=co2_control_thread, daemon=True).start()
        threads_started = True


    while True:
        try:
            # serial down? nog een keer
            if ser is None or not ser.is_open:
                logging.info("Reinitializing serial connection...")
                ser = initialize_serial()

            # fallbacks
            co2_value = Config.FALLBACK_CO2
            o2_value = Config.FALLBACK_O2  
            temperatures = [read_temperature(sensor) for sensor in sensors]
            humidity = read_humidity()
            
            # gemid temp
            average_temperature = round((temperatures[2] + temperatures[3]) / 2, 2)

            # elke 10 sec controlleer de temperatuur	
            current_time = time.time()
            if current_time - last_temperature_control_time_temp >= CONTROL_INTERVAL_TEMP:
                control_temperature(average_temperature)
                last_temperature_control_time_temp = current_time

            
            # co2 lezen met serial port, doe voorzichtig want sensor werkt niet goed, niet te vaak aansturen.
            if ser is not None:
                co2_value = get_co2_value_from_serial(ser)

            # start co2 function als interval is geweest
            if current_time - last_temperature_control_time_co2 >= CONTROL_INTERVAL_CO2:
                control_co2(co2_value)
                last_temperature_control_time_co2 = current_time

            # Read oxygen value from the Grove Oxygen Sensor
            o2_value = read_oxygen()

            # data voordat emit word in array
            sensor_data = {
                'timestamp': int(time.time()),
                'co2': co2_value,
                'o2': o2_value,
                'temperatures': [round(temp, 2) for temp in temperatures] + [round((temperatures[2] + temperatures[3]) / 2, 2)],
                'humidity': round(humidity, 2)
            }

            # data saving naar csv bestand
            save_to_file(sensor_data)

            # data buffer omdat wifi niet goed werkt
            data_buffer.append(sensor_data)

            # data moet naar alle clienten
            socketio.emit('update_dashboard', sensor_data, to=None)
            logging.info("Emitting data successfully.")

            # als niet in range, zorg dat er not connected staat voor het gemak van de gebruiker
            display_temp = "Not connected" if sensor_data['temperatures'][5] > 950 else f"{sensor_data['temperatures'][5]} C"
            display_humidity = "Not connected" if sensor_data['humidity'] > 100 else f"{sensor_data['humidity']} %"
            display_o2 = "Not connected" if sensor_data['o2'] > 21 else f"{sensor_data['o2']} %"
            display_co2 = "Not connected" if sensor_data['co2'] > 21 else f"{sensor_data['co2']} %"

            # oled scherm aanzetten met de goede library en alvast functies aansturen die ip adres een wifi ssid krijgen
            if oled:
                ip_address = get_ip_address()
                wifi_ssid = get_wifi_ssid()
                image = Image.new('1', (oled.width, oled.height))
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                # oled schermpje weergave
                draw.text((0, 0), f"SSID: {wifi_ssid}", font=font, fill=255)
                draw.text((0, 10), f"IP: {ip_address}", font=font, fill=255)
                draw.text((0, 20), f"Temp: {display_temp}", font=font, fill=255)
                draw.text((0, 30), f"Humidity: {display_humidity}", font=font, fill=255)
                draw.text((0, 40), f"O2: {display_o2}", font=font, fill=255)
                draw.text((0, 50), f"CO2: {display_co2}", font=font, fill=255)
                
                oled.image(image)
                oled.show()

        except Exception as e:
            logging.error(f"Error reading sensors: {e}")
            # data moet altijd een fallback hebben voor als een sensor breekt.
            fallback_data = {
                'timestamp': int(time.time()),
                'co2': round(Config.FALLBACK_CO2 / 10000, 2),
                'o2': Config.FALLBACK_O2,
                'temperatures': [round(FALLBACK_TEMPERATURE, 2)] * len(sensors),
                'humidity': round(FALLBACK_HUMIDITY, 2)
            }
            save_to_file(fallback_data)  # fallback data moet ook gesaved worden
            socketio.emit('update_dashboard', fallback_data, to=None)

        # Emit data elke seconde want slapen 1 sec
        socketio.sleep(1)

def get_co2_value_from_serial(ser):
    try:
        ser.write(b'Z 2\r\n')
        time.sleep(0.1)
        co2_response = ser.read(ser.in_waiting).decode("utf-8").strip()
        return process_co2_response(co2_response)
    except Exception as e:
        logging.error(f"Error reading CO2 sensor: {e}")
        return Config.FALLBACK_CO2


def process_co2_response(response):
    try:
        if response.startswith("Z") and len(response) > 1:
            co2_value_ppm = int(response[1:].trip()) * 10
            return round(co2_value_ppm / 10000, 2)
    except Exception as e:
        logging.error("Error processing CO2 response: %s", e)
    return Config.FALLBACK_CO2

temperatures = [read_temperature(sensor) for sensor in sensors]
# gemiddelde temperaturen berekenen want handig voor het project.
def calculate_average_temperature(temperatures):
    average_temperature = round((temperatures[2] + temperatures[3]) / 2, 2)
    
    return average_temperature

@socketio.on('request_data')
def send_buffered_data():
    #dit is om de data te verzenden naar de socketio om te emitten naar het dashboard, (niks veranderen!)
    for data in data_buffer:
        emit('update_dashboard', data)
