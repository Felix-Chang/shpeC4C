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
│   └── requirements.txt
├── backend/          FastAPI server
│   ├── main.py
│   └── requirements.txt
├── frontend/         React + TypeScript dashboard
│   ├── src/
│   ├── .env.example
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
|--------|------------------|--------------------------------|
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

| HC-SR04 Pin | RPi GPIO         |
|-------------|------------------|
| Trig        | GPIO 23 (pin 16) |
| Echo        | GPIO 24 (pin 18) |
| VCC         | 5V               |
| GND         | GND              |

The Echo pin outputs 5V. Use a voltage divider (1k / 2k resistors) to bring it down to 3.3V for the Pi's GPIO input.

### Software

```bash
cd sensor
pip install -r requirements.txt
python main.py
```

### Configuration

Set these environment variables to override defaults:

| Variable      | Default                                                    | Description              |
|---------------|------------------------------------------------------------|--------------------------|
| `BACKEND_URL` | `https://shpec4c-production.up.railway.app/telemetry`      | Telemetry POST endpoint  |
| `BIN_ID`      | `bin-01`                                                   | Identifier for this bin  |

The sensor takes 7 readings per cycle using a median filter, then sends the smoothed distance and calculated fill percentage to the backend every second.

### Calibration

In `sensor/main.py`, adjust these values to match your bin dimensions:

- `EMPTY_DISTANCE_CM` -- Distance from sensor to bottom of an empty bin (default: 60 cm)
- `FULL_DISTANCE_CM` -- Distance when the bin is considered full (default: 10 cm)

## License

This project was built for the SHPE Code4Change hackathon.
