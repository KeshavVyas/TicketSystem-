#!/usr/bin/env python3
"""
Test GPIO 27 to diagnose LED issue
"""

from gpiozero import OutputDevice
import time
import sys

GPIO_PIN = 27

print(f"Testing GPIO {GPIO_PIN}")
print("=" * 50)

# Try different initialization methods
print("\nMethod 1: OutputDevice with initial_value=True")
try:
    gpio1 = OutputDevice(GPIO_PIN, initial_value=True)
    print(f"✓ GPIO {GPIO_PIN} initialized ON")
    time.sleep(2)
    gpio1.off()
    print(f"✓ GPIO {GPIO_PIN} turned OFF")
    time.sleep(2)
    gpio1.on()
    print(f"✓ GPIO {GPIO_PIN} turned ON")
    time.sleep(2)
    gpio1.close()
except Exception as e:
    print(f"✗ Error: {e}")

print("\nMethod 2: Direct on/off")
try:
    gpio2 = OutputDevice(GPIO_PIN, initial_value=False)
    print(f"GPIO {GPIO_PIN} state: {gpio2.value}")
    gpio2.on()
    print(f"✓ GPIO {GPIO_PIN} turned ON, state: {gpio2.value}")
    time.sleep(2)
    gpio2.off()
    print(f"✓ GPIO {GPIO_PIN} turned OFF, state: {gpio2.value}")
    time.sleep(2)
    gpio2.close()
except Exception as e:
    print(f"✗ Error: {e}")

print("\nMethod 3: Using RPi.GPIO (if available)")
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.output(GPIO_PIN, GPIO.HIGH)
    print(f"✓ GPIO {GPIO_PIN} set HIGH using RPi.GPIO")
    time.sleep(2)
    GPIO.output(GPIO_PIN, GPIO.LOW)
    print(f"✓ GPIO {GPIO_PIN} set LOW using RPi.GPIO")
    GPIO.cleanup()
except ImportError:
    print("RPi.GPIO not available")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 50)
print("Test complete. Check if LED lit up during any of these tests.")
print("\nTroubleshooting tips:")
print("1. Make sure LED has a current-limiting resistor (220-330 ohm)")
print("2. Check wiring: GPIO 27 -> Resistor -> LED anode -> LED cathode -> GND")
print("3. Verify you're using BCM pin 27, not physical pin 27")
print("4. Check if GPIO 27 is being used by another process")
