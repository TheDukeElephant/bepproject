from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import RPi.GPIO as GPIO
import atexit

# Define the Blueprint
main_blueprint = Blueprint('main', __name__)

# Initialize GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setwarnings(False)

# Define device pin mappings
device_pins = {
    # Relays
    'co2-solenoid': 4,         # GPIO 4: Relay 1 for CO2 solenoid
    'argon-solenoid': 17,      # GPIO 17: Relay 2 for Argon solenoid
    'humidifier': 27,          # GPIO 27: Relay 3 for humidifier

    # Motor driver connections for pump
    'pump': 20,
    'pump-ena': 20,            # GPIO 20: ENA for pump (PWM)
    'pump-in1': 21,            # GPIO 21: IN1 for pump (forward direction)
    'pump-in2': 18,            # GPIO 18: IN2 for pump (reverse direction, keep LOW for forward)

    # Motor driver connections for ITO heating elements
    'ito-top': 22,
    'ito-top-ena': 22,         # GPIO 22: ENA for ITO top (PWM)
    'ito-top-in1': 23,         # GPIO 23: IN1 for ITO top
    'ito-top-in2': 24,         # GPIO 24: IN2 for ITO top
    'ito-bottom': 16,
    'ito-bottom-ena': 16,      # GPIO 16: ENA for ITO bottom (PWM)
    'ito-bottom-in3': 25,      # GPIO 25: IN3 for ITO bottom
    'ito-bottom-in4': 12       # GPIO 12: IN4 for ITO bottom
}

# Set all pins as output and initialize to OFF
#for pin in device_pins.values():
#    GPIO.setup(pin, GPIO.OUT)
#    GPIO.output(pin, GPIO.LOW)
# Set all pins as output and initialize relays to OFF (HIGH state)
for pin, name in device_pins.items():
    GPIO.setup(pin, GPIO.OUT)
    if 'relay' in name or 'solenoid' in name or 'humidifier' in name:
        GPIO.output(pin, GPIO.HIGH)  # OFF state for the relay
    else:
        GPIO.output(pin, GPIO.LOW)  # Default LOW for motor drivers

# Store PWM instances
pwm_instances = {}
pwm_pins = ['pump-ena', 'ito-top-ena', 'ito-bottom-ena']  # Pins requiring PWM
for pwm_device in pwm_pins:
    pin = device_pins[pwm_device]
    pwm_instances[pwm_device] = GPIO.PWM(pin, 100)  # 100 Hz frequency
    pwm_instances[pwm_device].start(0)  # Start with 0% duty cycle


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
        state = data.get('state')

        # Debugging logs
        print(f"Received toggle request: Device={device}, State={state}")

        if device not in device_pins:
            print(f"Invalid device name received: {device}")  # Log the invalid device
            return {'error': f"Invalid device: {device}"}, 400

        # Get the pin number for the device
        if device == 'pump':
            # Handle the pump's motor driver
            GPIO.output(device_pins['pump-in1'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['pump-in2'], GPIO.LOW)  # Keep IN2 LOW for forward
        elif device == 'ito-top':
            # Handle ITO top motor driver
            GPIO.output(device_pins['ito-top-in1'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['ito-top-in2'], GPIO.LOW)  # Keep IN2 LOW for forward
        elif device == 'ito-bottom':
            # Handle ITO bottom motor driver
            GPIO.output(device_pins['ito-bottom-in3'], GPIO.HIGH if state == 'on' else GPIO.LOW)
            GPIO.output(device_pins['ito-bottom-in4'], GPIO.LOW)  # Keep IN4 LOW for forward
        else:
            # Handle simple relay devices
            pin = device_pins[device]
            GPIO.output(pin, GPIO.LOW if state == 'on' else GPIO.HIGH)

        print(f"Device {device} toggled to {'ON' if state == 'on' else 'OFF'}")  # Debugging log
        return {'status': 'success', 'device': device, 'state': state}
    except Exception as e:
        print(f"Error toggling device: {e}")  # Debugging log for exceptions
        return {'error': str(e)}, 500


@main_blueprint.route('/set-device-speed', methods=['POST'])
@login_required
def set_device_speed():
    """Set the speed for a PWM device."""
    try:
        data = request.json
        device = data.get('device')
        speed = int(data.get('speed'))  # Speed should be an integer 0-100

        if device not in pwm_pins:
            return {'error': f"Device {device} does not support speed control"}, 400

        # Adjust the PWM duty cycle
        pwm_instances[device].ChangeDutyCycle(speed)

        return {'status': 'success', 'device': device, 'speed': speed}
    except Exception as e:
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
    """Handle the setup page for configuring thresholds."""
    config_file_path = 'config.txt'

    # Relay states to synchronize UI with hardware
    relay_states = {device: GPIO.input(pin) for device, pin in device_pins.items() if 'solenoid' in device or 'humidifier' in device}

    if request.method == 'POST':
        # Handle the setup form submission
        co2_threshold = request.form.get('co2_threshold')
        o2_threshold = request.form.get('o2_threshold')
        temp_threshold = request.form.get('temp_threshold')
        humidity_threshold = request.form.get('humidity_threshold')

        try:
            with open(config_file_path, 'w') as config_file:
                config_file.write(f"co2_threshold={round(float(co2_threshold), 1)}\n")
                config_file.write(f"o2_threshold={round(float(o2_threshold), 1)}\n")
                config_file.write(f"temp_threshold={round(float(temp_threshold), 1)}\n")
                config_file.write(f"humidity_threshold={round(float(humidity_threshold), 1)}\n")
            flash("Thresholds saved successfully!", "success")
        except Exception as e:
            flash(f"Error saving thresholds: {e}", "error")

        # Redirect back to the dashboard after form submission
        return redirect(url_for('main.dashboard'))

    # For GET requests, load existing thresholds from config.txt
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
                if key in {"co2_threshold", "o2_threshold", "temp_threshold", "humidity_threshold"}:
                    thresholds[key] = round(float(value), 1)  # Round to 1 decimal place
    except FileNotFoundError:
        flash("No configuration file found. Please set thresholds.", "info")
    except Exception as e:
        flash(f"Error reading configuration: {e}", "error")

    # Render the setup page with current thresholds and relay states
    return render_template('setup.html', thresholds=thresholds, relay_states=relay_states)
