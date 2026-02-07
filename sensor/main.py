import os
import time
import statistics
from gpiozero import DistanceSensor
import requests

# ----------------------------
# CONFIG
# ----------------------------
TRIG_PIN = 23   # GPIO23 (physical pin 16)
ECHO_PIN = 24   # GPIO24 (physical pin 18)  <-- through voltage divider/level shifter if echo is 5V

# Trash bin calibration (in centimeters)
EMPTY_DISTANCE_CM = 60.0
FULL_DISTANCE_CM = 10.0

# Sampling
SAMPLES = 7
SAMPLE_DELAY = 0.08  # seconds between samples

# Env-var driven config
SEND_HTTP = True
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/telemetry")
BIN_ID = os.environ.get("BIN_ID", "wpb-bin-01")

# ----------------------------
# SETUP SENSOR
# ----------------------------
sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=2.0)  # 2.0m max

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def distance_cm():
    meters = sensor.distance * sensor.max_distance
    return meters * 100.0

def smoothed_distance_cm():
    readings = []
    for _ in range(SAMPLES):
        d = distance_cm()
        if d > 0:
            readings.append(d)
        time.sleep(SAMPLE_DELAY)

    if not readings:
        return None

    return statistics.median(readings)

def fill_percent_from_distance(d_cm):
    if d_cm is None:
        return None

    fill = (EMPTY_DISTANCE_CM - d_cm) / (EMPTY_DISTANCE_CM - FULL_DISTANCE_CM) * 100.0
    return clamp(fill, 0.0, 100.0)

def send_to_backend(d_cm, fill_pct):
    payload = {
        "bin_id": BIN_ID,
        "distance_cm": d_cm,
        "fill_percent": fill_pct,
        "ts": time.time(),
    }
    try:
        r = requests.post(BACKEND_URL, json=payload, timeout=3)
        r.raise_for_status()
        print(f"Sent: {payload}")
    except Exception as e:
        print(f"Send failed: {e}")

def main():
    print("Starting ultrasonic monitoring...")
    while True:
        d = smoothed_distance_cm()
        fill = fill_percent_from_distance(d)

        if d is None or fill is None:
            print("No valid reading")
        else:
            print(f"Distance: {d:6.1f} cm | Fill: {fill:5.1f}%")

            if SEND_HTTP:
                send_to_backend(d, fill)

        time.sleep(1.0)

if __name__ == "__main__":
    main()
