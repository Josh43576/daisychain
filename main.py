from sensors import read_all_pzem
from controls.relay import control_appliance, cleanup as cleanup_relay
from auth.rfid import check_user, read_rfid_id, is_authorized
from display.lcd import show_readings, initialize_lcd
from utils.server import send_to_server, get_control_commands
import time
import signal
import sys
import os
import json
from datetime import datetime

# Global flag for graceful shutdown
shutdown_requested = False
admin_override_limit = None
admin_override_active = False

daily_energy_kwh = 0.0
state_file = os.path.join(os.path.dirname(__file__), "daily_usage_state.json")
history_file = os.path.join(os.path.dirname(__file__), "daily_usage_history.json")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\nShutdown requested...")
    shutdown_requested = True


def load_daily_state():
    """Load the current daily total without deleting history."""
    global daily_energy_kwh
    try:
        if not os.path.exists(state_file):
            return
        with open(state_file, "r") as file:
            data = json.load(file)
            daily_energy_kwh = float(data.get("daily_energy_kwh", 0.0))
    except Exception:
        daily_energy_kwh = 0.0


def save_daily_state():
    """Persist the active daily counter."""
    payload = {
        "daily_energy_kwh": daily_energy_kwh,
        "updated_at": datetime.utcnow().isoformat()
    }
    with open(state_file, "w") as file:
        json.dump(payload, file)


def append_history(event_type, message, value_watts=0.0, preset_limit=0.0):
    """Keep a permanent history log for resets, overrides, and trips."""
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as file:
                history = json.load(file)
        except Exception:
            history = []

    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "message": message,
        "value_watts": value_watts,
        "preset_limit": preset_limit,
    })

    with open(history_file, "w") as file:
        json.dump(history, file)


def reset_daily_usage():
    """Reset only the active daily counter; keep historical records intact."""
    global daily_energy_kwh
    daily_energy_kwh = 0.0
    save_daily_state()
    append_history("daily_reset", "Admin RFID reset cleared the current day total.")
    print("Today's power usage reset by administrator. Historical logs remain saved.")


def handle_admin_bypass(preset_limit):
    """Allow an authorized admin to override the preset after a trip or reset the day."""
    global admin_override_limit, admin_override_active

    print("Power limit reached. Present the admin RFID card to override or reset daily usage.")
    card_id = read_rfid_id()
    if card_id is None or not is_authorized(card_id):
        print("Override denied: unauthorized RFID card.")
        return False

    print("Authorized admin card detected.")
    while True:
        choice = input("Enter custom wattage (<= preset limit), type 'RESET' to clear today's usage, or 'CANCEL': ").strip().upper()

        if choice == "CANCEL":
            print("Override cancelled. Power remains cut off.")
            return False

        if choice == "RESET":
            admin_override_limit = None
            admin_override_active = False
            reset_daily_usage()
            return True

        try:
            custom_watts = float(choice)
        except ValueError:
            print("Invalid value. Please enter a number or RESET/CANCEL.")
            continue

        if custom_watts <= 0:
            print("Override value must be greater than 0.")
            continue

        if custom_watts > preset_limit:
            print(f"Emergency override cannot exceed the preset limit of {preset_limit} W.")
            continue

        admin_override_limit = custom_watts
        admin_override_active = True
        append_history("admin_override", "Authorized admin set temporary allowable limit.", value_watts=custom_watts, preset_limit=preset_limit)
        print(f"Admin override active: permitted power is {custom_watts} W.")
        return True


def update_daily_energy(readings):
    """Update the active daily total while leaving historical logs in place."""
    global daily_energy_kwh
    total = 0.0
    for reading in readings:
        try:
            total += float(reading.get("energy", 0.0))
        except (TypeError, ValueError):
            pass
    daily_energy_kwh = total
    save_daily_state()
    return total


def main():
    print("Starting Advanced IoT Power Management System...")
    print("Press Ctrl+C to stop.")
    load_daily_state()

    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize LCD once
    initialize_lcd()

    try:
        while not shutdown_requested:
            # 1. Read sensors
            readings = read_all_pzem()
            print("Sensor Readings:", readings)

            # 2. Update daily total before checking trip condition
            current_daily_energy = update_daily_energy(readings)
            print(f"Current daily energy: {current_daily_energy} kWh")

            # 3. RFID authentication for system access
            user_ok = check_user()
            if not user_ok:
                print("Unauthorized user detected. Skipping control.")
                time.sleep(5)
                continue

            # 4. Display locally
            show_readings(readings)

            # 5. Send to Flask web app
            send_to_server(readings)

            # 6. Get control commands from Flask
            commands = get_control_commands()
            appliances = commands.get("appliances", [])
            preset_limit = float(commands.get("preset_limit", 500.0))
            active_limit = admin_override_limit if admin_override_active else preset_limit

            # 7. Check each sensor against the effective power limit
            for i, reading in enumerate(readings):
                try:
                    power_value = float(reading.get("power", 0))
                except (TypeError, ValueError):
                    power_value = 0.0

                if power_value > active_limit:
                    print(
                        f"Power limit exceeded: {power_value}W > {active_limit}W. Checking for admin bypass..."
                    )

                    if handle_admin_bypass(preset_limit):
                        print("System allowed through admin bypass or daily reset.")
                        continue

                    print(f"Power limit exceeded: Appliance {i+1} at {power_value}W > {preset_limit}W. Cutting power.")
                    append_history("preset_cutoff", "Preset limit exceeded. Relay cut power.", value_watts=power_value, preset_limit=preset_limit)
                    control_appliance(i, False)
                    appliances[i] = "OFF"

            # 8. Apply relay control from web commands
            for i, cmd in enumerate(appliances):
                if cmd == "ON":
                    if control_appliance(i, True):
                        print(f"Appliance {i+1} turned ON")
                elif cmd == "OFF":
                    if control_appliance(i, False):
                        print(f"Appliance {i+1} turned OFF")

            # 9. Auto-clear admin override when the load falls back under the allowed limit
            if admin_override_active:
                total_power = 0.0
                for reading in readings:
                    try:
                        total_power += float(reading.get("power", 0))
                    except (TypeError, ValueError):
                        pass
                if total_power < admin_override_limit * 0.9:
                    admin_override_active = False
                    admin_override_limit = None
                    print("Admin override expired automatically after normal load recovered.")

            # 10. Wait before next cycle
            time.sleep(5)

    except Exception as e:
        print(f"Fatal error in main loop: {e}")

    finally:
        # Cleanup resources
        print("Cleaning up...")
        cleanup_relay()
        print("System stopped.")

if __name__ == "__main__":
    main()
