import os
import time
import statistics
import RPi.GPIO as GPIO
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----------------------------
# CONFIG
# ----------------------------
TRIG_PIN = 25   # BCM GPIO23 (physical pin 16)
ECHO_PIN = 24   # BCM GPIO24 (physical pin 18) <-- use a voltage divider/level shifter if echo is 5V

# Trash bin calibration (in centimeters)
EMPTY_DISTANCE_CM = 60.0
FULL_DISTANCE_CM = 10.0

# Sampling
SAMPLES = 7
SAMPLE_DELAY = 0.08  # seconds between samples

# Env-var driven config
SEND_HTTP = True
BACKEND_URL = os.environ.get("BACKEND_URL", "https://shpec4c-production.up.railway.app/telemetry")
BIN_ID = os.environ.get("BIN_ID", "bin-01")

# HC-SR04-ish constants
SPEED_OF_SOUND_CM_S = 34300.0  # cm/s at ~20°C
TIMEOUT_S = 0.03               # ~30ms covers up to ~5m round trip; you can lower since bins are close

# ----------------------------
# GPIO SETUP
# ----------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

GPIO.output(TRIG_PIN, GPIO.LOW)
time.sleep(0.1)  # settle sensor

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def distance_cm():
    """
    Trigger ultrasonic pulse and measure echo time.
    Returns distance in cm, or None on timeout.
    """
    # Send 10us trigger pulse
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # Wait for echo to go HIGH (start)
    start_wait = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        if time.time() - start_wait > TIMEOUT_S:
            return None
    pulse_start = time.time()

    # Wait for echo to go LOW (end)
    end_wait = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        if time.time() - end_wait > TIMEOUT_S:
            return None
    pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start  # seconds

    # Distance: (time * speed_of_sound) / 2
    d_cm = (pulse_duration * SPEED_OF_SOUND_CM_S) / 2.0

    # Basic sanity filter (tweak if needed)
    if d_cm <= 0 or d_cm > 400:  # many sensors are reliable up to ~400cm
        return None

    return d_cm

def smoothed_distance_cm():
    readings = []
    for _ in range(SAMPLES):
        d = distance_cm()
        if d is not None:
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
    print("Starting ultrasonic monitoring (RPi.GPIO)...")
    try:
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
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
