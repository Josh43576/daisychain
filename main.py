from sensors import read_all_pzem
from controls.relay import control_appliance, cleanup as cleanup_relay
from auth.rfid import check_user
from display.lcd import show_readings, initialize_lcd
from utils.server import send_to_server, get_control_commands
import time
import signal
import sys

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\nShutdown requested...")
    shutdown_requested = True

def main():
    print("Starting Advanced IoT Power Management System...")
    print("Press Ctrl+C to stop.")
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize LCD once
    initialize_lcd()
    
    try:
        while not shutdown_requested:
            # 1. Read sensors
            readings = read_all_pzem()
            print("Sensor Readings:", readings)

            # 2. RFID authentication
            user_ok = check_user()
            if not user_ok:
                print("Unauthorized user detected. Skipping control.")
                time.sleep(5)
                continue

            # 3. Display locally
            show_readings(readings)

            # 4. Send to Flask web app
            send_to_server(readings)

            # 5. Get control commands from Flask
            commands = get_control_commands()
            appliances = commands.get("appliances", [])

            # 6. Apply relay control
            for i, cmd in enumerate(appliances):
                if cmd == "ON":
                    if control_appliance(i, True):
                        print(f"Appliance {i+1} turned ON")
                elif cmd == "OFF":
                    if control_appliance(i, False):
                        print(f"Appliance {i+1} turned OFF")

            # 7. Wait before next cycle
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
