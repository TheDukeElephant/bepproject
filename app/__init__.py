from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

socketio = SocketIO()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = "super_secret_key"  # Replace with a secure key

    # Initialize extensions
    socketio.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from .routes import main_blueprint
    from .auth import auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
