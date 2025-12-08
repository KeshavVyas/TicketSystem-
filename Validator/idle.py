#!/usr/bin/env python3
from gpiozero import OutputDevice
import time
import signal
import sys
import subprocess
import os

print("idle")

# Kill any processes that might be using GPIO 21 (like read_temp.py polling)
def kill_gpio21_processes():
    """Kill any processes that might be holding GPIO 21"""
    try:
        # Kill any read_temp.py processes that might be polling
        result = subprocess.run(
            ['pgrep', '-f', 'read_temp.py'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                try:
                    pid = int(pid_str.strip())
                    if pid != os.getpid():
                        print(f"Killing read_temp.py process (PID: {pid}) to release GPIO 21...")
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.3)  # Give it time to release GPIO
                except (ValueError, ProcessLookupError):
                    pass
    except Exception as e:
        print(f"Warning: Could not check for processes: {e}")

# Kill any processes using GPIO 21 first
kill_gpio21_processes()
time.sleep(0.2)  # Wait a bit more for GPIO to be released

# Set up GPIO 21 and turn it on
try:
    gpio_21 = OutputDevice(21, initial_value=True)
    gpio_21.on()  # Explicitly set to ON
    print("GPIO 21 turned ON")
except Exception as e:
    print(f"Error initializing GPIO 21: {e}")
    print("GPIO 21 may still be in use. Waiting a bit longer...")
    time.sleep(0.5)
    try:
        gpio_21 = OutputDevice(21, initial_value=True)
        gpio_21.on()
        print("GPIO 21 turned ON (retry successful)")
    except Exception as e2:
        print(f"Error: Could not initialize GPIO 21 after retry: {e2}")
        sys.exit(1)

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
