import random
import time

# ==========================================
# OS DETECTION & HARDWARE INIT
# ==========================================
try:
    from gpiozero import OutputDevice
    import Adafruit_DHT
    
    ON_PI = True
    print("[SYSTEM] Hardware Layer: Raspberry Pi detected. GPIO Active.")
    
    # Define GPIO Pins (BCM Numbering)
    # Most 5V Relay modules are "Active Low". 
    # If your relays work backwards (turn off when you say ON), change active_high to True.
    RELAY_LIGHT = OutputDevice(17, active_high=False, initial_value=False) 
    RELAY_FAN = OutputDevice(27, active_high=False, initial_value=False)
    RELAY_AC = OutputDevice(22, active_high=False, initial_value=False)
    
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 4 # Connected to BCM GPIO 4

except ImportError:
    ON_PI = False
    print("[WARNING] Hardware Layer: Windows detected. Simulating GPIO for testing.")

# ==========================================
# APPLIANCE CONTROL
# ==========================================
def control_appliance(device, state):
    """Turns physical relays ON or OFF."""
    if ON_PI:
        if device == "LIGHT":
            RELAY_LIGHT.on() if state == "ON" else RELAY_LIGHT.off()
        elif device == "FAN":
            RELAY_FAN.on() if state == "ON" else RELAY_FAN.off()
        elif device == "AC":
            RELAY_AC.on() if state == "ON" else RELAY_AC.off()
        print(f"[GPIO-EXEC] {device} relay set to {state}")
    else:
        print(f"[MOCK-EXEC] {device} turned {state}")

# ==========================================
# SENSOR READINGS
# ==========================================
def get_temperature():
    """Reads live data from DHT11 sensor."""
    if ON_PI:
        # DHT11 sensors can occasionally drop a reading, read_retry tries up to 15 times safely
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if temperature is not None:
            print(f"[GPIO-READ] Sensor read {temperature} C")
            return int(temperature)
        else:
            print("[GPIO-ERROR] Failed to read sensor. Using fallback.")
            return 25 # Safe fallback if the physical wire is loose during the demo
    else:
        mock_temp = random.randint(24, 28)
        print(f"[MOCK-READ] Read {mock_temp} C")
        return mock_temp