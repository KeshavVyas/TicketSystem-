#!/usr/bin/env python3

import time
import subprocess
import sys
import os
import signal
import board
import digitalio
import adafruit_dht

# Kill any existing read_temp.py processes (except this one)
def kill_existing_processes():
    """Kill any other instances of read_temp.py"""
    current_pid = os.getpid()
    try:
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
                    if pid != current_pid:
                        print(f"Killing existing read_temp.py process (PID: {pid})...")
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.5)  # Give it time to clean up
                except (ValueError, ProcessLookupError):
                    pass
    except Exception as e:
        print(f"Warning: Could not check for existing processes: {e}")

# Clean up any existing processes first
kill_existing_processes()
time.sleep(0.5)  # Wait a bit for GPIO to be released

# Setup GPIO 24 as output for power control
try:
    gpio24 = digitalio.DigitalInOut(board.D24)
    gpio24.direction = digitalio.Direction.OUTPUT
    gpio24.value = True  # Turn on GPIO 24
    print("GPIO 24 initialized and turned ON")
except Exception as e:
    print(f"Error initializing GPIO 24: {e}")
    print("This usually means GPIO 24 is still in use by another process.")
    print("Try running: pkill -f read_temp.py")
    sys.exit(1)

# Setup DHT sensor on GPIO 23
dht = adafruit_dht.DHT22(board.D23)

try:
    while True:
        try:
            temp_c = dht.temperature
            humidity = dht.humidity
            
            # Only process if we got valid readings
            if temp_c is not None and humidity is not None:
                temp_f = temp_c * 9/5 + 32
                print(f"Temperature: {temp_f}°F, Humidity: {humidity}%")
                
                # Check if humidity exceeds 95%
                if humidity > 50:
                    print(f"Humidity {humidity}% exceeds 95% - shutting down GPIOs and starting servers...")
                    # Turn off GPIO 24
                    gpio24.value = False
                    # Close sensor on GPIO 23
                    dht.exit()
                    # Call start_servers.sh
                    subprocess.run(["/home/pi/Desktop/TicketSystem-/Validator/start_servers.sh"])
                    break
        except RuntimeError:
            pass
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    try:
        gpio24.value = False
        gpio24.deinit()  # Properly release the GPIO
    except:
        pass
    try:
        dht.exit()
    except:
        pass
