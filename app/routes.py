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
        threshold = request.form.get('threshold')
        try:
            # Save the threshold value (example logic, replace with actual saving mechanism)
            with open('config.txt', 'w') as config_file:
                config_file.write(f"threshold={threshold}")
            flash("Threshold saved successfully!", "success")
        except Exception as e:
            flash(f"Error saving threshold: {e}", "error")
        # Redirect back to the dashboard after form submission
        return redirect(url_for('main.dashboard'))
    # Render the setup page for GET requests
    return render_template('setup.html')
