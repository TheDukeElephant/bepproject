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
    if request.method == 'POST':
        # Handle the setup form submission
        co2_threshold = request.form.get('co2_threshold')
        o2_threshold = request.form.get('o2_threshold')
        temp_threshold = request.form.get('temp_threshold')
        humidity_threshold = request.form.get('humidity_threshold')

        try:
            # Save the threshold values to config.txt
            with open('config.txt', 'w') as config_file:
                config_file.write(f"co2_threshold={co2_threshold}\n")
                config_file.write(f"o2_threshold={o2_threshold}\n")
                config_file.write(f"temp_threshold={temp_threshold}\n")
                config_file.write(f"humidity_threshold={humidity_threshold}\n")
            
            flash("Thresholds saved successfully!", "success")
        except Exception as e:
            flash(f"Error saving thresholds: {e}", "error")
        
        # Redirect back to the dashboard after form submission
        return redirect(url_for('main.dashboard'))

    # Render the setup page for GET requests
    return render_template('setup.html')
