from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

# Define the Blueprint
main_blueprint = Blueprint('main', __name__)

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
    config_file_path = 'config.txt'

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

    # Render the setup page with current thresholds
    return render_template('setup.html', thresholds=thresholds)

