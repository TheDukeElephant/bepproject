import logging
import socket
import subprocess
import atexit
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from app.hardware.sensors import FALLBACK_TEMPERATURE, FALLBACK_HUMIDITY, FALLBACK_OXYGEN # Import fallbacks for comparison

# --- Constants ---
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
DEFAULT_FONT = None # Load default font during init if possible

# --- State Variables ---
_i2c = None
_oled = None
_is_initialized = False

# --- Helper Functions ---
def _get_ip_address():
    """Gets the primary IP address of the device."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send data, just finds preferred outbound IP
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception as e:
        logging.debug(f"Could not get IP address: {e}") # Use debug as this might happen normally offline
        ip_address = "N/A"
    finally:
        s.close()
    return ip_address

def _get_wifi_ssid():
    """Gets the currently connected WiFi SSID."""
    try:
        # Ensure iwgetid is installed on the Raspberry Pi OS
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, check=False)
        ssid = result.stdout.strip()
        return ssid if ssid else "N/A"
    except FileNotFoundError:
        logging.warning("`iwgetid` command not found. Cannot determine SSID.")
        return "N/A"
    except Exception as e:
        logging.error(f"Error getting Wi-Fi SSID: {e}")
        return "N/A"

# --- Initialization and Cleanup ---
def initialize_display():
    """Initializes the I2C bus and the OLED display."""
    global _i2c, _oled, _is_initialized, DEFAULT_FONT
    if _is_initialized:
        logging.warning("Display already initialized.")
        return True

    logging.info("Initializing OLED display...")
    try:
        # Note: I2C might be initialized by other sensors too.
        # Consider sharing the bus object if necessary.
        _i2c = busio.I2C(board.SCL, board.SDA)
        _oled = adafruit_ssd1306.SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, _i2c)
        _oled.fill(0) # Clear display on init
        _oled.show()
        _is_initialized = True
        logging.info("OLED display initialized successfully.")
        # Load default font once
        DEFAULT_FONT = ImageFont.load_default()
        # Register cleanup function
        atexit.register(display_standby)
        return True
    except ValueError:
         logging.error("OLED display not found on I2C bus. Check connections and address.")
         _oled = None
         _is_initialized = False
         return False
    except Exception as e:
        logging.error(f"Error initializing OLED display: {e}")
        _oled = None
        _is_initialized = False
        return False

def clear_display():
    """Clears the OLED display."""
    if not _is_initialized or not _oled:
        logging.warning("Display not initialized, cannot clear.")
        return
    try:
        _oled.fill(0)
        _oled.show()
    except Exception as e:
        logging.error(f"Error clearing display: {e}")

def display_standby():
    """Displays a 'Standby...' message on the OLED."""
    if not _is_initialized or not _oled:
        # Don't log warning here as it might be called during shutdown before init
        return

    logging.info("Setting OLED display to Standby...")
    try:
        image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        draw = ImageDraw.Draw(image)
        font = DEFAULT_FONT or ImageFont.load_default() # Fallback if init failed before font load
        # Basic centering
        text = "Standby..."
        (font_width, font_height) = font.getsize(text)
        draw.text(
            ( (DISPLAY_WIDTH - font_width) // 2, (DISPLAY_HEIGHT - font_height) // 2 ),
            text, font=font, fill=255
        )
        _oled.image(image)
        _oled.show()
    except Exception as e:
        logging.error(f"Error displaying 'Standby...' on OLED: {e}")

# --- Display Update ---
def update_display(sensor_data):
    """Updates the OLED display with current sensor data and network info."""
    if not _is_initialized or not _oled:
        logging.warning("Display not initialized, cannot update.")
        return

    try:
        # Prepare display strings, handling potential errors or fallback values
        # Using the 5th temperature sensor (index 4) as the primary display temp
        temp_val = sensor_data.get('temperatures', [FALLBACK_TEMPERATURE]*5)[4]
        display_temp = "N/A" if temp_val == FALLBACK_TEMPERATURE else f"{temp_val:.1f} C"

        humidity_val = sensor_data.get('humidity', FALLBACK_HUMIDITY)
        display_humidity = "N/A" if humidity_val == FALLBACK_HUMIDITY else f"{humidity_val:.1f} %"

        o2_val = sensor_data.get('o2', FALLBACK_OXYGEN)
        display_o2 = "N/A" if o2_val == FALLBACK_OXYGEN else f"{o2_val:.1f} %"

        # CO2 value needs to be read separately via serial, assuming it's passed in sensor_data
        co2_val = sensor_data.get('co2', -1) # Assuming -1 indicates not available/error
        display_co2 = "N/A" if co2_val == -1 else f"{co2_val:.2f} %" # CO2 might have more decimals

        # Get network info
        ip_address = _get_ip_address()
        wifi_ssid = _get_wifi_ssid()

        # Draw on image buffer
        image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        draw = ImageDraw.Draw(image)
        font = DEFAULT_FONT or ImageFont.load_default()

        # Draw text lines
        draw.text((0, 0),  f"SSID: {wifi_ssid}", font=font, fill=255)
        draw.text((0, 10), f"IP: {ip_address}", font=font, fill=255)
        draw.text((0, 22), f"Temp: {display_temp}", font=font, fill=255)
        draw.text((0, 32), f"Hum:  {display_humidity}", font=font, fill=255)
        draw.text((0, 42), f"O2:   {display_o2}", font=font, fill=255)
        draw.text((0, 52), f"CO2:  {display_co2}", font=font, fill=255)

        # Send image to display
        _oled.image(image)
        _oled.show()

    except Exception as e:
        logging.error(f"Error updating OLED display: {e}")

# Note: initialize_display() should be called once during application startup.
# atexit registration is handled within initialize_display().