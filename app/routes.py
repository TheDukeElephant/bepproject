from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
@login_required
def index():
    # Redirect to login if the user is not authenticated
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('index.html')
