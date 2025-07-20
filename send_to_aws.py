import serial
import time
import requests
import json
from datetime import datetime
from collections import deque

# Configuration
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
API_URL = "https://l9z9cprk71.execute-api.us-east-1.amazonaws.com/prod/storeEthyleneData"
ROLLING_WINDOW_SIZE = 5
DISCONNECTED_THRESHOLD = 0.3  # Volts

# Initialize rolling window
voltage_window = deque(maxlen=ROLLING_WINDOW_SIZE)

def read_serial_line(ser):
    try:
        line = ser.readline().decode().strip()
        print(f"[DEBUG] Raw Serial Line: {line}")
        return line
    except Exception as e:
        print(f"[ERROR] Failed to read from serial: {e}")
        return None

def parse_sensor_data(line):
    try:
        if "Raw:" in line and "Voltage:" in line:
            parts = line.split("|")
            voltage_part = parts[1].strip()
            voltage = float(voltage_part.replace("Voltage:", "").replace("V", "").strip())
            return voltage
    except Exception as e:
        print(f"[ERROR] Failed to parse sensor line: {e}")
    return None

def send_to_aws(ethylene_ppm):
    try:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "ethylene_ppm": f"{ethylene_ppm:.2f}",
            "station_id": "RPI-1"  # Set your Pi's ID here
        }
        print(f"[DEBUG] Sending Payload: {payload}")
        response = requests.post(API_URL, json=payload)
        print(f"[DEBUG] AWS Response: {response.status_code}, {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Failed to send to AWS: {e}")
        return False

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"[INFO] Listening on {SERIAL_PORT}...")

        while True:
            line = read_serial_line(ser)
            if not line:
                continue

            voltage = parse_sensor_data(line)
            if voltage is None:
                continue

            if voltage < DISCONNECTED_THRESHOLD:
                print("[WARNING] Sensor disconnected or low voltage!")
                continue

            voltage_window.append(voltage)
            average_voltage = sum(voltage_window) / len(voltage_window)

            ethylene_ppm = average_voltage * 8.5  # Adjust based on your calibration

            print(f"Raw Voltage: {voltage:.3f} V | Ethylene (avg): {ethylene_ppm:.2f} ppm")

            send_to_aws(ethylene_ppm)
            time.sleep(2)

    except serial.SerialException as e:
        print(f"[ERROR] Serial port error: {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Script terminated by user.")

if __name__ == "__main__":
    main()
