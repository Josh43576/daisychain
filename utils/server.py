import requests

DEFAULT_PRESET_LIMIT = 500.0

# Replace <server-ip> with the IP address or hostname of your Flask server
API_DATA = "http://<server-ip>:5000/api/data"
API_CONTROL = "http://<server-ip>:5000/api/control"

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
    Fetch appliance control commands from the Flask web app.
    Returns a dictionary like: {"appliances": ["ON", "OFF", "ON"], "preset_limit": 500.0}
    """
    try:
        r = requests.get(API_CONTROL, timeout=5)
        r.raise_for_status()  # Raise exception for bad status codes
        data = r.json()

        if isinstance(data, dict) and "appliances" in data:
            if isinstance(data["appliances"], list):
                if "preset_limit" not in data:
                    data["preset_limit"] = DEFAULT_PRESET_LIMIT
                return data

        print("Warning: Invalid response format from API")
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT}
    except requests.exceptions.Timeout:
        print("Error: API request timed out")
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT}
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server")
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT}
    except Exception as e:
        print("Error fetching commands:", e)
        return {"appliances": [], "preset_limit": DEFAULT_PRESET_LIMIT}
