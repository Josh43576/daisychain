import time

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    class _GPIO:
        BOARD = "BOARD"
        BCM = "BCM"
        OUT = "OUT"
        HIGH = 1
        LOW = 0

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setup(pin, mode):
            pass

        @staticmethod
        def output(pin, value):
            pass

        @staticmethod
        def cleanup():
            pass

    GPIO = _GPIO()

__all__ = ["initialize_lcd", "show_readings"]

# Set to False if you do not have a GPIO-connected HD44780-style 16x2 LCD.
# The MPI3508 device (I2C/SPI variant) may be separate; disable GPIO LCD
# to avoid attempting to access Raspberry Pi GPIO when not wired.
USE_GPIO_LCD = False

# MPI3508 / Raspberry Pi direct GPIO LCD wiring
# Power lines are connected to physical pin 2 (5V) and pin 6 (GND).
# Update the signal pins below to match your actual MPI3508 wiring.
LCD_RS = 18
LCD_E = 23
LCD_D4 = 24
LCD_D5 = 25
LCD_D6 = 26
LCD_D7 = 7

LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False

lcd_initialized = False

# Standard 2-line LCD addresses in 4-bit mode
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0


def lcd_pulse_enable():
    GPIO.output(LCD_E, GPIO.HIGH)
    time.sleep(0.0005)
    GPIO.output(LCD_E, GPIO.LOW)
    time.sleep(0.0005)


def lcd_write_byte(bits, mode):
    GPIO.output(LCD_RS, mode)

    GPIO.output(LCD_D4, bool(bits & 0x10))
    GPIO.output(LCD_D5, bool(bits & 0x20))
    GPIO.output(LCD_D6, bool(bits & 0x40))
    GPIO.output(LCD_D7, bool(bits & 0x80))
    lcd_pulse_enable()

    GPIO.output(LCD_D4, bool(bits & 0x01))
    GPIO.output(LCD_D5, bool(bits & 0x02))
    GPIO.output(LCD_D6, bool(bits & 0x04))
    GPIO.output(LCD_D7, bool(bits & 0x08))
    lcd_pulse_enable()


def lcd_init():
    # Use BCM numbering to match the GPIO constants (BCM numbers)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_E, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)

    time.sleep(0.05)
    lcd_write_byte(0x33, LCD_CMD)
    time.sleep(0.01)
    lcd_write_byte(0x32, LCD_CMD)
    lcd_write_byte(0x28, LCD_CMD)
    lcd_write_byte(0x0C, LCD_CMD)
    lcd_write_byte(0x06, LCD_CMD)
    lcd_write_byte(0x01, LCD_CMD)
    time.sleep(0.02)


def lcd_string(message, line):
    if line == 1:
        lcd_write_byte(LCD_LINE_1, LCD_CMD)
    else:
        lcd_write_byte(LCD_LINE_2, LCD_CMD)

    message = (message[:LCD_WIDTH]).ljust(LCD_WIDTH, " ")
    for char in message:
        lcd_write_byte(ord(char), LCD_CHR)


def initialize_lcd():
    """Initialize the LCD once at startup."""
    global lcd_initialized
    if not USE_GPIO_LCD:
        return

    if not lcd_initialized:
        try:
            lcd_init()
            lcd_initialized = True
        except Exception as e:
            print(f"Error initializing LCD: {e}")


def show_readings(readings, appliance_names=None):
    """Display readings on the LCD using friendly appliance names."""
    names = appliance_names or ["A1", "A2", "A3"]
    try:
        if USE_GPIO_LCD:
            if len(readings) >= 1:
                label = names[0][:5]
                lcd_string(f"{label} P:{readings[0].get('power','-')}W", 1)
            if len(readings) >= 2:
                label = names[1][:5]
                lcd_string(f"{label} P:{readings[1].get('power','-')}W", 2)
    except Exception as e:
        print(f"Error updating LCD: {e}")

    for i, r in enumerate(readings):
        name = names[i] if i < len(names) else f"Appliance {i + 1}"
        print(f"{name}: {r}")
