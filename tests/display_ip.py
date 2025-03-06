import time
import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont
import socket
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to get the IP address
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        logging.error(f"Error getting IP address: {e}")
        ip = "No IP"
    return ip

# Setup I2C and OLED
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = SSD1306_I2C(128, 32, i2c, addr=0x3C)  # Adjust addr if different
except Exception as e:
    logging.error(f"Error initializing I2C or OLED: {e}")
    exit(1)

# Clear the display
oled.fill(0)
oled.show()

# Create a blank image for drawing
width = oled.width
height = oled.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# Load default font
font = ImageFont.load_default()

while True:
    # Clear the image
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Get the current IP address
    ip_address = get_ip()

    # Draw the IP address on the display
    draw.text((0, 0), f"IP: {ip_address}", font=font, fill=255)

    # Display the image
    oled.image(image)
    oled.show()

    # Wait for a while before updating
    time.sleep(10)
