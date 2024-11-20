from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

#initiate Flask extensions
login_manager = LoginManager()
socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.secret_key = "super_secret_key"  # Replace with a secure key

    # Initialize Socketio extension
    socketio.init_app(app)
    
    #initialize Flask extensions
    login_manager.init_app(app)
    
    #initialize unauthenticated users to login pages
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from .routes import main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
