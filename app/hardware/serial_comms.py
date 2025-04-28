import serial
import time
import logging
import atexit

# --- Constants ---
SERIAL_PORT = '/dev/serial0' # Default serial port on Raspberry Pi for GPIO pins
BAUDRATE = 9600
TIMEOUT = 1.0 # seconds
FALLBACK_CO2_PERCENT = -1.0 # Use a distinct value to indicate failure/unavailable

# Sensor-specific commands (adjust if your sensor uses different commands)
INIT_COMMAND = b'K 2\r\n' # Command sent during initialization (e.g., set continuous mode)
READ_COMMAND = b'Z 2\r\n' # Command to request a CO2 reading

# --- State Variables ---
_serial_connection = None
_is_initialized = False

# --- Internal Functions ---
def _process_co2_response(response_str):
    """
    Processes the raw string response from the CO2 sensor.
    Expected format based on original code: "Zxxxxx" where xxxxx is the reading.
    The original code multiplied by 10 (ppm?) and divided by 10000 (to get %).
    Adjust parsing logic based on your specific sensor's output format.
    """
    try:
        response_str = response_str.strip()
        if response_str.startswith("Z") and len(response_str) > 1:
            # Assuming the part after 'Z' needs to be interpreted
            # Original logic: int(response[1:].strip()) * 10 / 10000
            # Let's refine this based on typical sensor outputs (often direct ppm)
            # Example: If "Z 1234" means 1234 ppm
            parts = response_str.split()
            if len(parts) > 1:
                 co2_value_ppm = int(parts[1])
                 # Convert ppm to percentage
                 co2_percent = round(co2_value_ppm / 10000.0, 2)
                 return co2_percent
            else:
                 # Fallback to original logic if split fails but format seems right
                 co2_value_raw = int(response_str[1:].strip())
                 co2_percent = round((co2_value_raw * 10) / 10000.0, 2) # Original conversion
                 logging.warning(f"Processed CO2 response using original logic: {response_str} -> {co2_percent}%")
                 return co2_percent

        logging.warning(f"Unexpected CO2 sensor response format: '{response_str}'")
        return FALLBACK_CO2_PERCENT
    except ValueError:
        logging.error(f"Could not parse CO2 value from response: '{response_str}'")
        return FALLBACK_CO2_PERCENT
    except Exception as e:
        logging.error(f"Error processing CO2 response '{response_str}': {e}")
        return FALLBACK_CO2_PERCENT

# --- Public Functions ---
def initialize_co2_sensor(port=SERIAL_PORT, baudrate=BAUDRATE, timeout=TIMEOUT):
    """
    Initializes the serial connection to the CO2 sensor.
    Returns True on success, False on failure.
    """
    global _serial_connection, _is_initialized
    if _is_initialized:
        logging.warning("Serial CO2 sensor already initialized.")
        return True

    logging.info(f"Initializing CO2 sensor on {port}...")
    try:
        _serial_connection = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        # Wait briefly for the port to open
        time.sleep(1.5) # Increased sleep slightly

        # Send initialization command if required by the sensor
        if INIT_COMMAND:
            _serial_connection.write(INIT_COMMAND)
            time.sleep(0.2) # Allow time for command processing
            # Optionally read and discard any response to the init command
            _serial_connection.read(_serial_connection.in_waiting or 1)

        _is_initialized = True
        logging.info("CO2 sensor serial connection established.")
        atexit.register(close_serial_port) # Ensure cleanup on exit
        return True
    except serial.SerialException as e:
        logging.error(f"SerialException initializing CO2 sensor on {port}: {e}")
        _serial_connection = None
        _is_initialized = False
        return False
    except Exception as e:
        logging.error(f"Unexpected error initializing CO2 sensor: {e}")
        _serial_connection = None
        _is_initialized = False
        return False

def read_co2_value():
    """
    Reads the CO2 value from the serial sensor.
    Returns the CO2 percentage or FALLBACK_CO2_PERCENT on failure.
    """
    if not _is_initialized or not _serial_connection:
        logging.warning("CO2 sensor serial port not initialized.")
        return FALLBACK_CO2_PERCENT

    try:
        # Clear input buffer before sending command
        _serial_connection.reset_input_buffer()
        # Send the command to request data
        _serial_connection.write(READ_COMMAND)
        # Wait for the sensor to respond
        time.sleep(0.2) # Adjust sleep time based on sensor response time

        # Read the response
        if _serial_connection.in_waiting > 0:
            response_bytes = _serial_connection.read(_serial_connection.in_waiting)
            response_str = response_bytes.decode("utf-8", errors='ignore') # Decode safely
            return _process_co2_response(response_str)
        else:
            logging.warning("No response received from CO2 sensor.")
            return FALLBACK_CO2_PERCENT

    except serial.SerialException as e:
        logging.error(f"SerialException reading CO2 sensor: {e}")
        # Consider attempting to re-initialize or flag the connection as broken
        return FALLBACK_CO2_PERCENT
    except Exception as e:
        logging.error(f"Unexpected error reading CO2 sensor: {e}")
        return FALLBACK_CO2_PERCENT

def close_serial_port():
    """Closes the serial port connection if open."""
    global _serial_connection, _is_initialized
    if _serial_connection and _serial_connection.is_open:
        logging.info("Closing CO2 sensor serial port...")
        try:
            _serial_connection.close()
            logging.info("CO2 sensor serial port closed.")
        except Exception as e:
            logging.error(f"Error closing serial port: {e}")
    _serial_connection = None
    _is_initialized = False

# Note: initialize_co2_sensor() should be called once during application startup.
# atexit registration is handled within initialize_co2_sensor().