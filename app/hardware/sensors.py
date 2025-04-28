import logging
import board
import busio
import digitalio
import adafruit_max31865
import Adafruit_DHT
# Assuming DFRobot_Oxygen.py is correctly placed relative to this file or installable
# If DFRobot_Oxygen.py is in the app/ directory, the import should work.
# If it's meant to be a library, it should be in requirements.txt
try:
    from app.DFRobot_Oxygen import DFRobot_Oxygen_IIC
except ImportError:
    logging.error("Failed to import DFRobot_Oxygen_IIC. Make sure DFRobot_Oxygen.py is in the 'app' directory or installed.")
    DFRobot_Oxygen_IIC = None # Define as None if import fails

# --- Constants ---
# Fallback values (used if sensor reading fails)
FALLBACK_TEMPERATURE = 999.0 # Using a distinct value to indicate failure
FALLBACK_HUMIDITY = -1.0    # Using a distinct value
FALLBACK_OXYGEN = -1.0      # Using a distinct value

# DHT Sensor Configuration
DHT_SENSOR_TYPE = Adafruit_DHT.DHT22
DHT_PIN = 4 # GPIO Pin (BCM numbering)

# MAX31865 Configuration
RTD_NOMINAL_RESISTANCE = 100.0
RTD_REF_RESISTANCE = 430.0
# Define CS pins for each MAX31865 sensor
CS_PINS = [board.D5, board.D6, board.D13, board.D19, board.D26]

# DFRobot Oxygen Sensor Configuration
OXYGEN_I2C_BUS = 1 # Raspberry Pi I2C bus 1
OXYGEN_I2C_ADDRESS = 0x73

# --- State Variables ---
_spi = None
_i2c = None
_temp_sensors = [] # List to hold MAX31865 sensor objects
_oxygen_sensor = None # Holds the DFRobot_Oxygen_IIC object

# --- Initialization ---
def initialize_sensors():
    """Initializes all connected sensors (Temperature, Humidity, Oxygen)."""
    global _spi, _i2c, _temp_sensors, _oxygen_sensor
    logging.info("Initializing hardware sensors...")

    # Initialize SPI for Temperature Sensors
    try:
        _spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        _temp_sensors = [] # Clear previous instances if any
        for cs_pin in CS_PINS:
            try:
                cs_digitalio = digitalio.DigitalInOut(cs_pin)
                sensor = adafruit_max31865.MAX31865(
                    _spi,
                    cs_digitalio,
                    rtd_nominal=RTD_NOMINAL_RESISTANCE,
                    ref_resistor=RTD_REF_RESISTANCE
                )
                _temp_sensors.append(sensor)
                logging.info(f"MAX31865 sensor on CS pin {cs_pin} initialized.")
            except Exception as e:
                 logging.error(f"Failed to initialize MAX31865 on CS pin {cs_pin}: {e}")
                 _temp_sensors.append(None) # Add None as placeholder if init fails

    except Exception as e:
        logging.error(f"Failed to initialize SPI bus: {e}")
        _spi = None # Ensure SPI is None if failed
        _temp_sensors = [None] * len(CS_PINS) # Fill with None placeholders

    # Initialize I2C for Oxygen Sensor (if library loaded)
    if DFRobot_Oxygen_IIC:
        try:
            # Note: I2C is often initialized elsewhere too (e.g., for OLED).
            # Consider passing an existing I2C bus object if available.
            _i2c = busio.I2C(board.SCL, board.SDA)
            _oxygen_sensor = DFRobot_Oxygen_IIC(OXYGEN_I2C_BUS, OXYGEN_I2C_ADDRESS)
            # Perform a basic check if possible (e.g., read data once)
            _oxygen_sensor.get_oxygen_data(1) # Example check
            logging.info(f"DFRobot Oxygen sensor on I2C bus {OXYGEN_I2C_BUS} address {OXYGEN_I2C_ADDRESS} initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize DFRobot Oxygen sensor: {e}")
            _oxygen_sensor = None
            # Don't reset _i2c here as it might be used by other devices (OLED)
    else:
        logging.warning("DFRobot_Oxygen_IIC library not available. Oxygen sensor disabled.")
        _oxygen_sensor = None

    # DHT sensor doesn't require explicit object initialization here,
    # Adafruit_DHT.read_retry handles it.
    logging.info("Sensor initialization complete.")

# --- Reading Functions ---
def read_temperatures():
    """Reads temperature from all initialized MAX31865 sensors."""
    temperatures = []
    for i, sensor in enumerate(_temp_sensors):
        if sensor:
            try:
                temp = sensor.temperature
                # Add basic validation if needed (e.g., check reasonable range)
                temperatures.append(round(temp, 2))
            except Exception as e:
                logging.warning(f"Error reading temperature from MAX31865 sensor {i}: {e}")
                temperatures.append(FALLBACK_TEMPERATURE)
        else:
            # Sensor failed to initialize
            temperatures.append(FALLBACK_TEMPERATURE)
    return temperatures

def read_humidity():
    """Reads humidity from the DHT22 sensor."""
    try:
        # read_retry handles the communication and retries
        humidity, temp_from_dht = Adafruit_DHT.read_retry(DHT_SENSOR_TYPE, DHT_PIN)
        if humidity is not None:
            # Add basic validation if needed (e.g., 0-100 range)
            return round(humidity, 2)
        else:
            logging.warning("Failed to read humidity from DHT sensor (returned None).")
            return FALLBACK_HUMIDITY
    except Exception as e:
        # This might catch runtime errors or library issues
        logging.error(f"Error reading humidity from DHT sensor: {e}")
        return FALLBACK_HUMIDITY

def read_oxygen():
    """Reads oxygen concentration from the DFRobot Gravity Oxygen Sensor."""
    if _oxygen_sensor:
        try:
            # The '1' likely refers to the number of samples or a mode
            oxygen_value = _oxygen_sensor.get_oxygen_data(1)
            if oxygen_value is not None:
                 # Add basic validation if needed (e.g., 0-25% range typical)
                return round(oxygen_value, 2)
            else:
                logging.warning("Failed to read oxygen from DFRobot sensor (returned None).")
                return FALLBACK_OXYGEN
        except Exception as e:
            logging.error(f"Error reading oxygen from DFRobot sensor: {e}")
            return FALLBACK_OXYGEN
    else:
        # Sensor not initialized or library failed to load
        # logging.debug("Oxygen sensor not available.") # Use debug level if frequent
        return FALLBACK_OXYGEN

# Note: initialize_sensors() should be called once during application startup.