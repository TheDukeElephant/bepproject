import time
import logging
import threading
from collections import deque

# Import hardware modules
from app.hardware import sensors as hw_sensors
from app.hardware import serial_comms as hw_serial
from app.hardware import display as hw_display

# Import other services and app components
from app.services import datalog_service
from app import socketio # Import the socketio instance from app/__init__

# --- Constants ---
READ_INTERVAL = 1.0 # Seconds between sensor readings
BUFFER_SIZE = 20 # Number of recent readings to keep in memory

# --- State Variables ---
_data_buffer = deque(maxlen=BUFFER_SIZE)
_sensor_thread = None
_stop_event = threading.Event()
_latest_data = {} # Store the most recent complete sensor data dictionary

# --- Private Functions ---
def _sensor_reading_loop():
    """
    The main loop that runs in a background thread to read sensors,
    log data, update display, and emit data.
    """
    global _latest_data
    logging.info("Sensor reading loop started.")

    while not _stop_event.is_set():
        try:
            start_time = time.time()

            # 1. Read all sensors using hardware modules
            temperatures = hw_sensors.read_temperatures() # Expects a list
            humidity = hw_sensors.read_humidity()
            oxygen = hw_sensors.read_oxygen()
            co2 = hw_serial.read_co2_value()

            # Ensure temperatures list has the expected length (5 sensors)
            if len(temperatures) < 5:
                 logging.warning(f"Expected 5 temperature readings, got {len(temperatures)}. Padding with fallback.")
                 temperatures.extend([hw_sensors.FALLBACK_TEMPERATURE] * (5 - len(temperatures)))
            elif len(temperatures) > 5:
                 logging.warning(f"Expected 5 temperature readings, got {len(temperatures)}. Truncating.")
                 temperatures = temperatures[:5]


            # 2. Assemble sensor data dictionary
            current_data = {
                'timestamp': int(start_time),
                'temperatures': temperatures, # List of 5 temps
                'humidity': humidity,
                'o2': oxygen,
                'co2': co2,
                # Add calculated average temp if needed by consumers (e.g., control loop)
                # 'average_temperature': round((temperatures[2] + temperatures[3]) / 2, 2) if len(temperatures) >= 4 else hw_sensors.FALLBACK_TEMPERATURE
            }
            _latest_data = current_data # Update latest data cache

            # 3. Log data to CSV file
            datalog_service.save_data_to_log(current_data)

            # 4. Add to internal buffer
            _data_buffer.append(current_data)

            # 5. Update OLED display
            hw_display.update_display(current_data)

            # 6. Emit data via SocketIO
            # Use the imported socketio instance directly
            socketio.emit('update_dashboard', current_data)
            # logging.debug("Emitted sensor data via SocketIO.") # Use debug level

            # Calculate time taken and sleep accordingly
            elapsed_time = time.time() - start_time
            sleep_time = max(0, READ_INTERVAL - elapsed_time)
            if sleep_time == 0:
                logging.warning(f"Sensor reading loop took longer than interval: {elapsed_time:.2f}s")

            # Use time.sleep() for background threads not managed by socketio directly
            time.sleep(sleep_time)

        except Exception as e:
            logging.error(f"Error in sensor reading loop: {e}", exc_info=True)
            # Avoid busy-waiting on continuous errors
            time.sleep(READ_INTERVAL * 2)

    logging.info("Sensor reading loop stopped.")

# --- Public Service Functions ---
def start_sensor_service():
    """Starts the background thread for reading sensors."""
    global _sensor_thread
    if _sensor_thread is None or not _sensor_thread.is_alive():
        _stop_event.clear()
        _sensor_thread = threading.Thread(target=_sensor_reading_loop, daemon=True)
        _sensor_thread.start()
        logging.info("Sensor service thread started.")
    else:
        logging.warning("Sensor service thread already running.")

def stop_sensor_service():
    """Signals the background sensor reading thread to stop."""
    logging.info("Stopping sensor service thread...")
    _stop_event.set()
    if _sensor_thread and _sensor_thread.is_alive():
        _sensor_thread.join(timeout=READ_INTERVAL * 2) # Wait for thread to finish
        if _sensor_thread.is_alive():
             logging.warning("Sensor service thread did not stop gracefully.")
    _sensor_thread = None
    logging.info("Sensor service thread stop signal sent.")


def get_buffered_data():
    """Returns a list of recent sensor readings from the buffer."""
    return list(_data_buffer)

def get_latest_data():
    """Returns the most recent sensor reading dictionary."""
    return _latest_data.copy() # Return a copy

# --- SocketIO Event Handlers ---
# Moved handler registration here to keep service logic together
def register_socketio_handlers(socketio_instance):
     """Registers SocketIO event handlers related to the sensor service."""
     @socketio_instance.on('request_data')
     def handle_request_data():
         """Sends buffered data to a client requesting it."""
         logging.debug("Client requested buffered data.")
         buffered_data = get_buffered_data()
         for data in buffered_data:
             # Use emit from the passed instance or the global one
             socketio.emit('update_dashboard', data) # Emitting to the requesting client context
         logging.debug(f"Sent {len(buffered_data)} buffered data points.")

# Note:
# - start_sensor_service() should be called once during application startup.
# - stop_sensor_service() could be called during shutdown (e.g., via atexit).
# - register_socketio_handlers(socketio) should be called after socketio is initialized.