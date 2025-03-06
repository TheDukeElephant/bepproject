# bepproject

This project is based on a Flask framework Python app.
It will enable control of a box which can alter the temperature, humidity, CO2 levels, and O2 levels of a box designed for carrying living cells.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/bepproject.git
    cd bepproject
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Initialize the database:
    ```sh
    python setup.py
    ```

2. Run the application (use sudo if necessary):
    ```sh
    sudo python run.py
    ```

3. Access the application at `http://localhost:5000`.

## Features

- Monitor and control temperature, humidity, CO2, and O2 levels.
- Display IP address on an OLED screen.
- Automatic Wi-Fi reconnection.
- User authentication and dashboard.

## License

This project is licensed under the MIT License.
