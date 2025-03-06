from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import RPi.GPIO as GPIO
import atexit
import logging
from config import Config  # Updated import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the Blueprint
main_blueprint = Blueprint('main', __name__)

# Initialize GPIO
try:
    GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
    GPIO.setwarnings(False)
except Exception as e:
    logging.error(f"Error initializing GPIO: {e}")

# Define device pin mappings
device_pins = {
    # Relays
    'co2-solenoid': 4,         # GPIO 4: Relay 1 for CO2 solenoid
    'argon-solenoid': 17,      # GPIO 17: Relay 2 for Argon solenoid
    'humidifier': 27,          # GPIO 27: Relay 3 for humidifier
    'humidifier2': 24,          # GPIO 27: Relay 3 for humidifier
    'oxygen-sensor': 5,        # GPIO pin for the oxygen sensor

    # Motor driver connections for pump
    #'pump': 20,
    'pump-ena': 20,            # GPIO 20: ENA for pump (PWM)
    'pump-in1': 21,            # GPIO 21: IN1 for pump (forward direction)
    'pump-in2': 18,            # GPIO 18: IN2 for pump (reverse direction, keep LOW for forward)

    # Motor driver connections for ITO heating elements
    #'ito-top': 22,
    'ito-top-ena': 22,         # GPIO 22: ENA for ITO top (PWM)
    'ito-top-in1': 23,         # GPIO 23: IN1 for ITO top
    'ito-top-in2': 1,         # GPIO 24: IN2 for ITO top
    #'ito-bottom': 16,
    'ito-bottom-ena': 16,      # GPIO 16: ENA for ITO bottom (PWM)
    'ito-bottom-in3': 25,      # GPIO 25: IN3 for ITO bottom
    'ito-bottom-in4': 12       # GPIO 12: IN4 for ITO bottom
}

# Validate and set all pins as output and initialize to OFF
for device, pin in device_pins.items():
    try:
        if not isinstance(pin, int):
            raise ValueError(f"Pin value for '{device}' must be an integer, got {pin}")
        logging.info(f"Setting up GPIO pin {pin} for {device}")
        GPIO.setup(pin, GPIO.OUT)
        if 'solenoid' in device or 'humidifier' in device or 'humidifier2' in device:
            GPIO.output(pin, GPIO.HIGH)  # Ensure relays are OFF (HIGH is the off state for most relays)
        else:
            GPIO.output(pin, GPIO.LOW)  # Default LOW for motor drivers
    except Exception as e:
        logging.error(f"Error setting up GPIO for {device}: {e}")

# Store PWM instances
pwm_instances = {}
pwm_pins = ['pump-ena', 'ito-top-ena', 'ito-bottom-ena']  # Pins requiring PWM
for pwm_device in pwm_pins:
    pin = device_pins[pwm_device]
    pwm_instances[pwm_device] = GPIO.PWM(pin, 100)  # 100 Hz frequency
    pwm_instances[pwm_device].start(0)  # Start with 0% duty cycle

# Store current duty cycles in memory so we can reflect them accurately on the Setup page
current_pwm_duty_cycle = {
    'pump-ena': 50,
    'ito-top-ena': 50,
    'ito-bottom-ena': 50
}

# Ensure GPIO cleanup on application exit
def cleanup_gpio():
    """Clean up all GPIO resources and stop PWM."""
    for pwm in pwm_instances.values():
        pwm.stop()
    GPIO.cleanup()


atexit.register(cleanup_gpio)


@main_blueprint.route('/toggle-device', methods=['POST'])
@login_required
def toggle_device():
    """Toggle a relay or GPIO pin."""
    try:
        data = request.json
        device = data.get('device')
        state = data.get('state')  # 'on' or 'off'

        if device not in device_pins and device not in ['pump', 'ito-top', 'ito-bottom']:
            return {'error': f"Invalid device: {device}"}, 400

        if device == 'pump':
            GPIO.output(device_pins['pump-in1'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['pump-in2'], GPIO.LOW)
            if state == 'off':
                pwm_instances['pump-ena'].ChangeDutyCycle(0)
                current_pwm_duty_cycle['pump-ena'] = 0
        elif device == 'ito-top':
            GPIO.output(device_pins['ito-top-in1'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['ito-top-in2'], GPIO.LOW)
            if state == 'off':
                pwm_instances['ito-top-ena'].ChangeDutyCycle(0)
                current_pwm_duty_cycle['ito-top-ena'] = 0
        elif device == 'ito-bottom':
            GPIO.output(device_pins['ito-bottom-in3'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['ito-bottom-in4'], GPIO.LOW)
            if state == 'off':
                pwm_instances['ito-bottom-ena'].ChangeDutyCycle(0)
                current_pwm_duty_cycle['ito-bottom-ena'] = 0
        else:
            pin = device_pins[device]
            GPIO.output(pin, GPIO.LOW if state == 'on' else GPIO.HIGH)

        logging.info("Device %s toggled to %s", device, state)
        return {'status': 'success', 'device': device, 'state': state}
    except Exception as e:
        logging.error("Error toggling device: %s", e)
        return {'error': str(e)}, 500


@main_blueprint.route('/set-device-speed', methods=['POST'])
@login_required
def set_device_speed():
    """Set the speed for a PWM device."""
    try:
        data = request.json
        device = data.get('device')
        speed = int(data.get('speed'))

        if device not in pwm_pins:
            return {'error': f"Device {device} does not support speed control"}, 400

        pwm_instances[device].ChangeDutyCycle(speed)
        current_pwm_duty_cycle[device] = speed  # Store current duty cycle in memory

        return {'status': 'success', 'device': device, 'speed': speed}
    except Exception as e:
        logging.error(f"Error setting device speed: {e}")
        return {'error': str(e)}, 500


@main_blueprint.route('/')
@login_required
def index():
    # Redirect logged-in users to the dashboard
    return redirect(url_for('main.dashboard'))


@main_blueprint.route('/dashboard')
@login_required
def dashboard():
    # Render the dashboard page
    return render_template('dashboard.html')


@main_blueprint.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Handle the setup page for configuring thresholds and device states."""
    config_file_path = 'config.txt'

    # Relay states to synchronize UI with hardware
    relay_states = {device: GPIO.input(pin) for device, pin in device_pins.items() if 'solenoid' in device or 'humidifier' in device or 'humidifier2' in device}

    # Initialize device states and speeds
    device_states = {
        'pump': 'off',
        'pump_speed': 50,
        'ito-top': 'off',
        'ito-top_speed': 50,
        'ito-bottom': 'off',
        'ito-bottom_speed': 50
    }

    if request.method == 'POST':
        # Handle the setup form submission
        co2_threshold = request.form.get('co2_threshold')
        o2_threshold = request.form.get('o2_threshold')
        temp_threshold = request.form.get('temp_threshold')
        humidity_threshold = request.form.get('humidity_threshold')

        # Save thresholds and device states to config file
        try:
            with open(config_file_path, 'w') as config_file:
                config_file.write(f"co2_threshold={round(float(co2_threshold), 1)}\n")
                config_file.write(f"o2_threshold={round(float(o2_threshold), 1)}\n")
                config_file.write(f"temp_threshold={round(float(temp_threshold), 1)}\n")
                config_file.write(f"humidity_threshold={round(float(humidity_threshold), 1)}\n")
                config_file.write(f"pump_state={request.form.get('pump_state')}\n")
                config_file.write(f"pump_speed={request.form.get('pump_speed')}\n")
                config_file.write(f"ito_top_state={request.form.get('ito_top_state')}\n")
                config_file.write(f"ito_top_speed={request.form.get('ito_top_speed')}\n")
                config_file.write(f"ito_bottom_state={request.form.get('ito_bottom_state')}\n")
                config_file.write(f"ito_bottom_speed={request.form.get('ito_bottom_speed')}\n")
            flash("Settings saved successfully!", "success")
        except Exception as e:
            flash(f"Error saving settings: {e}", "error")

        # Redirect back to the dashboard after form submission
        return redirect(url_for('main.dashboard'))

    # For GET requests, load existing thresholds and device states from config.txt
    thresholds = {
        "co2_threshold": 0.0,
        "o2_threshold": 0.0,
        "temp_threshold": 0.0,
        "humidity_threshold": 0.0
    }

    try:
        with open(config_file_path, 'r') as config_file:
            for line in config_file:
                key, value = line.strip().split('=')
                if key in thresholds:
                    thresholds[key] = round(float(value), 1)  # Round to 1 decimal place
                elif key in device_states:
                    device_states[key] = value if 'state' in key else int(value)
    except FileNotFoundError:
        flash("No configuration file found. Please set thresholds.", "info")
    except Exception as e:
        flash(f"Error reading configuration: {e}", "error")

    # Update device states based on actual GPIO pin states
    device_states['pump'] = 'on' if GPIO.input(device_pins['pump-in1']) == GPIO.HIGH else 'off'
    device_states['ito-top'] = 'on' if GPIO.input(device_pins['ito-top-in1']) == GPIO.HIGH else 'off'
    device_states['ito-bottom'] = 'on' if GPIO.input(device_pins['ito-bottom-in3']) == GPIO.HIGH else 'off'

    # Read the actual PWM speeds
    device_states['pump_speed'] = current_pwm_duty_cycle['pump-ena']
    device_states['ito_top_speed'] = current_pwm_duty_cycle['ito-top-ena']
    device_states['ito_bottom_speed'] = current_pwm_duty_cycle['ito-bottom-ena']

    # Pass GPIO states and device states to the template
    return render_template(
        'setup.html',
        thresholds=thresholds,
        relay_states=relay_states,
        device_states=device_states,
        GPIO_LOW=GPIO.LOW,
        GPIO_HIGH=GPIO.HIGH
    )
