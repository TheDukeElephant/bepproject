import csv
import logging
import os
import time

# --- Constants ---
OUTPUT_FILE = "sensor_data.csv"
# Define the header row explicitly to ensure consistency
# Note: Original code calculated average_temperature but didn't save it explicitly.
# The header had 'average_temperature', but the save function used *sensor_data['temperatures']
# which included 5 temps. Let's define a clear header.
# Assuming 5 temperature sensors + humidity + co2 + o2
HEADER = [
    'timestamp', 'co2', 'o2',
    'temperature_1', 'temperature_2', 'temperature_3', 'temperature_4', 'temperature_5',
    'humidity'
]

# --- Service Functions ---
def initialize_datalog():
    """
    Initializes the data log file. Creates the file and writes the header
    if the file doesn't exist or is empty.
    """
    try:
        # Check if file exists and is not empty
        file_exists = os.path.exists(OUTPUT_FILE)
        is_empty = os.path.getsize(OUTPUT_FILE) == 0 if file_exists else True

        if not file_exists or is_empty:
            with open(OUTPUT_FILE, 'w', newline='') as file: # Use 'w' to create/overwrite if empty
                writer = csv.writer(file)
                writer.writerow(HEADER)
            logging.info(f"Data log file '{OUTPUT_FILE}' initialized with header.")
        else:
            logging.info(f"Data log file '{OUTPUT_FILE}' already exists.")

    except Exception as e:
        logging.error(f"Error initializing data log file '{OUTPUT_FILE}': {e}")

def save_data_to_log(sensor_data):
    """
    Appends a row of sensor data to the CSV log file.

    Args:
        sensor_data (dict): A dictionary containing sensor readings.
                            Expected keys match the HEADER list.
    """
    try:
        # Ensure all header keys are present in the data, providing defaults if necessary
        row_data = [
            sensor_data.get('timestamp', int(time.time())),
            sensor_data.get('co2', -1.0), # Use fallback/error indicator
            sensor_data.get('o2', -1.0),
            # Handle temperatures - expect a list
            *sensor_data.get('temperatures', [-1.0] * 5)[:5], # Take first 5 temps, provide fallback
            sensor_data.get('humidity', -1.0)
        ]

        # Ensure the number of elements matches the header length
        if len(row_data) != len(HEADER):
             logging.error(f"Data length mismatch: Expected {len(HEADER)} columns, got {len(row_data)}. Data: {sensor_data}")
             # Pad with a default value if too short, or truncate if too long (less ideal)
             # This indicates an issue elsewhere generating sensor_data
             row_data = (row_data + [-1.0] * len(HEADER))[:len(HEADER)]


        with open(OUTPUT_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row_data)

    except KeyError as e:
         logging.error(f"Missing key '{e}' in sensor data for logging: {sensor_data}")
    except Exception as e:
        logging.error(f"Error saving data to log file '{OUTPUT_FILE}': {e}")

# Note: initialize_datalog() should be called once during application startup.