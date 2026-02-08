import certifi
import math
import os
import time
import random
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from typing import Optional

load_dotenv()

# ----------------------------
# MONGODB CONNECTION
# ----------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["wastewise"]
bins_col = db["bins"]
telemetry_col = db["telemetry"]

# ----------------------------
# PYDANTIC MODELS
# ----------------------------

class TelemetryIn(BaseModel):
    bin_id: str
    distance_cm: float
    fill_percent: float
    ts: float

class BinOut(BaseModel):
    bin_id: str
    name: str
    lat: float
    lng: float
    distance_cm: float
    fill_percent: float
    ts: float
    last_emptied_at: Optional[float] = None

class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    weight: float

class RouteStop(BaseModel):
    bin_id: str
    name: str
    lat: float
    lng: float
    fill_percent: float
    priority: float
    order: int

class RouteOut(BaseModel):
    stops: list[RouteStop]
    polyline: list[list[float]]

# ----------------------------
# SEED DATA
# ----------------------------

BIN_REGISTRY: dict[str, dict] = {
    "bin-01": {"name": "Marston Library",          "lat": 29.6481, "lng": -82.3436},
    "bin-02": {"name": "Reitz Union",              "lat": 29.6462, "lng": -82.3479},
    "bin-03": {"name": "Plaza of the Americas",    "lat": 29.6505, "lng": -82.3427},
    "bin-04": {"name": "Ben Hill Griffin Stadium",  "lat": 29.6500, "lng": -82.3486},
    "bin-05": {"name": "Turlington Hall",          "lat": 29.6489, "lng": -82.3443},
    "bin-06": {"name": "Hub / CSE Building",       "lat": 29.6483, "lng": -82.3440},
}

SEED_FILLS: dict[str, float] = {
    "bin-01": 15.0,
    "bin-02": 42.0,
    "bin-03": 78.0,
    "bin-04": 91.0,
    "bin-05": 5.0,
    "bin-06": 63.0,
}

SEED_EMPTIED_HOURS_AGO: dict[str, float] = {
    "bin-01": 12.0,
    "bin-02": 18.0,
    "bin-03": 36.0,
    "bin-04": 48.0,
    "bin-05": 6.0,
    "bin-06": 24.0,
}


# ... (Your existing BIN_REGISTRY, SEED_FILLS, SEED_EMPTIED_HOURS_AGO from above) ...

def generate_campus_bins(existing_registry, count_to_add=30):
    new_registry = existing_registry.copy()
    new_fills = SEED_FILLS.copy()
    new_emptied = SEED_EMPTIED_HOURS_AGO.copy()
    
    # Get list of existing landmarks to cluster around
    landmarks = list(existing_registry.values())
    last_bin_id = len(existing_registry)

    for i in range(1, count_to_add + 1):
        # Pick a random landmark to place this new bin near (e.g., near Marston)
        parent = random.choice(landmarks)
        
        # Create a new ID
        new_id = f"bin-{last_bin_id + i:02d}"
        
        # Add slight random jitter to lat/lng (approx 10-50 meters)
        # 0.0001 deg is roughly 11 meters
        jitter_lat = random.uniform(-0.0005, 0.0005) 
        jitter_lng = random.uniform(-0.0005, 0.0005)
        
        # Generate varied names (e.g., "Marston Library - Zone B")
        suffixes = ["North Entrance", "South Exit", "Bus Stop", "2nd Floor", "Parking Lot", "Walkway"]
        new_name = f"{parent['name']} - {random.choice(suffixes)}"

        # Add to registry
        new_registry[new_id] = {
            "name": new_name,
            "lat": round(parent["lat"] + jitter_lat, 5),
            "lng": round(parent["lng"] + jitter_lng, 5)
        }

        # Generate random simulation data for the new bin
        new_fills[new_id] = round(random.uniform(0.0, 100.0), 1)
        new_emptied[new_id] = round(random.uniform(1.0, 72.0), 1)

    return new_registry, new_fills, new_emptied

# --- EXECUTION ---
full_registry, full_fills, full_emptied = generate_campus_bins(BIN_REGISTRY, 30)

# Print a sample to verify
print(f"Total Bins: {len(full_registry)}")
print("Sample of new bins:")
for k, v in list(full_registry.items())[-5:]: # Show last 5
    print(f"{k}: {v['name']} | Fill: {full_fills[k]}% | Last Empty: {full_emptied[k]}h ago")

# Route optimization: penalty points per kilometer of travel
# Higher values favor geographic proximity, lower values favor fill priority
# Recommended: 0.5 for campus-scale (0-2km), 0.1 for city-scale (5-10km)
DISTANCE_PENALTY_PER_KM = 0.5

def _fill_to_distance(fill_pct: float) -> float:
    empty_dist = 60.0
    full_dist = 10.0
    return round(empty_dist - (fill_pct / 100.0) * (empty_dist - full_dist), 1)

def seed_bins():
    """Upsert seed bins using $setOnInsert so live data is never overwritten."""
    now = time.time()
    for bin_id, info in BIN_REGISTRY.items():
        fill = SEED_FILLS[bin_id]
        hours_ago = SEED_EMPTIED_HOURS_AGO[bin_id]
        bins_col.update_one(
            {"bin_id": bin_id},
            {"$setOnInsert": {
                "name": info["name"],
                "location": {"lat": info["lat"], "lng": info["lng"]},
                "fill_percent": fill,
                "distance_cm": _fill_to_distance(fill),
                "last_seen_at": now,
                "last_emptied_at": now - hours_ago * 3600,
            }},
            upsert=True,
        )
    # Create indexes idempotently
    bins_col.create_index("bin_id", unique=True)
    telemetry_col.create_index([("bin_id", 1), ("ts", 1)])

# ----------------------------
# HELPERS
# ----------------------------

def doc_to_bin_out(doc: dict) -> BinOut:
    loc = doc.get("location", {})
    return BinOut(
        bin_id=doc["bin_id"],
        name=doc.get("name", "Unknown"),
        lat=loc.get("lat", 0.0),
        lng=loc.get("lng", 0.0),
        distance_cm=doc.get("distance_cm", 0.0),
        fill_percent=doc.get("fill_percent", 0.0),
        ts=doc.get("last_seen_at", 0.0),
        last_emptied_at=doc.get("last_emptied_at"),
    )

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ----------------------------
# APP
# ----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed the database
    seed_bins()
    yield
    # Shutdown: cleanup (if needed)

app = FastAPI(title="Smart Waste Management API", lifespan=lifespan)

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
    bins_col.update_one(
        {"bin_id": data.bin_id},
        {"$set": {
            "fill_percent": data.fill_percent,
            "distance_cm": data.distance_cm,
            "last_seen_at": data.ts,
        }},
        upsert=True,
    )
    telemetry_col.insert_one({
        "bin_id": data.bin_id,
        "distance_cm": data.distance_cm,
        "fill_percent": data.fill_percent,
        "ts": data.ts,
    })
    return {"status": "ok", "bin_id": data.bin_id}

@app.get("/bins", response_model=list[BinOut])
def get_bins():
    docs = bins_col.find()
    return [doc_to_bin_out(d) for d in docs]

@app.get("/bins/{bin_id}", response_model=BinOut)
def get_bin(bin_id: str):
    doc = bins_col.find_one({"bin_id": bin_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")
    return doc_to_bin_out(doc)

@app.post("/bins/{bin_id}/emptied", response_model=BinOut)
def mark_emptied(bin_id: str):
    now = time.time()
    doc = bins_col.find_one_and_update(
        {"bin_id": bin_id},
        {"$set": {"last_emptied_at": now, "fill_percent": 0.0, "distance_cm": _fill_to_distance(0.0)}},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")
    return doc_to_bin_out(doc)

@app.get("/heatmap", response_model=list[HeatmapPoint])
def get_heatmap(minutes: int = Query(default=120, ge=1)):
    cutoff = time.time() - minutes * 60
    pipeline = [
        {"$match": {"ts": {"$gte": cutoff}}},
        {"$group": {"_id": "$bin_id", "avg_fill": {"$avg": "$fill_percent"}}},
    ]
    agg_results = {r["_id"]: r["avg_fill"] for r in telemetry_col.aggregate(pipeline)}

    points = []
    for doc in bins_col.find():
        bin_id = doc["bin_id"]
        fill = agg_results.get(bin_id, doc.get("fill_percent", 0.0))
        loc = doc.get("location", {})
        points.append(HeatmapPoint(
            lat=loc.get("lat", 0.0),
            lng=loc.get("lng", 0.0),
            weight=round(fill / 100.0, 3),
        ))
    return points

@app.get("/route", response_model=RouteOut)
def get_route(
    start: str = Query(..., description="Starting bin_id"),
    end: str = Query(..., description="Ending bin_id"),
):
    all_docs = {d["bin_id"]: d for d in bins_col.find()}
    if start not in all_docs:
        raise HTTPException(status_code=404, detail=f"Start bin '{start}' not found")
    if end not in all_docs:
        raise HTTPException(status_code=404, detail=f"End bin '{end}' not found")

    now = time.time()

    def compute_priority(doc: dict) -> float:
        fill = doc.get("fill_percent", 0.0)
        emptied_at = doc.get("last_emptied_at")
        if emptied_at:
            hours_since = (now - emptied_at) / 3600.0
        else:
            hours_since = 48.0
        return 0.7 * (fill / 100.0) + 0.3 * min(hours_since / 24.0, 1.0)

    # Candidates: bins with fill >= 10%, excluding start and end
    candidates = {}
    for bid, doc in all_docs.items():
        if bid in (start, end):
            continue
        if doc.get("fill_percent", 0.0) >= 10.0:
            candidates[bid] = doc

    # Greedy route building
    route_ids = [start]
    current = all_docs[start]
    visited = {start}

    for _ in range(min(10, len(candidates))):
        best_bid = None
        best_score = -float("inf")
        cur_loc = current.get("location", {})
        cur_lat = cur_loc.get("lat", 0.0)
        cur_lng = cur_loc.get("lng", 0.0)

        for bid, doc in candidates.items():
            if bid in visited:
                continue
            loc = doc.get("location", {})
            dist_km = haversine_km(cur_lat, cur_lng, loc.get("lat", 0.0), loc.get("lng", 0.0))
            score = compute_priority(doc) - DISTANCE_PENALTY_PER_KM * dist_km
            if score > best_score:
                best_score = score
                best_bid = bid

        if best_bid is None:
            break
        visited.add(best_bid)
        route_ids.append(best_bid)
        current = candidates[best_bid]

    if end not in visited:
        route_ids.append(end)

    # Build response
    stops = []
    polyline = []
    for order, bid in enumerate(route_ids):
        doc = all_docs[bid]
        loc = doc.get("location", {})
        lat = loc.get("lat", 0.0)
        lng = loc.get("lng", 0.0)
        stops.append(RouteStop(
            bin_id=bid,
            name=doc.get("name", "Unknown"),
            lat=lat,
            lng=lng,
            fill_percent=doc.get("fill_percent", 0.0),
            priority=round(compute_priority(doc), 3),
            order=order,
        ))
        polyline.append([lat, lng])

    return RouteOut(stops=stops, polyline=polyline)

# ----------------------------
# RUN
# ----------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
