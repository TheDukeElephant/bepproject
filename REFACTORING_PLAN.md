# Refactoring Plan: Portable Cell Culture Incubator Flask App

This document outlines the plan to refactor the Flask application for the portable cell culture incubator. The goal is to improve structure, maintainability, testability, and robustness by separating concerns and following best practices.

**Approved Plan:**

1.  **Project Structure Cleanup:**
    *   Remove the `app/old/` directory and its contents.
    *   Create new directories within `app/`:
        *   `app/hardware/`: For abstracting hardware interactions (GPIO, sensors, display).
        *   `app/services/`: For background tasks like sensor reading, control loops, and data logging.
        *   `app/utils/`: (Optional) For shared utility functions if needed.

2.  **Centralize Configuration:**
    *   Modify `app/__init__.py`: Remove the hardcoded `app.secret_key` and load it from `Config` class in `config.py` (e.g., `app.config.from_object(Config)`).
    *   Modify `app/routes.py` (`setup` route): Remove logic for reading/writing `config.txt`. Instead, read threshold values directly from the `Config` object imported from `config.py`.
    *   *Note:* For this phase, changing thresholds in `config.py` will require an application restart. Dynamic configuration updates could be a future enhancement.

3.  **Create Hardware Abstraction Layer (`app/hardware/`):**
    *   **`gpio_devices.py`:** Define classes or functions to manage GPIO-controlled devices (relays, pump motor driver pins). Encapsulate `RPi.GPIO` setup, pin definitions, state changes (on/off), and cleanup logic.
    *   **`sensors.py`:** Define classes or functions for reading each type of sensor (MAX31865 temperature, DHT22 humidity, DFRobot Oxygen). Encapsulate sensor library initialization and reading logic, including error handling and fallback values.
    *   **`display.py`:** Define a class or functions to manage the OLED display (initialization, clearing, drawing text/images). Encapsulate `adafruit_ssd1306` interactions.
    *   **`serial_comms.py`:** Define functions for initializing the serial port and communicating with the CO2 sensor (sending commands, reading responses, processing data).

4.  **Implement Service Layer (`app/services/`):**
    *   **`sensor_service.py`:**
        *   Create a class/functions responsible for periodically reading all sensors using the `app/hardware/sensors.py` and `app/hardware/serial_comms.py` modules.
        *   Manage the data buffer (`deque`).
        *   Emit sensor data via SocketIO (`socketio.emit`).
        *   Handle data logging by calling a dedicated logging service/function.
        *   Handle display updates by calling the `app/hardware/display.py` module.
        *   This will contain the core logic currently in `read_sensor_data` from `app/background.py`.
    *   **`control_service.py`:**
        *   Create a class/functions responsible for the automatic temperature and CO2 control loops.
        *   Periodically get current sensor values (potentially from `sensor_service` or by reading directly via the hardware layer).
        *   Get control thresholds from `config.py`.
        *   Use the `app/hardware/gpio_devices.py` module to turn actuators (heater relay, CO2 solenoid) on/off based on the control logic.
        *   This will contain the logic currently in `temperature_control_thread` and `co2_control_thread`.
    *   **`datalog_service.py`:** (Optional, could be a utility)
        *   Create functions for initializing and writing sensor data to the CSV file (`OUTPUT_FILE`). Encapsulate the logic from `initialize_output_file` and `save_to_file`.

5.  **Refactor Core Application Components:**
    *   **`app/routes.py`:**
        *   Remove all direct `RPi.GPIO` calls, sensor reading logic, and `config.txt` handling.
        *   Modify `/toggle-device` and `/set-device-speed` to call methods in the `app/hardware/gpio_devices.py` module.
        *   Modify `/setup` (GET) to read current thresholds from `config.py` and potentially current device states from the hardware layer. The POST part of `/setup` might be removed if configuration is only changed by editing `config.py`.
    *   **`app/sockets.py`:** Ensure SocketIO events (`request_data`) are handled correctly, likely by interacting with the `sensor_service`.
    *   **`app/background.py`:** This file might become very thin or be removed entirely, with its responsibilities moved to the `app/services/` modules. The `background_sensor_read` function will be replaced by starting the services.
    *   **`run.py`:**
        *   Modify the startup sequence to initialize the hardware abstraction layer components.
        *   Start the background threads/tasks for `SensorService` and `ControlService`. Ensure they are started correctly (e.g., using `threading` or `socketio.start_background_task`).
        *   Ensure `atexit` cleanup calls the cleanup methods in the hardware abstraction layer.

6.  **Update Dependencies:**
    *   Review `requirements.txt` to ensure all necessary libraries are included and potentially remove unused ones.

**Proposed Structure Diagram:**

```mermaid
graph TD
    subgraph User Interface
        UI[Web Browser]
    end

    subgraph Flask Application (app/)
        direction LR
        Routes[routes.py] --> Services
        Sockets[sockets.py] --> Services
        AppFactory[__init__.py] --> Config[config.py]
        AppFactory --> Routes
        AppFactory --> Sockets
        AppFactory --> Services
        AppFactory --> Hardware
    end

    subgraph Services Layer (app/services/)
        direction TB
        SensorService[sensor_service.py] --> Hardware
        ControlService[control_service.py] --> Hardware
        ControlService --> Config
        SensorService --> DataLogService[datalog_service.py]
        SensorService --> Hardware # For Display
        SensorService --> Sockets
    end

    subgraph Hardware Abstraction Layer (app/hardware/)
        direction TB
        GPIODevices[gpio_devices.py]
        Sensors[sensors.py]
        Display[display.py]
        SerialComms[serial_comms.py]
    end

    subgraph External
        direction TB
        PhysicalSensors[Physical Sensors]
        Actuators[Actuators/Relays]
        OLED[OLED Display]
        SerialDevice[Serial CO2 Sensor]
    end

    UI -- HTTP/WebSocket --> Flask Application
    Hardware -- Interacts with --> External
    Services -- Started by --> Runner[run.py]

    %% Ensure services are distinct visually
    linkStyle 6,7,8,9,10,11,12 stroke-width:0px;

```

This refactoring aims to create a cleaner, more modular, and maintainable application structure.