import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ----------------------------
# MODELS
# ----------------------------

class TelemetryIn(BaseModel):
    bin_id: str
    distance_cm: float
    fill_percent: float
    ts: float

class BinInfo(BaseModel):
    bin_id: str
    name: str
    lat: float
    lng: float
    distance_cm: float
    fill_percent: float
    ts: float

# ----------------------------
# STATIC REGISTRY  (TODO: fill in real names + coordinates)
# ----------------------------

BIN_REGISTRY: dict[str, dict] = {
    "bin-01": {"name": "Marston Library",     "lat": 29.6481, "lng": -82.3436},
    "bin-02": {"name": "Reitz Union",        "lat": 29.6462, "lng": -82.3479},
    "bin-03": {"name": "Plaza of the Americas", "lat": 29.6510, "lng": -82.3418},
    "bin-04": {"name": "Ben Hill Griffin Stadium", "lat": 29.6500, "lng": -82.3486},
    "bin-05": {"name": "Turlington Hall",    "lat": 29.6494, "lng": -82.3428},
    "bin-06": {"name": "Hub / CSE Building", "lat": 29.6483, "lng": -82.3440},
}

# ----------------------------
# IN-MEMORY TELEMETRY STORE + SEED DATA
# ----------------------------

def _seed_entry(fill_pct: float) -> dict:
    empty_dist = 60.0
    full_dist = 10.0
    distance = empty_dist - (fill_pct / 100.0) * (empty_dist - full_dist)
    return {
        "distance_cm": round(distance, 1),
        "fill_percent": fill_pct,
        "ts": time.time(),
    }

telemetry_store: dict[str, dict] = {
    "bin-01": _seed_entry(15.0),
    "bin-02": _seed_entry(42.0),
    "bin-03": _seed_entry(78.0),
    "bin-04": _seed_entry(91.0),
    "bin-05": _seed_entry(5.0),
    "bin-06": _seed_entry(63.0),
}

# ----------------------------
# HELPERS
# ----------------------------

def build_bin_info(bin_id: str) -> BinInfo:
    reg = BIN_REGISTRY[bin_id]
    tel = telemetry_store.get(bin_id, {"distance_cm": 0.0, "fill_percent": 0.0, "ts": 0.0})
    return BinInfo(
        bin_id=bin_id,
        name=reg["name"],
        lat=reg["lat"],
        lng=reg["lng"],
        distance_cm=tel["distance_cm"],
        fill_percent=tel["fill_percent"],
        ts=tel["ts"],
    )

# ----------------------------
# APP
# ----------------------------

app = FastAPI(title="Smart Waste Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# ENDPOINTS
# ----------------------------

@app.post("/telemetry")
def receive_telemetry(data: TelemetryIn):
    telemetry_store[data.bin_id] = {
        "distance_cm": data.distance_cm,
        "fill_percent": data.fill_percent,
        "ts": data.ts,
    }
    return {"status": "ok", "bin_id": data.bin_id}

@app.get("/bins", response_model=list[BinInfo])
def get_bins():
    return [build_bin_info(bid) for bid in BIN_REGISTRY]

@app.get("/bins/{bin_id}", response_model=BinInfo)
def get_bin(bin_id: str):
    if bin_id not in BIN_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")
    return build_bin_info(bin_id)

# ----------------------------
# RUN
# ----------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
