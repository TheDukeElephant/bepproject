from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import logging
from config import Config
from app.hardware import gpio_devices as hw_gpio # Import the new hardware module

# Configure logging (can be done once in run.py or app factory)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the Blueprint
main_blueprint = Blueprint('main', __name__)

# NOTE: GPIO initialization and cleanup are now handled within hw_gpio module
# and should be called from run.py


@main_blueprint.route('/toggle-device', methods=['POST'])
@login_required
def toggle_device():
    """Toggle a device state using the hardware abstraction layer."""
    try:
        data = request.json
        device_name = data.get('device') # e.g., 'pump', 'co2-solenoid'
        state = data.get('state')  # 'on' or 'off'

        if state not in ['on', 'off']:
             return {'error': "Invalid state. Must be 'on' or 'off'."}, 400

        # Use the hardware module function
        success = hw_gpio.set_device_state(device_name, state)

        if success:
            logging.info(f"API: Device '{device_name}' toggled to {state}")
            return {'status': 'success', 'device': device_name, 'state': state}
        else:
            # The hardware module logs the specific error
            logging.error(f"API: Failed to toggle device '{device_name}' to {state}")
            # Check if the device name itself was invalid vs. a hardware issue
            if device_name not in [hw_gpio.PUMP, hw_gpio.CO2_SOLENOID, hw_gpio.ARGON_SOLENOID, hw_gpio.ITO_HEATING]:
                 return {'error': f"Invalid device name: {device_name}"}, 400
            else:
                 return {'error': f"Failed to set state for device '{device_name}'"}, 500

    except Exception as e:
        logging.error(f"API Error in /toggle-device: {e}", exc_info=True)
        return {'error': 'An internal server error occurred'}, 500


@main_blueprint.route('/set-device-speed', methods=['POST'])
@login_required
def set_device_speed():
    """Set the speed for the pump."""
    try:
        data = request.json
        # Assuming speed control is only for the pump now
        device = data.get('device') # Keep for potential future use, but validate
        speed_str = data.get('speed')

        if device != hw_gpio.PUMP:
             return {'error': f"Speed control only supported for device '{hw_gpio.PUMP}'"}, 400

        if speed_str is None:
             return {'error': "Missing 'speed' parameter"}, 400

        try:
             speed = int(speed_str)
             if not (0 <= speed <= 100):
                  raise ValueError("Speed must be between 0 and 100")
        except ValueError as e:
             return {'error': f"Invalid speed value: {e}"}, 400

        # Use the hardware module function
        success = hw_gpio.set_pump_speed(speed)

        if success:
            logging.info(f"API: Pump speed set to {speed}%")
            return {'status': 'success', 'device': hw_gpio.PUMP, 'speed': speed}
        else:
            # Hardware module logs details
            logging.error(f"API: Failed to set pump speed to {speed}%")
            # Check if pump is off as a possible reason
            if hw_gpio.get_device_state(hw_gpio.PUMP) == 'off' and speed > 0:
                 return {'error': 'Cannot set speed while pump is off. Turn pump on first.'}, 409 # Conflict
            else:
                 return {'error': 'Failed to set pump speed'}, 500

    except Exception as e:
        logging.error(f"API Error in /set-device-speed: {e}", exc_info=True)
        return {'error': 'An internal server error occurred'}, 500


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
@main_blueprint.route('/setup', methods=['GET']) # Only handle GET requests now
@login_required
def setup():
    """Display the setup page with current thresholds from config and device states."""

    # Get current device states from the hardware layer
    try:
        # Use the specific UI helper for relays if it interprets LOW/HIGH correctly
        relay_states = hw_gpio.get_relay_states_for_ui()

        # Get pump state and speed
        pump_state = hw_gpio.get_device_state(hw_gpio.PUMP)
        pump_speed = hw_gpio.get_pump_speed()

        device_states = {
            hw_gpio.PUMP: pump_state if pump_state is not None else 'unknown',
            'pump_speed': pump_speed if pump_speed is not None else 'unknown'
        }

    except Exception as e:
        # Handle potential errors during hardware communication at startup/refresh
        logging.error(f"Error getting device states for setup page: {e}", exc_info=True)
        flash("Error retrieving current device states.", "error")
        # Provide default/error states to prevent template errors
        relay_states = { hw_gpio.CO2_SOLENOID: 'error', hw_gpio.ARGON_SOLENOID: 'error', hw_gpio.ITO_HEATING: 'error' }
        device_states = { hw_gpio.PUMP: 'error', 'pump_speed': 'error' }


    # Fetch thresholds from Config object
    thresholds = {
        "co2_threshold": Config.CO2_THRESHOLD,
        "o2_threshold": Config.O2_THRESHOLD, # Note: O2 control not implemented yet
        "temp_lower_bound": Config.TEMP_LOWER_BOUND,
        "temp_upper_bound": Config.TEMP_UPPER_BOUND,
        # Add other relevant config values if needed by the template
    }

    # Pass data to the template
    # Ensure the template 'setup.html' uses the correct keys
    # (e.g., hw_gpio.PUMP constant value or the string 'pump')
    return render_template(
        'setup.html',
        thresholds=thresholds,
        relay_states=relay_states,
        device_states=device_states,
        # Pass constants if template needs them (e.g., for data-device attributes)
        DEVICE_NAMES=hw_gpio # Pass the whole module or specific constants
    )
