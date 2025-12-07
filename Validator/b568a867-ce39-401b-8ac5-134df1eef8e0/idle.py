#!/usr/bin/env python3
from gpiozero import OutputDevice
import time
import signal
import sys

print("idle")

# Set up GPIO 21 and turn it on
gpio_21 = OutputDevice(21, initial_value=True)
gpio_21.on()  # Explicitly set to ON
print("GPIO 21 turned ON")

# Keep the script running to maintain GPIO state
# The GPIO will stay ON as long as this script is running
def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down...")
    gpio_21.off()
    gpio_21.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("GPIO 21 is ON. Press Ctrl+C to turn it off and exit.")
try:
    while True:
        time.sleep(1)  # Keep script alive
except KeyboardInterrupt:
    signal_handler(None, None)
