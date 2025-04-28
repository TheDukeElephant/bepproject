# BEP Project: Environmental Control Box

## Overview

This project implements a control system for an environmental chamber designed for transporting living cells. It utilizes a Flask web application running on a Raspberry Pi to monitor and regulate temperature, humidity, CO2, and O2 levels within the chamber. The system provides a web-based dashboard for real-time monitoring and control, along with user authentication.

## Features

*   **Real-time Monitoring:** View current temperature, humidity, CO2, and O2 levels via a web dashboard.
*   **Environmental Control:** Automatically adjusts internal conditions based on configurable thresholds using connected actuators.
*   **Web Interface:** User-friendly dashboard built with Flask, HTML, CSS, and JavaScript.
*   **User Authentication:** Secure login system to restrict access.
*   **Data Logging:** (Assumed based on `datalog_service.py`) Logs sensor data over time.
*   **Hardware Integration:** Interfaces with various sensors and actuators via GPIO and serial communication.
*   **OLED Display:** Shows the device's IP address for easy network access.
*   **Wi-Fi Management:** Includes a monitor script (`wifi_monitor.py`) for automatic reconnection.

## Architecture

The application follows a modular structure:

*   **`run.py`:** Main entry point to start the Flask application.
*   **`config.py`:** Stores configuration settings like sensor thresholds and hardware pins.
*   **`app/`:** Core application package.
    *   **`__init__.py`:** Initializes the Flask app and extensions (e.g., SocketIO, Database).
    *   **`routes.py`:** Defines web page routes and API endpoints.
    *   **`auth.py`:** Handles user login and authentication logic.
    *   **`database.py`:** Manages database interactions (likely SQLite via `users.db`).
    *   **`sockets.py`:** Handles WebSocket communication for real-time updates.
    *   **`background.py`:** Runs background tasks like sensor reading and control loops.
    *   **`hardware/`:** Modules for interfacing with specific hardware components:
        *   `sensors.py`: Reads data from various sensors.
        *   `gpio_devices.py`: Controls devices connected via GPIO (e.g., heaters, fans).
        *   `display.py`: Manages the OLED display.
        *   `serial_comms.py`: Handles serial communication (e.g., for CO2/O2 sensors).
    *   **`services/`:** High-level services coordinating application logic:
        *   `sensor_service.py`: Aggregates and processes sensor data.
        *   `control_service.py`: Implements the control logic based on sensor readings and setpoints.
        *   `datalog_service.py`: Manages the logging of sensor data.
    *   **`static/`:** Contains CSS stylesheets and JavaScript files for the frontend.
    *   **`templates/`:** HTML templates for the web interface (Login, Setup, Dashboard).
*   **`requirements.txt`:** Lists Python package dependencies.
*   **`wifi_monitor.py`:** Standalone script to ensure Wi-Fi connectivity.
*   **`tests/`:** Contains test scripts (e.g., `display_ip.py`).

## Hardware Requirements (Example - Needs Verification)

*   Raspberry Pi (Model 3B+ or newer recommended)
*   Temperature/Humidity Sensor (e.g., DHT22, BME280)
*   CO2 Sensor (e.g., MH-Z19) - Likely connected via Serial/UART
*   O2 Sensor (e.g., DFRobot Gravity Analog Oxygen Sensor) - Requires ADC if analog
*   Relays or Motor Drivers for controlling heaters, fans, valves.
*   OLED Display (e.g., SSD1306) - Connected via I2C
*   Power Supply
*   Enclosure/Box

*(Please update this section with the specific hardware used in the project)*

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd bepproject
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure system dependencies for libraries like RPi.GPIO are met.*
3.  **Configure Hardware:** Connect all sensors, actuators, and the display to the Raspberry Pi according to the pin configurations defined (or intended to be defined) in `config.py` and the `app/hardware/` modules.
4.  **Configure Settings:** Edit `config.py` to set:
    *   Sensor calibration values (if any).
    *   Control thresholds (target temperature, humidity, CO2, O2 levels).
    *   GPIO pin assignments for actuators and sensors.
    *   Serial port details for relevant sensors.
    *   I2C address for the OLED display.
5.  **Initialize Database (if needed):** There might be a command or initial setup step required for `users.db`. (Check `database.py` or `run.py`).
6.  **Run the Application:**
    ```bash
    sudo python run.py
    ```
    *(Using `sudo` might be necessary for GPIO access)*
7.  **Access the Dashboard:** Open a web browser and navigate to `http://<your-pi-ip>:5000`. The IP address should be shown on the OLED display shortly after startup.

## Running Background Scripts

*   **Wi-Fi Monitor:** This script (`wifi_monitor.py`) can be run separately or integrated to run automatically (e.g., via systemd) to maintain network connectivity:
    ```bash
    python wifi_monitor.py
    ```

## Configuration (`config.py`)

This file centralizes key settings:

*   `SECRET_KEY`: For Flask session security.
*   `DATABASE_URI`: Path to the user database.
*   **Sensor/Control Thresholds:** Target values for temperature, humidity, CO2, O2.
*   **Pin Definitions:** GPIO pins used for relays, sensors, etc.
*   **Serial Port Settings:** Device path and baud rate for serial sensors.
*   **I2C Settings:** Address for the OLED display.
*   **(Other settings...)**

*(Review `config.py` for all available options)*

## Testing

The `tests/` directory contains scripts for testing specific components. For example, `display_ip.py` likely tests the OLED display functionality. Add more tests as needed to ensure reliability.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
