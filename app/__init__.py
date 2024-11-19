from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO

# Extensions
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'super_secret_key'  # Replace with environment variable in production

    # Initialize extensions
    login_manager.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    from .routes import main_blueprint
    from .auth import auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
