import requests

DEFAULT_PRESET_LIMIT = 500.0
DEFAULT_APPLIANCE_NAMES = ["Appliance 1", "Appliance 2", "Appliance 3"]

# Replace <server-ip> with the IP address or hostname of your Flask server
API_DATA = "http://<server-ip>:5000/api/data"
API_CONTROL = "http://<server-ip>:5000/api/control"
API_CONFIG = "http://<server-ip>:5000/api/config"

def send_to_server(data):
    """
    Send sensor readings to the Flask web app.
    """
    try:
        r = requests.post(API_DATA, json=data)
        print("Data upload:", r.status_code)
    except Exception as e:
        print("Error sending data:", e)

def get_control_commands():
    """
    Fetch appliance control commands and names from the Flask web app.
    Returns a dictionary like:
    {"appliances": ["ON", "OFF", "ON"], "preset_limit": 500.0, "appliance_names": ["Fridge", "AC", "Lights"]}
    """
    try:
        r = requests.get(API_CONTROL, timeout=5)
        r.raise_for_status()
        data = r.json()

        if isinstance(data, dict) and "appliances" in data:
            if isinstance(data["appliances"], list):
                if "preset_limit" not in data:
                    data["preset_limit"] = DEFAULT_PRESET_LIMIT
                if "appliance_names" not in data:
                    data["appliance_names"] = DEFAULT_APPLIANCE_NAMES
                return data

        print("Warning: Invalid response format from API")
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT, "appliance_names": DEFAULT_APPLIANCE_NAMES}
    except requests.exceptions.Timeout:
        print("Error: API request timed out")
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT, "appliance_names": DEFAULT_APPLIANCE_NAMES}
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server")
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT, "appliance_names": DEFAULT_APPLIANCE_NAMES}
    except Exception as e:
        print("Error fetching commands:", e)
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT, "appliance_names": DEFAULT_APPLIANCE_NAMES}


def set_appliance_names(names):
    """Set appliance names on the Flask server before the system starts reading."""
    try:
        payload = {"appliance_names": names}
        r = requests.post(API_CONFIG, json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Error setting appliance names:", e)
        return {"error": str(e)}
