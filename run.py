import logging
import sys
from config import Config # Config handles its own logging init now

# --- Initialize Logging ---
# Logging should be configured early, potentially via Config or here
# Assuming Config.init_logging() in config.py handles it.
# If not, uncomment and configure here:
# logging.basicConfig(format=Config.LOG_FORMAT, level=logging.INFO)

# --- Import App Components ---
try:
    from app import create_app, socketio
    from app.database import init_db
    from wifi_monitor import start_wifi_monitor # Keep if still used
    # Import Hardware Modules
    from app.hardware import gpio_devices as hw_gpio
    from app.hardware import sensors as hw_sensors
    from app.hardware import display as hw_display
    from app.hardware import serial_comms as hw_serial
    # Import Service Modules
    from app.services import datalog_service
    from app.services import sensor_service
    from app.services import control_service
except ModuleNotFoundError as e:
    # Log critical error and exit if core components are missing
    logging.critical(f"Error importing core modules: {e}", exc_info=True)
    sys.exit(f"Failed to import core modules: {e}")
except Exception as e:
    logging.critical(f"Unexpected error during imports: {e}", exc_info=True)
    sys.exit(f"Unexpected error during imports: {e}")


# --- Initialize Hardware and Services ---
# It's crucial to initialize hardware *before* creating the app
# if app creation depends on hardware state, or before starting services.
try:
    logging.info("Initializing hardware...")
    hw_gpio.setup_gpio() # Handles GPIO setup and atexit cleanup registration
    hw_sensors.initialize_sensors()
    hw_display.initialize_display() # Handles display init and atexit cleanup
    hw_serial.initialize_co2_sensor() # Handles serial init and atexit cleanup
    logging.info("Hardware initialization complete.")

    logging.info("Initializing services...")
    datalog_service.initialize_datalog()
    logging.info("Services initialization complete.")

except Exception as e:
    # Log critical error and exit if hardware/service init fails
    logging.critical(f"Failed during hardware/service initialization: {e}", exc_info=True)
    # Optionally try to cleanup GPIO/Display if partially initialized before exiting
    hw_display.display_standby() # Show standby message if possible
    hw_gpio.cleanup_gpio()
    hw_serial.close_serial_port()
    sys.exit(f"Failed during hardware/service initialization: {e}")


# --- Create Flask App ---
# Now create the app after hardware/services are ready (if needed)
app = create_app()

# --- Initialize Database ---
# Init DB after app creation if it depends on the app context
with app.app_context():
     try:
          init_db()
          logging.info("Database initialized.")
     except Exception as e:
          logging.critical(f"Failed to initialize database: {e}", exc_info=True)
          sys.exit(f"Failed to initialize database: {e}")


# --- Register SocketIO Handlers ---
# Must be done after socketio object is created (in create_app)
try:
    sensor_service.register_socketio_handlers(socketio)
    logging.info("SocketIO handlers registered.")
except Exception as e:
    logging.error(f"Failed to register SocketIO handlers: {e}", exc_info=True)
    # Decide if this is critical enough to exit


# --- Main Execution ---
if __name__ == "__main__":
    logging.info("Starting background services...")
    try:
        # Start the new background services (threads)
        sensor_service.start_sensor_service()
        control_service.start_control_service()
        # Start other background tasks like Wi-Fi monitor if needed
        start_wifi_monitor()
        logging.info("Background services started.")
    except Exception as e:
        logging.critical(f"Failed to start background services: {e}", exc_info=True)
        sys.exit(f"Failed to start background services: {e}")

    logging.info("Starting Flask-SocketIO server...")
    try:
        # Run the Flask-SocketIO server
        # use_reloader=False is important for background threads/hardware access
        socketio.run(app, host="0.0.0.0", port=5000, debug=Config.SECRET_KEY == 'fallback_key_for_dev', use_reloader=False)
    except Exception as e:
        logging.critical(f"Error running Flask-SocketIO server: {e}", exc_info=True)
        # Consider stopping background threads gracefully here before exiting
        sensor_service.stop_sensor_service()
        control_service.stop_control_service()
        sys.exit(f"Error running Flask-SocketIO server: {e}")
