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
    'co2-solenoid': 4,         # GPIO 4: Relay for CO2 solenoid
    'argon-solenoid': 17,      # GPIO 17: Relay for Argon solenoid
    
    # Renamed "humidifier" to "ito-heating"
    'ito-heating': 27,         # GPIO 27: Reused for ITO heating
    
    # Sensors
    'oxygen-sensor': 5,        # GPIO pin for the oxygen sensor
    
    # Motor driver connections for pump (kept)
    'pump-ena': 20,            # GPIO 20: ENA for pump (PWM)
    'pump-in1': 21,            # GPIO 21: IN1
    'pump-in2': 18             # GPIO 18: IN2 (kept LOW for forward)
}

# Validate and set all pins as output and initialize to OFF
for device, pin in device_pins.items():
    try:
        if not isinstance(pin, int):
            raise ValueError(f"Pin value for '{device}' must be an integer, got {pin}")
        logging.info(f"Setting up GPIO pin {pin} for {device}")
        GPIO.setup(pin, GPIO.OUT)
        if 'solenoid' in device or 'ito-heating' in device:
            GPIO.output(pin, GPIO.HIGH)  # Ensure relays are OFF (HIGH is the off state for most relays)
        else:
            GPIO.output(pin, GPIO.LOW)  # Default LOW for motor drivers
    except Exception as e:
        logging.error(f"Error setting up GPIO for {device}: {e}")

# Store PWM instances
pwm_instances = {}
pwm_pins = ['pump-ena']  # Only the pump uses PWM now
pwm_instances['pump-ena'] = GPIO.PWM(device_pins['pump-ena'], 100)
pwm_instances['pump-ena'].start(0)

current_pwm_duty_cycle = {
    'pump-ena': 0  # We'll set it to 75% only when pump is on
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
    """Toggle a relay or GPIO pin (pump, ito-heating, co2-solenoid, argon-solenoid)."""
    try:
        data = request.json
        device = data.get('device')
        state = data.get('state')  # 'on' or 'off'

        if device not in device_pins and device not in ['pump']:
            return {'error': f"Invalid device: {device}"}, 400

        if device == 'pump':
            # On => set pump to 75% speed
            GPIO.output(device_pins['pump-in1'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['pump-in2'], GPIO.LOW)
            pwm_instances['pump-ena'].ChangeDutyCycle(75 if state == 'on' else 0)
            current_pwm_duty_cycle['pump-ena'] = 75 if state == 'on' else 0
        elif device == 'ito-heating':
            # Relay: LOW = ON, HIGH = OFF
            pin = device_pins['ito-heating']
            GPIO.output(pin, GPIO.LOW if state == 'on' else GPIO.HIGH)
        else:
            # Generic relay toggles
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
    relay_states = {
        'co2-solenoid': GPIO.input(device_pins['co2-solenoid']),
        'argon-solenoid': GPIO.input(device_pins['argon-solenoid']),
        'ito-heating': GPIO.input(device_pins['ito-heating'])
    }

    # Initialize device states and speeds
    device_states = {
        'pump': 'off'
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

    # Read the actual PWM speeds
    device_states['pump_speed'] = current_pwm_duty_cycle['pump-ena']

    # Pass GPIO states and device states to the template
    return render_template(
        'setup.html',
        thresholds=thresholds,
        relay_states=relay_states,
        device_states=device_states,
        GPIO_LOW=GPIO.LOW,
        GPIO_HIGH=GPIO.HIGH
    )
