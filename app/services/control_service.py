import time
import logging
import threading

# Import config and hardware/service layers
from config import Config
from app.hardware import gpio_devices as hw_gpio
from app.hardware import sensors as hw_sensors
from app.hardware import serial_comms as hw_serial
from app.services import sensor_service # To get latest data if needed

# --- Constants ---
# Control loop intervals (seconds) - Consider moving to Config if user-adjustable
TEMP_CONTROL_INTERVAL = 10
CO2_CONTROL_INTERVAL = 30
# CO2 solenoid on-time (seconds) - Consider moving to Config
CO2_SOLENOID_ON_TIME = 0.1

# --- State Variables ---
_temp_control_thread = None
_co2_control_thread = None
_stop_event = threading.Event()

# --- Private Control Logic Functions ---
def _control_temperature():
    """Checks temperature and controls the heater relay."""
    try:
        # Get latest temperature data
        # Option 1: Use sensor_service cache (slightly delayed but less hardware access)
        # latest_data = sensor_service.get_latest_data()
        # temperatures = latest_data.get('temperatures', [])

        # Option 2: Read directly from hardware (more immediate)
        temperatures = hw_sensors.read_temperatures()

        if not temperatures or len(temperatures) < 4:
             logging.warning("Control Service: Insufficient temperature data to control heater.")
             return

        # Calculate average temperature (using sensors 3 and 4 as per original logic)
        # Check if readings are valid before averaging
        temp3 = temperatures[2]
        temp4 = temperatures[3]
        if temp3 == hw_sensors.FALLBACK_TEMPERATURE or temp4 == hw_sensors.FALLBACK_TEMPERATURE:
             logging.warning("Control Service: Fallback temperature reading detected, skipping heater control.")
             return

        average_temperature = round((temp3 + temp4) / 2, 2)
        logging.debug(f"Control Service: Avg Temp = {average_temperature:.2f} C")

        # Get current heater state (optional, for logging state changes)
        current_state = hw_gpio.get_device_state(hw_gpio.ITO_HEATING)

        # Apply control logic based on Config thresholds
        if average_temperature < Config.TEMP_LOWER_BOUND:
            if current_state != 'on':
                logging.info(f"Temp below lower bound ({Config.TEMP_LOWER_BOUND}). Turning heater ON.")
                hw_gpio.set_device_state(hw_gpio.ITO_HEATING, 'on')
            else:
                 logging.debug("Temp below lower bound, heater already ON.")
        elif average_temperature > Config.TEMP_UPPER_BOUND:
            if current_state != 'off':
                logging.info(f"Temp above upper bound ({Config.TEMP_UPPER_BOUND}). Turning heater OFF.")
                hw_gpio.set_device_state(hw_gpio.ITO_HEATING, 'off')
            else:
                 logging.debug("Temp above upper bound, heater already OFF.")
        else:
            # Temperature is within bounds, ensure heater state is logged if it was previously unknown
            if current_state is None: # Log initial state if unknown
                 logging.info(f"Temp within bounds [{Config.TEMP_LOWER_BOUND}-{Config.TEMP_UPPER_BOUND}]. Heater state: {hw_gpio.get_device_state(hw_gpio.ITO_HEATING)}")
            else:
                 logging.debug(f"Temp within bounds [{Config.TEMP_LOWER_BOUND}-{Config.TEMP_UPPER_BOUND}]. Heater state: {current_state}")


    except Exception as e:
        logging.error(f"Error in temperature control logic: {e}", exc_info=True)


def _control_co2():
    """Checks CO2 level and controls the CO2 solenoid."""
    try:
        # Get latest CO2 reading
        # Option 1: Use sensor_service cache
        # latest_data = sensor_service.get_latest_data()
        # co2_value = latest_data.get('co2', hw_serial.FALLBACK_CO2_PERCENT)

        # Option 2: Read directly from hardware
        co2_value = hw_serial.read_co2_value()
        logging.debug(f"Control Service: CO2 = {co2_value:.2f} %")

        if co2_value == hw_serial.FALLBACK_CO2_PERCENT:
             logging.warning("Control Service: Fallback CO2 reading detected, skipping CO2 control.")
             return

        # Apply control logic based on Config threshold
        # Original logic: Turn on briefly if between 0.01% and 5% (CO2_THRESHOLD)
        # Assuming Config.CO2_THRESHOLD is the upper limit (e.g., 5.0)
        if 0.01 < co2_value < Config.CO2_THRESHOLD:
            logging.info(f"CO2 below threshold ({Config.CO2_THRESHOLD}%). Activating CO2 solenoid for {CO2_SOLENOID_ON_TIME}s.")
            # Turn solenoid ON (LOW state for relay)
            success_on = hw_gpio.set_device_state(hw_gpio.CO2_SOLENOID, 'on')
            if success_on:
                time.sleep(CO2_SOLENOID_ON_TIME)
                # Turn solenoid OFF (HIGH state for relay)
                hw_gpio.set_device_state(hw_gpio.CO2_SOLENOID, 'off')
                logging.info("CO2 solenoid OFF.")
            else:
                 logging.error("Failed to turn CO2 solenoid ON.")
        else:
             # Ensure solenoid is off if value is too high or too low (e.g., 0)
             current_state = hw_gpio.get_device_state(hw_gpio.CO2_SOLENOID)
             if current_state != 'off':
                  logging.info(f"CO2 level ({co2_value}%) outside activation range (0.01-{Config.CO2_THRESHOLD}%). Ensuring CO2 solenoid is OFF.")
                  hw_gpio.set_device_state(hw_gpio.CO2_SOLENOID, 'off')
             else:
                  logging.debug(f"CO2 level ({co2_value}%) outside activation range. Solenoid already OFF.")

    except Exception as e:
        logging.error(f"Error in CO2 control logic: {e}", exc_info=True)


# --- Background Thread Loops ---
def _temperature_control_loop():
    """Background thread loop for temperature control."""
    logging.info("Temperature control loop started.")
    while not _stop_event.is_set():
        _control_temperature()
        # Wait for the defined interval, checking stop event periodically
        _stop_event.wait(TEMP_CONTROL_INTERVAL)
    logging.info("Temperature control loop stopped.")

def _co2_control_loop():
    """Background thread loop for CO2 control."""
    logging.info("CO2 control loop started.")
    while not _stop_event.is_set():
        _control_co2()
        # Wait for the defined interval, checking stop event periodically
        _stop_event.wait(CO2_CONTROL_INTERVAL)
    logging.info("CO2 control loop stopped.")


# --- Public Service Functions ---
def start_control_service():
    """Starts the background threads for temperature and CO2 control."""
    global _temp_control_thread, _co2_control_thread
    if (_temp_control_thread and _temp_control_thread.is_alive()) or \
       (_co2_control_thread and _co2_control_thread.is_alive()):
        logging.warning("Control service threads already running.")
        return

    _stop_event.clear()

    # Start Temperature Control Thread
    _temp_control_thread = threading.Thread(target=_temperature_control_loop, daemon=True)
    _temp_control_thread.start()

    # Start CO2 Control Thread
    _co2_control_thread = threading.Thread(target=_co2_control_loop, daemon=True)
    _co2_control_thread.start()

    logging.info("Control service threads started.")

def stop_control_service():
    """Signals the background control threads to stop."""
    logging.info("Stopping control service threads...")
    _stop_event.set()

    threads_to_join = []
    if _temp_control_thread and _temp_control_thread.is_alive():
        threads_to_join.append(_temp_control_thread)
    if _co2_control_thread and _co2_control_thread.is_alive():
        threads_to_join.append(_co2_control_thread)

    for thread in threads_to_join:
        thread.join(timeout=max(TEMP_CONTROL_INTERVAL, CO2_CONTROL_INTERVAL) + 1) # Wait slightly longer than interval
        if thread.is_alive():
             logging.warning(f"Control service thread {thread.name} did not stop gracefully.")

    _temp_control_thread = None
    _co2_control_thread = None
    logging.info("Control service threads stop signal sent.")

# Note: start_control_service() should be called once during application startup.
# stop_control_service() could be called during shutdown (e.g., via atexit).