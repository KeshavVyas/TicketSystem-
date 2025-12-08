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

HUMIDITY_THRESHOLD = float(env.get('HUMIDITY_THRESHOLD', '75'))

# Kill any processes that might be using GPIO 24
def kill_gpio24_processes():
    current_pid = os.getpid()
    try:
        # Kill any read_temp.py processes
        result = subprocess.run(['pgrep', '-f', 'read_temp.py'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                try:
                    pid = int(pid_str.strip())
                    if pid != current_pid:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.3)
                except (ValueError, ProcessLookupError):
                    pass
    except Exception:
        pass

kill_gpio24_processes()
time.sleep(1.0)  # Wait 1 second before reading

# Setup GPIO 4 for blinking indicator
gpio4 = OutputDevice(4, initial_value=False)

# Setup DHT sensor on GPIO 24
dht = adafruit_dht.DHT22(board.D18)

print("Starting temperature and humidity monitoring...")

try:
    while True:
        try:
            temp_c = dht.temperature
            humidity = dht.humidity
            
            if temp_c is not None and humidity is not None:
                temp_f = temp_c * 9/5 + 32
                print(f"Temperature: {temp_f}°F, Humidity: {humidity}%")
                
                # Check if humidity exceeds threshold
                if humidity > HUMIDITY_THRESHOLD:
                    print(f"Humidity {humidity}% exceeds threshold - starting servers...")
                    
                    # Turn off GPIO 4 and wait 1 second
                    gpio4.off()
                    time.sleep(1.0)
                    
                    # Close DHT sensor before starting servers
                    try:
                        dht.exit()
                    except:
                        pass
                    
                    # Start servers
                    subprocess.run(["/home/pi/Desktop/TicketSystem-/Validator/start_servers.sh"])
                    
                    # Re-initialize DHT sensor to resume monitoring
                    time.sleep(1.0)
                    dht = adafruit_dht.DHT22(board.D24)
                    print("Resumed temperature and humidity monitoring...")
                else:
                    # Blink GPIO 4 at 0.5 second intervals when humidity is below threshold
                    gpio4.on()
                    time.sleep(0.5)
                    gpio4.off()
                    time.sleep(0.5)
            else:
                print("Failed to read sensor data")
                # Still blink GPIO 4 even if sensor read fails
                gpio4.on()
                time.sleep(0.5)
                gpio4.off()
                time.sleep(0.5)
                
        except RuntimeError:
            # DHT sensors sometimes fail to read, this is normal
            # Still blink GPIO 4
            gpio4.on()
            time.sleep(0.5)
            gpio4.off()
            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
            gpio4.on()
            time.sleep(0.5)
            gpio4.off()
            time.sleep(0.5)
        
except KeyboardInterrupt:
    pass
finally:
    try:
        gpio4.off()
        gpio4.close()
    except:
        pass
    try:
        dht.exit()
    except:
        pass
