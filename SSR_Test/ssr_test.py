import time
import RPi.GPIO as GPIO


def run_ssr_test():
    # BCM numbering for the GPIO pins.
    GPIO.setmode(GPIO.BCM)

    warn = getattr(GPIO, "setwarnings", None)
    if callable(warn):
        warn(False)

    # GPIO 17 = Physical Pin 11
    # GPIO 27 = Physical Pin 13
    # GPIO 22 = Physical Pin 15
    relay_pins = [17, 27, 22]

    try:
        for pin in relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        for pin in relay_pins:
            print(f"GPIO {pin} ON: sending HIGH signal to the SSR...")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(10)

            print(f"GPIO {pin} OFF: sending LOW signal to the SSR...")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(2)

        print("GPIO 17, 27, and 22 test complete.")
        print("GPIO 17 = Physical Pin 11")
        print("GPIO 27 = Physical Pin 13")
        print("GPIO 22 = Physical Pin 15")

    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete.")


if __name__ == "__main__":
    run_ssr_test()