from app import create_app, socketio
#from app import create_app
from app.background import background_co2_read
from app.database import init_db

# Initialize the app
app = create_app()

# Initialize the database
init_db()

# Start background tasks
socketio.start_background_task(target=background_co2_read)

if __name__ == "__main__":
    print("Starting Flask application...")
    #socketio.run(app, host="172.20.10.11", port=5000)
    socketio.run(app, host="0.0.0.0", port=5000)
    #app.run(host="0.0.0.0", port=5000)
