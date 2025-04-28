# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import Config  # Import the Config class

login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # Load config from Config object

    # Initialize extensions
    login_manager.init_app(app)
    socketio.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes import main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/')

    from app.auth import auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
