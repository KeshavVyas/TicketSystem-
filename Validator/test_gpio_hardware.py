#!/usr/bin/env python3
"""
Hardware test script for GPIO 27 and 22
This will help determine if the pins are damaged or if it's a software issue.
"""
import time
from gpiozero import OutputDevice

print("=" * 50)
print("GPIO Hardware Test")
print("=" * 50)
print("\nThis script will test GPIO 27 and 22.")
print("Watch your LEDs - they should turn ON for 3 seconds each.")
print("\nIf the LEDs don't light up, check:")
print("1. Wiring: GPIO -> Resistor (220-330Ω) -> LED anode -> LED cathode -> GND")
print("2. LED polarity (long leg = anode)")
print("3. Resistor value (too high = dim, too low = may damage LED)")
print("4. Power supply (3.3V for GPIO)")
print("\nStarting test in 2 seconds...")
time.sleep(2)

# Test GPIO 27
print("\n" + "=" * 50)
print("Testing GPIO 27 (should be RED LED based on .env)")
print("=" * 50)
try:
    led27 = OutputDevice(27, initial_value=False)
    print("✓ GPIO 27 initialized")
    print("→ Turning ON GPIO 27 (LED should light up now)...")
    led27.on()
    time.sleep(3)
    print("→ Turning OFF GPIO 27...")
    led27.off()
    led27.close()
    print("✓ GPIO 27 test complete")
except Exception as e:
    print(f"✗ GPIO 27 ERROR: {e}")

time.sleep(1)

# Test GPIO 22
print("\n" + "=" * 50)
print("Testing GPIO 22 (should be YELLOW LED based on .env)")
print("=" * 50)
try:
    led22 = OutputDevice(22, initial_value=False)
    print("✓ GPIO 22 initialized")
    print("→ Turning ON GPIO 22 (LED should light up now)...")
    led22.on()
    time.sleep(3)
    print("→ Turning OFF GPIO 22...")
    led22.off()
    led22.close()
    print("✓ GPIO 22 test complete")
except Exception as e:
    print(f"✗ GPIO 22 ERROR: {e}")

print("\n" + "=" * 50)
print("Test Complete")
print("=" * 50)
print("\nIf the LEDs didn't light up:")
print("- The GPIO pins are likely NOT damaged (software can control them)")
print("- Check your wiring and LED connections")
print("- Try a different LED or test with a multimeter")
print("- Verify the GPIO pin numbers in your .env file match your wiring")
