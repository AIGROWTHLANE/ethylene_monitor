import serial
import time
import requests
from datetime import datetime
from collections import deque

# -------------------------------
# Configuration
# -------------------------------
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
API_URL = "https://l9z9cprk71.execute-api.us-east-1.amazonaws.com/prod/storeEthyleneData"
ROLLING_WINDOW_SIZE = 5
DISCONNECTED_THRESHOLD = 0.3  # Volts
STATION_ID = "pi-lab-1"  # <-- Adjust to match your deployment

# Rolling window
voltage_window = deque(maxlen=ROLLING_WINDOW_SIZE)

# -------------------------------
# Serial Reader
# -------------------------------
def read_serial_line(ser):
    try:
        line = ser.readline().decode().strip()
        print(f"[DEBUG] Serial Line: {line}")
        return line
    except Exception as e:
        print(f"[ERROR] Serial read failed: {e}")
        return None

# -------------------------------
# Data Parser
# -------------------------------
def parse_sensor_data(line):
    try:
        if "Raw:" in line and "Voltage:" in line:
            parts = line.split("|")
            voltage_part = parts[1].strip()
            voltage = float(voltage_part.replace("Voltage:", "").replace("V", "").strip())
            return voltage
    except Exception as e:
        print(f"[ERROR] Parsing failed: {e}")
    return None

# -------------------------------
# AWS Sender
# -------------------------------
def send_to_aws(ethylene_ppm):
    payload = {
        "station_id": STATION_ID,
        "timestamp": datetime.utcnow().isoformat(),
        "ethylene_ppm": f"{ethylene_ppm:.2f}"
    }
    try:
        print(f"[DEBUG] Sending: {payload}")
        response = requests.post(API_URL, json=payload, timeout=5)
        print(f"[DEBUG] AWS: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] AWS send failed: {e}")
        return False

# -------------------------------
# Main Loop
# -------------------------------
def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"[INFO] Connected to {SERIAL_PORT}")

        while True:
            line = read_serial_line(ser)
            if not line:
                continue

            voltage = parse_sensor_data(line)
            if voltage is None:
                continue

            if voltage < DISCONNECTED_THRESHOLD:
                print("[WARNING] Sensor disconnected or unstable voltage.")
                continue

            voltage_window.append(voltage)
            avg_voltage = sum(voltage_window) / len(voltage_window)
            ethylene_ppm = avg_voltage * 8.5  # adjust if calibrated differently

            print(f"Voltage: {avg_voltage:.3f} V | Ethylene: {ethylene_ppm:.2f} ppm")

            send_to_aws(ethylene_ppm)
            time.sleep(2)

    except serial.SerialException as e:
        print(f"[ERROR] Serial error: {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Script manually stopped.")

# -------------------------------
if __name__ == "__main__":
    main()
