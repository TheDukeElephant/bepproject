import RPi.GPIO as GPIO
import logging
import atexit

# --- Constants ---
# Device Names (used as keys)
CO2_SOLENOID = 'co2-solenoid'
ARGON_SOLENOID = 'argon-solenoid'
ITO_HEATING = 'ito-heating' # Heater relay
PUMP = 'pump'

# Pin Definitions (BCM numbering)
_DEVICE_PINS = {
    CO2_SOLENOID: 4,
    ARGON_SOLENOID: 17,
    ITO_HEATING: 27,
    'pump-ena': 20,  # PWM Enable for Pump
    'pump-in1': 21,  # Direction Pin 1 for Pump
    'pump-in2': 18   # Direction Pin 2 for Pump (kept LOW for forward)
}

# PWM Configuration
_PWM_FREQUENCY = 100 # Hz
_PUMP_ENA_PIN = _DEVICE_PINS['pump-ena']
_PUMP_IN1_PIN = _DEVICE_PINS['pump-in1']
_PUMP_IN2_PIN = _DEVICE_PINS['pump-in2']

# --- State Variables ---
_pwm_pump = None
_current_pump_speed = 0
_device_states = { # Store the intended state ('on'/'off')
    CO2_SOLENOID: 'off',
    ARGON_SOLENOID: 'off',
    ITO_HEATING: 'off',
    PUMP: 'off'
}

# --- Initialization ---
def setup_gpio():
    """Initializes GPIO pins, sets modes, and configures PWM."""
    global _pwm_pump, _device_states
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup Relays (HIGH = OFF)
        GPIO.setup(_DEVICE_PINS[CO2_SOLENOID], GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(_DEVICE_PINS[ARGON_SOLENOID], GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(_DEVICE_PINS[ITO_HEATING], GPIO.OUT, initial=GPIO.HIGH)

        # Setup Pump Pins
        GPIO.setup(_PUMP_ENA_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(_PUMP_IN1_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(_PUMP_IN2_PIN, GPIO.OUT, initial=GPIO.LOW) # Keep IN2 low for forward

        # Setup Pump PWM
        _pwm_pump = GPIO.PWM(_PUMP_ENA_PIN, _PWM_FREQUENCY)
        _pwm_pump.start(0) # Start with 0% duty cycle (off)
        _current_pump_speed = 0
        _device_states[PUMP] = 'off' # Ensure initial state reflects PWM

        logging.info("GPIO setup complete.")
        atexit.register(cleanup_gpio) # Register cleanup on exit

    except Exception as e:
        logging.error(f"Error initializing GPIO: {e}")
        # Consider raising the exception or handling it more robustly
        raise # Re-raise the exception to indicate failure

# --- Control Functions ---
def set_device_state(device_name, state):
    """
    Sets the state ('on' or 'off') for a specific device.
    Handles relays and the pump motor.
    """
    global _current_pump_speed, _device_states

    if device_name not in _DEVICE_PINS and device_name != PUMP:
        logging.error(f"Invalid device name: {device_name}")
        return False # Indicate failure

    pin = _DEVICE_PINS.get(device_name)
    desired_state_on = (state == 'on')

    try:
        if device_name == PUMP:
            # Control pump motor direction and enable PWM
            GPIO.output(_PUMP_IN1_PIN, GPIO.HIGH if desired_state_on else GPIO.LOW)
            GPIO.output(_PUMP_IN2_PIN, GPIO.LOW) # Keep IN2 low for forward
            # Set speed to 75% when turning on, 0% when turning off
            speed_to_set = 75 if desired_state_on else 0
            _pwm_pump.ChangeDutyCycle(speed_to_set)
            _current_pump_speed = speed_to_set
            _device_states[PUMP] = state
            logging.info(f"Pump set to {state} (Speed: {speed_to_set}%)")

        elif device_name in [CO2_SOLENOID, ARGON_SOLENOID, ITO_HEATING]:
            # Control relays (LOW = ON, HIGH = OFF)
            gpio_state = GPIO.LOW if desired_state_on else GPIO.HIGH
            GPIO.output(pin, gpio_state)
            _device_states[device_name] = state
            logging.info(f"{device_name} set to {state}")
        else:
            logging.warning(f"Device '{device_name}' not directly controllable via set_device_state (might be part of pump).")
            return False

        return True # Indicate success

    except Exception as e:
        logging.error(f"Error setting state for {device_name} to {state}: {e}")
        return False # Indicate failure

def set_pump_speed(speed):
    """Sets the pump speed (PWM duty cycle)."""
    global _current_pump_speed
    try:
        speed = int(speed)
        if not (0 <= speed <= 100):
            raise ValueError("Speed must be between 0 and 100")

        # Only change duty cycle if pump is intended to be 'on'
        if _device_states[PUMP] == 'on' or speed == 0:
             _pwm_pump.ChangeDutyCycle(speed)
             _current_pump_speed = speed
             logging.info(f"Pump speed set to {speed}%")
             # If speed is set to 0, update the state
             if speed == 0:
                 _device_states[PUMP] = 'off'
                 GPIO.output(_PUMP_IN1_PIN, GPIO.LOW) # Ensure direction pin is off
             return True
        else:
            logging.warning(f"Pump is currently off. Cannot set speed to {speed}%. Turn pump on first.")
            return False

    except Exception as e:
        logging.error(f"Error setting pump speed to {speed}: {e}")
        return False

# --- Status Functions ---
def get_device_state(device_name):
    """Gets the current intended state ('on' or 'off') of a device."""
    if device_name in _device_states:
        # Return the tracked state
        return _device_states[device_name]
        # Alternatively, read the actual GPIO state if needed, but might be complex for PWM/relays
        # pin = _DEVICE_PINS.get(device_name)
        # if pin:
        #     # Logic to interpret GPIO.input(pin) based on device type (relay/motor)
        #     pass
    logging.warning(f"Could not get state for unknown device: {device_name}")
    return None # Or raise an error

def get_pump_speed():
    """Gets the current pump speed (PWM duty cycle)."""
    return _current_pump_speed

def get_all_device_states():
    """Returns a dictionary of all tracked device states."""
    # Consider adding actual hardware reads here if necessary for robustness
    return _device_states.copy()

def get_relay_states_for_ui():
     """Gets relay states suitable for UI (interpreting HIGH/LOW)."""
     # This reads the *actual* pin state, which might differ from tracked state briefly
     # during transitions or if external factors change it.
     return {
         CO2_SOLENOID: 'on' if GPIO.input(_DEVICE_PINS[CO2_SOLENOID]) == GPIO.LOW else 'off',
         ARGON_SOLENOID: 'on' if GPIO.input(_DEVICE_PINS[ARGON_SOLENOID]) == GPIO.LOW else 'off',
         ITO_HEATING: 'on' if GPIO.input(_DEVICE_PINS[ITO_HEATING]) == GPIO.LOW else 'off',
     }


# --- Cleanup ---
def cleanup_gpio():
    """Cleans up GPIO resources and stops PWM."""
    global _pwm_pump
    logging.info("Cleaning up GPIO resources...")
    if _pwm_pump:
        try:
            _pwm_pump.stop()
            logging.info("PWM stopped.")
        except Exception as e:
            logging.error(f"Error stopping PWM: {e}")
    try:
        GPIO.cleanup()
        logging.info("GPIO cleanup finished.")
    except Exception as e:
        logging.error(f"Error during GPIO cleanup: {e}")

# Note: setup_gpio() should be called once during application startup (e.g., in run.py).
# The atexit registration is now handled within setup_gpio().