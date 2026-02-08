import RPi.GPIO as GPIO
import time

# Pin configuration
TRIGGER_PIN = 25
ECHO_PIN = 24

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

def get_distance():
    # Ensure trigger is low
    GPIO.output(TRIGGER_PIN, False)
    time.sleep(0.1)

    # Send 10us pulse to trigger
    GPIO.output(TRIGGER_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIGGER_PIN, False)

    # Measure pulse duration on Echo pin
    start_time = time.time()
    stop_time = time.time()

    # Wait for echo to go HIGH
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    # Wait for echo to go LOW
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    # Calculate duration and distance
    # Speed of sound is ~34300 cm/s. 
    # Formula: (Time * Speed) / 2 (for round trip)
    duration = stop_time - start_time
    distance = (duration * 34300) / 2
    
    return distance

try:
    print("Starting Ultrasonic Sensor Test... Press Ctrl+C to stop.")
    while True:
        dist = get_distance()
        print(f"Distance: {dist:.2f} cm")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nMeasurement stopped by user.")
finally:
    GPIO.cleanup()
