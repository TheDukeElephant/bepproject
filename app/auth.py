from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, current_user
from .database import authenticate_user
from . import login_manager  # Import the login_manager instance

auth_blueprint = Blueprint('auth', __name__)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('main.index'))
        return "Invalid credentials", 401
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('login.html')

@auth_blueprint.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
