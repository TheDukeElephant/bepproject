# BEP Project

This project is based on a Flask framework Python app.
It will enable control of a box which can alter the temperature, humidity, CO2 levels, and O2 levels of a box designed for carrying living cells.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Configure thresholds in `config.py`.
3. Run the Flask application:
   ```
   python run.py
   ```
4. Navigate to http://<your-pi-ip>:5000

## Notes

- Old scripts in `app/old` are deprecated.
- Logs are stored to console using a consistent format.

## Features

- Monitor and control temperature, humidity, CO2, and O2 levels.
- Display IP address on an OLED screen.
- Automatic Wi-Fi reconnection.
- User authentication and dashboard.

## License

This project is licensed under the MIT License.
