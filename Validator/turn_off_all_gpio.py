#!/usr/bin/env python3
"""
Turn off all GPIO pins used in the project
"""

from gpiozero import OutputDevice
import time

# Try to import digitalio for GPIO 24 (used by read_temp.py)
try:
    import board
    import digitalio
    HAS_DIGITALIO = True
except ImportError:
    HAS_DIGITALIO = False

# List of GPIO pins used as outputs in the project
GPIO_PINS_GPIOZERO = [4, 21, 22]  # Pins using gpiozero
GPIO_24_PIN = 24  # Pin using digitalio (if available)

print("Turning off all GPIO pins...")
print("=" * 50)

gpio_devices = []

# Turn off pins using gpiozero
for pin in GPIO_PINS_GPIOZERO:
    try:
        gpio = OutputDevice(pin, initial_value=False)
        gpio.off()  # Explicitly turn off
        gpio_devices.append((pin, gpio, 'gpiozero'))
        print(f"✓ GPIO {pin} turned OFF (gpiozero)")
    except Exception as e:
        print(f"✗ GPIO {pin} error: {e}")

# Turn off GPIO 24 using digitalio (if available)
if HAS_DIGITALIO:
    try:
        gpio24 = digitalio.DigitalInOut(board.D24)
        gpio24.direction = digitalio.Direction.OUTPUT
        gpio24.value = False
        gpio_devices.append((GPIO_24_PIN, gpio24, 'digitalio'))
        print(f"✓ GPIO {GPIO_24_PIN} turned OFF (digitalio)")
        gpio24.deinit()  # Release it immediately
    except Exception as e:
        print(f"✗ GPIO {GPIO_24_PIN} error: {e}")

print("=" * 50)
print(f"Turned off {len(gpio_devices)} GPIO pins")

# Keep pins off for a moment to ensure state is set
time.sleep(0.2)

# Clean up - close all GPIO devices
for pin, gpio, lib_type in gpio_devices:
    try:
        if lib_type == 'gpiozero':
            gpio.close()
        elif lib_type == 'digitalio':
            gpio.deinit()
    except:
        pass

print("All GPIO pins have been turned off and released.")

