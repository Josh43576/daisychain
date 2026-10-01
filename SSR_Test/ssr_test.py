import RPi.GPIO as GPIO
import time

# This is a simple hardware test for a Solid State Relay (SSR).
# It does NOT use the website, Flask app, RFID system, sensors, or the existing project code.
# This program is meant to test the SSR by itself on the Raspberry Pi.

# Use BCM numbering for the GPIO pins.
# BCM numbering is the standard Raspberry Pi GPIO numbering system.
GPIO.setmode(GPIO.BCM)

# Test GPIO 17 first.
# This pin is the one we will use to control the SSR input.
GPIO.setup(17, GPIO.OUT)

# Turn GPIO 17 ON.
# If the SSR input is active-high, this should trigger the SSR.
print("GPIO 17 ON: sending HIGH signal to the SSR...")
GPIO.output(17, GPIO.HIGH)

# Keep the signal ON for about 10 seconds so you can check the hardware.
time.sleep(10)

# Turn GPIO 17 OFF after the test period.
print("GPIO 17 OFF: sending LOW signal to the SSR...")
GPIO.output(17, GPIO.LOW)

# Clean up the GPIO configuration when the test finishes.
# This is important so the pin is reset properly.
GPIO.cleanup()

print("GPIO test complete. The SSR should have been activated and then turned off.")
