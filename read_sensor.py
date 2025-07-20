import serial
import time

# Update with your correct port (e.g., /dev/ttyUSB0 or /dev/ttyACM0)
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset

    print("Connected to Arduino on", SERIAL_PORT)
    print("Reading ethylene sensor data...\n")

    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print("Received:", line)

except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
import serial
import time

# Update with your correct port (e.g., /dev/ttyUSB0 or /dev/ttyACM0)
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset

    print("Connected to Arduino on", SERIAL_PORT)
    print("Reading ethylene sensor data...\n")

    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print("Received:", line)

except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
