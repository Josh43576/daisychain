#!/usr/bin/env python3
"""
Manual (Face-to-Face) Interface for the Raspberry Pi Power Monitor System.

Workflow:
1. Scan RFID card to start
2. Read electrical parameters from PZEM sensors via RS485
3. Display readings on MPI3508 LCD
4. Check if power consumption exceeds preset limit
5. If limit exceeded, prompt admin to rescan RFID for confirmation and reset
6. Return to step 1

This script runs independently from the Flask web app.
"""

import time
import sys
from pzem_multi_reader import read_pzem_module, PZEM_IDS
from auth.rfid import read_rfid_id, is_authorized, AUTHORIZED_IDS
from display.lcd import initialize_lcd, show_readings

# Configuration
DEFAULT_PRESET_LIMIT = 500.0  # watts
APPLIANCE_NAMES = ["Appliance 1", "Appliance 2", "Appliance 3"]
PRESET_LIMIT_WATTS = DEFAULT_PRESET_LIMIT

# State tracking
power_limit_exceeded = False
last_total_power = 0.0


def get_total_power(readings):
    """Calculate total power consumption from all sensors."""
    total = 0.0
    for reading in readings:
        if "power" in reading and reading["power"] is not None:
            total += reading["power"]
    return total


def display_readings_on_lcd(readings):
    """Display sensor readings on LCD in a user-friendly format."""
    try:
        show_readings(readings, APPLIANCE_NAMES)
    except Exception as e:
        print(f"LCD display error: {e}")


def check_power_limit(total_power):
    """Check if total power exceeds preset limit."""
    return total_power > PRESET_LIMIT_WATTS


def prompt_admin_reset():
    """
    Prompt admin to scan their RFID card to confirm reset.
    Returns True if authorized admin scans, False otherwise.
    """
    print("\n" + "="*60)
    print("POWER LIMIT EXCEEDED")
    print(f"Total Power: {last_total_power:.1f}W > Limit: {PRESET_LIMIT_WATTS}W")
    print("="*60)
    print("\nAdmin: Scan your RFID card to confirm reset and continue.")
    print("(Must be an authorized admin)")
    print()

    admin_id = read_rfid_id()
    if admin_id is None:
        print("No RFID card detected. Returning to scan mode.")
        return False

    if is_authorized(admin_id):
        print("✓ Admin authorized. Resetting limit check. Returning to scan mode.")
        return True
    else:
        print("✗ Admin card not authorized. Please use an authorized admin card.")
        print("Returning to scan mode.")
        return False


def wait_for_user_card():
    """Wait for a user RFID card to start the session."""
    print("\n" + "="*60)
    print("READY FOR USER")
    print("="*60)
    print("Waiting for user RFID card...")
    print()

    while True:
        card_id = read_rfid_id()
        if card_id is not None:
            return card_id
        time.sleep(1)


def read_and_display_sensors():
    """Read all PZEM sensors and display on LCD."""
    readings = []
    print("\nReading sensors...")

    for slave_id in PZEM_IDS:
        try:
            data = read_pzem_module(slave_id)
            readings.append(data)
            appliance_idx = PZEM_IDS.index(slave_id)
            appliance_name = APPLIANCE_NAMES[appliance_idx] if appliance_idx < len(APPLIANCE_NAMES) else f"Appliance {appliance_idx + 1}"

            if data.get("error"):
                print(f"  {appliance_name} (ID {slave_id}): ERROR - {data['error']}")
            else:
                voltage = data.get("voltage", "?")
                current = data.get("current", "?")
                power = data.get("power", "?")
                energy = data.get("energy", "?")
                print(f"  {appliance_name} (ID {slave_id}): V={voltage}V, I={current}A, P={power}W, E={energy}Wh")
        except Exception as e:
            print(f"  Sensor {slave_id}: Exception - {e}")
            readings.append({"error": str(e)})

    # Display on LCD
    display_readings_on_lcd(readings)

    return readings


def main():
    """Main loop for the manual interface."""
    global power_limit_exceeded, last_total_power

    print("\n" + "="*60)
    print("POWER MONITOR - MANUAL INTERFACE (RFID + LCD)")
    print("="*60)
    print(f"Preset Power Limit: {PRESET_LIMIT_WATTS}W")
    print(f"Authorized Admin IDs: {AUTHORIZED_IDS}")
    print()

    # Initialize LCD
    initialize_lcd()

    try:
        while True:
            # Step 1: Wait for user card
            user_card = wait_for_user_card()
            print(f"User card scanned: {user_card}")

            # Step 2: Read sensors
            readings = read_and_display_sensors()
            total_power = get_total_power(readings)
            last_total_power = total_power

            print(f"\n>>> Total Power Consumption: {total_power:.1f}W")

            # Step 3: Check power limit
            if check_power_limit(total_power):
                print("⚠ ALERT: Power limit exceeded!")
                power_limit_exceeded = True

                # Step 4: Prompt admin reset
                while power_limit_exceeded:
                    if prompt_admin_reset():
                        power_limit_exceeded = False
                        break
                    else:
                        # Keep prompting until authorized
                        time.sleep(2)

            # Step 5: Return to step 1
            print("\nReady for next user.")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nShutdown requested.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Manual interface stopped.")


if __name__ == "__main__":
    main()
