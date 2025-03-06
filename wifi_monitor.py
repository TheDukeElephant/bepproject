import threading
import time
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_wifi_connected():
    try:
        subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect_wifi():
    logging.info("Reconnecting to Wi-Fi...")
    try:
        result_down = os.system('sudo ifconfig wlan0 down')
        if result_down != 0:
            raise Exception("Failed to bring down wlan0")
        result_up = os.system('sudo ifconfig wlan0 up')
        if result_up != 0:
            raise Exception("Failed to bring up wlan0")
        time.sleep(10)
    except Exception as e:
        logging.error(f"Error reconnecting to Wi-Fi: {e}")

def wifi_monitor():
    while True:
        if not is_wifi_connected():
            reconnect_wifi()
        time.sleep(60)

def start_wifi_monitor():
    wifi_thread = threading.Thread(target=wifi_monitor, daemon=True)
    wifi_thread.start()
