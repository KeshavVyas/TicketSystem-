#!/usr/bin/env python3

import time
import os
import signal
import subprocess
import board
import adafruit_dht
from gpiozero import OutputDevice
from pathlib import Path

# Load .env file
env = {}
env_file = Path(__file__).parent / '.env'
if not env_file.exists():
    env_file = Path(__file__).parent.parent / '.env'

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                env[key] = value

YELLOW_GPIO = int(env.get('YELLOW_GPIO', '27'))
GREEN_GPIO = int(env.get('GREEN_GPIO', '4'))
RED_GPIO = int(env.get('RED_GPIO', '22'))

# Turn off all GPIO pins at startup to release any busy pins
print("Turning off all GPIO pins at startup...")
gpio_pins = [YELLOW_GPIO, GREEN_GPIO, RED_GPIO]
gpio_devices = []

for pin in gpio_pins:
    try:
        gpio = OutputDevice(pin, initial_value=False)
        gpio.off()
        gpio.close()
        print(f"✓ GPIO {pin} turned OFF and released")
    except Exception as e:
        print(f"✗ GPIO {pin} error: {e}")

# Wait a moment for GPIO to be fully released
time.sleep(0.5)

# Kill any existing login_server processes
try:
    result = subprocess.run(['pgrep', '-f', 'login_server.py'], capture_output=True, text=True)
    if result.returncode == 0:
        pids = result.stdout.strip().split('\n')
        for pid_str in pids:
            try:
                pid = int(pid_str.strip())
                if pid != os.getpid():
                    os.kill(pid, signal.SIGTERM)
                    print(f"Killed existing login_server process: {pid}")
            except (ValueError, ProcessLookupError):
                pass
except Exception:
    pass

# Wait a bit more after killing processes
time.sleep(1.0)

# Setup yellow LED for blinking indicator
yellow_led = OutputDevice(YELLOW_GPIO, initial_value=False)

# Setup DHT sensor on GPIO 18
dht = adafruit_dht.DHT22(board.D18)

# Wait for sensor to stabilize and discard first reading (may be stale)
print("Initializing sensor...")
time.sleep(2.0)  # Give sensor time to stabilize
try:
    # Discard first reading (may be from buffer/stale)
    _ = dht.temperature
    _ = dht.humidity
    time.sleep(2.0)  # Wait before first real reading
except:
    pass  # Ignore errors on initial read

login_server_process = None

print("Starting temperature and humidity monitoring...")

while True:
    try:
        temp_c = dht.temperature
        humidity = dht.humidity
    except RuntimeError:
        # DHT sensors sometimes fail to read, this is normal
        # Continue to next iteration
        yellow_led.on()
        time.sleep(0.5)
        yellow_led.off()
        time.sleep(0.5)
        continue
    except Exception as e:
        print(f"Sensor error: {e}")
        yellow_led.on()
        time.sleep(0.5)
        yellow_led.off()
        time.sleep(0.5)
        continue
    
    if temp_c is not None and humidity is not None:
        temp_f = temp_c * 9/5 + 32
        print(f"Temperature: {temp_f}°F, Humidity: {humidity}%")
        
        # Check if humidity exceeds threshold
        if humidity > 50:
            print("high humidity")
            
            # Stop taking readings - turn off yellow LED
            yellow_led.off()
            yellow_led.close()
            
            # Close DHT sensor
            try:
                dht.exit()
            except:
                pass
            
            # Wait 2 seconds
            print("Turning off GPIO pins and waiting 2 seconds...")
            time.sleep(2.0)
            
            # Kill any existing login_server processes first
            try:
                result = subprocess.run(['pgrep', '-f', 'login_server.py'], capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid_str in pids:
                        try:
                            pid = int(pid_str.strip())
                            if pid != os.getpid():
                                os.kill(pid, signal.SIGTERM)
                                print(f"Killed existing login_server process: {pid}")
                                time.sleep(0.5)
                        except (ValueError, ProcessLookupError):
                            pass
            except Exception:
                pass
            
            # Wait a bit more to ensure server is fully shut down and GPIO released
            time.sleep(1.0)
            
            # Start login server if not already running
            if login_server_process is None or login_server_process.poll() is not None:
                login_server_path = Path(__file__).parent / 'login_server.py'
                login_server_process = subprocess.Popen(['python3', str(login_server_path)])
                
                # Get IP for display
                pi_ip = env.get('PI_IP', 'localhost')
                if pi_ip == 'localhost':
                    import socket
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        pi_ip = s.getsockname()[0]
                        s.close()
                    except:
                        pass
                
                print(f"Login server starting... (check server output for secret URL)")
            
            # Stop monitoring loop - server is running
            break
        else:
            # Stop login server if running
           
            
            # Blink yellow LED at 0.5 second intervals when humidity is below 50%
            yellow_led.on()
            time.sleep(0.5)
            yellow_led.off()
            time.sleep(0.5)
    else:
        yellow_led.on()
        time.sleep(0.5)
        yellow_led.off()
        time.sleep(0.5)
