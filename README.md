# BinSight

A smart waste management system that uses ultrasonic sensors on Raspberry Pi to monitor trash bin fill levels in real time. Bin data is sent to a cloud-hosted backend and displayed on a web dashboard with Google Maps integration and route optimization for collection crews.

## Overview

BinSight consists of three components:

- **Sensor** -- A Raspberry Pi with an HC-SR04 ultrasonic sensor mounted inside a trash bin. It measures the distance to the waste surface, calculates fill percentage, and sends telemetry to the backend over HTTP.
- **Backend** -- A FastAPI server that receives sensor telemetry, stores bin state in memory, and exposes a REST API for the frontend.
- **Frontend** -- A React + TypeScript dashboard that displays bin locations on a Google Map, color-coded by fill level. Includes a route planner that generates optimized pickup routes prioritizing the fullest bins.

## Goals

- Reduce unnecessary pickups by only dispatching collection when bins are full.
- Provide real-time visibility into bin fill levels across a campus or area.
- Optimize collection routes to minimize time and fuel usage.
- Demonstrate a low-cost IoT pipeline from sensor to cloud to dashboard.

## Project Structure

```
shpeC4C/
├── sensor/           Raspberry Pi sensor script
│   ├── main.py
│   ├── admin.py      Admin CLI for managing bins
│   ├── .env          Configuration file (create this!)
│   └── requirements.txt
├── backend/          FastAPI server
│   ├── main.py
│   ├── .env          Configuration file (create this!)
│   └── requirements.txt
├── frontend/         React + TypeScript dashboard
│   ├── src/
│   ├── .env          Configuration file (create this!)
│   └── package.json
└── README.md
```

## Running the Backend

Requires Python 3.10+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The server starts on `http://localhost:8000`. Available endpoints:

| Method | Path             | Description                    |
| ------ | ---------------- | ------------------------------ |
| POST   | `/telemetry`     | Receive a sensor reading       |
| GET    | `/bins`          | List all bins with latest data |
| GET    | `/bins/{bin_id}` | Get a single bin               |

For deployment, the backend is configured to run on Railway. A `Procfile` is needed:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Running the Frontend

Requires Node.js 18+.

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `.env` and fill in your values:

```
VITE_GOOGLE_MAPS_KEY=your_google_maps_api_key
VITE_API_URL=http://localhost:8000
```

The Google Maps API key must have the **Maps JavaScript API** enabled. Then start the dev server:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## Raspberry Pi Sensor Setup

### Hardware

- Raspberry Pi (any model with GPIO)
- HC-SR04 ultrasonic distance sensor
- Voltage divider or level shifter for the Echo pin (3.3V logic)

### Wiring

| HC-SR04 Pin | RPi GPIO |
| ----------- | -------- |
| Trig        | GPIO 25  |
| Echo        | GPIO 24  |
| VCC         | 5V       |
| GND         | GND      |

The Echo pin outputs 5V. Use a voltage divider (1k / 2k resistors) to bring it down to 3.3V for the Pi's GPIO input.

### Software

```bash
cd sensor
pip install -r requirements.txt
```

### Configuration

**Create a `.env` file** in the `sensor/` folder:

```bash
# sensor/.env
BACKEND_URL=http://localhost:8000
BIN_ID=bin-01
```

**Configuration Options:**

| Variable      | Default                                     | Description             |
| ------------- | ------------------------------------------- | ----------------------- |
| `BACKEND_URL` | `https://yourApp-production.up.railway.app` | Backend API base URL    |
| `BIN_ID`      | `bin-01`                                    | Identifier for this bin |

> **Note:** For `main.py`, the URL should NOT include `/telemetry` - the script appends it automatically. For local testing, use `BACKEND_URL=http://localhost:8000`.

**Start the sensor:**

```bash
python main.py
```

The sensor takes 7 readings per cycle using a median filter, then sends the smoothed distance and calculated fill percentage to the backend every second.

### Admin Tool

The sensor folder includes an admin CLI tool for managing bins remotely:

```bash
cd sensor
python admin.py
```

Features:

- **List bins** - View all bins with fill levels and status
- **Add bin** - Register new bins with metadata (name, location)
- **Delete bin** - Remove bins from the system

The admin tool uses the same `.env` configuration as the sensor script.

### Calibration

In `sensor/main.py`, adjust these values to match your bin dimensions:

- `EMPTY_DISTANCE_CM` -- Distance from sensor to bottom of an empty bin (default: 60 cm)
- `FULL_DISTANCE_CM` -- Distance when the bin is considered full (default: 10 cm)

## License

This project was built for the SHPE Code4Change hackathon.
