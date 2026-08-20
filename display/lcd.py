# If using I²C LCD with backpack
try:
    import smbus2
except ModuleNotFoundError:
    smbus2 = None
    print("Warning: smbus2 not installed. LCD output is disabled.")
import time

__all__ = ["initialize_lcd", "show_readings"]

# I²C address for LCD (commonly 0x27 or 0x3F)
I2C_ADDR = 0x27
bus = smbus2.SMBus(1) if smbus2 is not None else None
lcd_initialized = False

# Commands for LCD
LCD_WIDTH = 16     # Characters per line
LCD_CHR = 1        # Mode - Sending data
LCD_CMD = 0        # Mode - Sending command
LCD_LINE_1 = 0x80  # LCD RAM address for line 1
LCD_LINE_2 = 0xC0  # LCD RAM address for line 2
E_PULSE = 0.0005
E_DELAY = 0.0005

def lcd_init():
    if bus is None:
        return
    lcd_byte(0x33, LCD_CMD)  # Initialize
    lcd_byte(0x32, LCD_CMD)  # Set to 4-bit mode
    lcd_byte(0x06, LCD_CMD)  # Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # Turn cursor off
    lcd_byte(0x28, LCD_CMD)  # 2 line display
    lcd_byte(0x01, LCD_CMD)  # Clear display
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    if bus is None:
        return
    # Send byte to data pins
    bits_high = mode | (bits & 0xF0) | 0x08
    bits_low = mode | ((bits << 4) & 0xF0) | 0x08
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
    if bus is None:
        return
    time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | 0x04))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR, (bits & ~0x04))
    time.sleep(E_DELAY)

def lcd_string(message, line):
    if bus is None:
        return
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

def initialize_lcd():
    """
    Initialize LCD once at startup.
    """
    global lcd_initialized
    if bus is not None and not lcd_initialized:
        try:
            lcd_init()
            lcd_initialized = True
        except Exception as e:
            print(f"Error initializing LCD: {e}")

def show_readings(readings):
    """
    Display readings on LCD (first two appliances).
    If more than two, rotate or print to console.
    """
    if bus is None:
        for i, r in enumerate(readings):
            print(f"Appliance {i+1}: {r}")
        return

    try:
        if len(readings) >= 1:
            lcd_string(f"A1 P:{readings[0].get('power','-')}W", LCD_LINE_1)
        if len(readings) >= 2:
            lcd_string(f"A2 P:{readings[1].get('power','-')}W", LCD_LINE_2)
    except Exception as e:
        print(f"Error updating LCD: {e}")

    # For debugging, also print to console
    for i, r in enumerate(readings):
        print(f"Appliance {i+1}: {r}")
