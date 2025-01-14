import threading
import time
import os
import subprocess

def is_wifi_connected():
    try:
        subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect_wifi():
    print("Reconnecting to Wi-Fi...")
    try:
        os.system('sudo ifconfig wlan0 down')
        os.system('sudo ifconfig wlan0 up')
        time.sleep(10)
    except Exception as e:
        print(f"Error reconnecting to Wi-Fi: {e}")

def wifi_monitor():
    while True:
        if not is_wifi_connected():
            reconnect_wifi()
        time.sleep(60)

def start_wifi_monitor():
    wifi_thread = threading.Thread(target=wifi_monitor, daemon=True)
    wifi_thread.start()
