# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO

login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'super_secret_key'

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
