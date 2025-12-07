#!/usr/bin/env python3
from gpiozero import OutputDevice
import time
import subprocess
import os
import signal

print("success")

# Kill any idle.py processes that might be holding GPIO 21
def kill_idle_processes():
    """Kill any idle.py processes to release GPIO 21"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'idle.py'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                try:
                    pid = int(pid_str.strip())
                    print(f"Killing idle.py process (PID: {pid}) to release GPIO 21...")
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.3)  # Give it time to release GPIO
                except (ValueError, ProcessLookupError):
                    pass
    except Exception as e:
        print(f"Warning: Could not check for idle.py processes: {e}")

# Kill idle.py processes first
kill_idle_processes()
time.sleep(0.2)  # Wait a bit more for GPIO to be released

# Turn off GPIO 21 as first step (idle state)
try:
    gpio_21 = OutputDevice(21, initial_value=False)
    print("GPIO 21 turned OFF")
except Exception as e:
    print(f"Warning: Could not access GPIO 21: {e}")
    gpio_21 = None
# Small delay to ensure state is set
time.sleep(0.1)

# Set up GPIO 4 and turn it on
gpio_4 = OutputDevice(4, initial_value=True)
print("GPIO 4 turned ON")

# Wait for 5 seconds
time.sleep(5)

# Turn off GPIO 4
gpio_4.off()
print("GPIO 4 turned OFF")

# Clean up GPIO
if gpio_21:
    gpio_21.close()
gpio_4.close()
