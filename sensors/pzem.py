import serial
import struct

__all__ = ["read_pzem", "read_all_pzem"]

# Define ports for 3 sensors (adjust based on your USB adapters)
ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2']

# PZEM-004T Modbus RTU protocol commands
PZEM_DEFAULT_ADDR = 0xF8
PZEM_VOLTAGE_CMD = bytes([PZEM_DEFAULT_ADDR, 0x03, 0x00, 0x00, 0x00, 0x02, 0x3D, 0x30])
PZEM_CURRENT_CMD = bytes([PZEM_DEFAULT_ADDR, 0x03, 0x00, 0x01, 0x00, 0x02, 0x3D, 0xC1])
PZEM_POWER_CMD = bytes([PZEM_DEFAULT_ADDR, 0x03, 0x00, 0x03, 0x00, 0x02, 0x3D, 0x09])
PZEM_ENERGY_CMD = bytes([PZEM_DEFAULT_ADDR, 0x03, 0x00, 0x05, 0x00, 0x02, 0x3C, 0x49])

def calculate_crc(data):
    """
    Calculate CRC16-ModBus for PZEM protocol.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def read_pzem_register(ser, command):
    """
    Send a command to PZEM sensor and read the response.
    """
    try:
        ser.write(command)
        response = ser.read(7)
        if len(response) == 7:
            return struct.unpack('>H', response[3:5])[0]
    except Exception as e:
        print(f"Error reading PZEM register: {e}")
    return None

def read_pzem(port):
    """
    Reads data from a single PZEM-004T sensor via Modbus RTU protocol.
    Returns voltage (V), current (A), power (W), and energy (kWh).
    """
    try:
        ser = serial.Serial(port, baudrate=9600, timeout=1)
        
        voltage = read_pzem_register(ser, PZEM_VOLTAGE_CMD)
        current = read_pzem_register(ser, PZEM_CURRENT_CMD)
        power = read_pzem_register(ser, PZEM_POWER_CMD)
        energy = read_pzem_register(ser, PZEM_ENERGY_CMD)
        
        ser.close()
        
        # Convert to proper units (divide by 10 for voltage and current, divide by 10 for power)
        result = {}
        if voltage is not None:
            result['voltage'] = voltage / 10.0  # V
        if current is not None:
            result['current'] = current / 100.0  # A
        if power is not None:
            result['power'] = power / 10.0  # W
        if energy is not None:
            result['energy'] = energy / 100.0  # kWh
        
        if result:
            return result
        else:
            return {"error": "No valid data from sensor"}
    except Exception as e:
        return {"error": str(e)}

def read_all_pzem():
    """
    Reads all connected PZEM sensors and returns a list of readings.
    """
    readings = []
    for port in ports:
        readings.append(read_pzem(port))
    return readings
 