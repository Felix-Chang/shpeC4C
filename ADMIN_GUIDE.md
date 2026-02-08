# Admin Tool Guide

## Overview

The admin tool allows you to manage waste bins in the system - add new bins with complete metadata and delete bins when needed.

## Files

- **`sensor/admin.py`** - Interactive CLI admin tool
- **`backend/main.py`** - Contains the admin API endpoints

## API Endpoints

### POST /bins/register
Register or update bin metadata (name and location coordinates).

**Request:**
```json
{
  "bin_id": "bin-07",
  "name": "Norman Hall",
  "lat": 29.6475,
  "lng": -82.3420
}
```

**Response:**
```json
{
  "status": "created",  // or "updated" if bin already exists
  "bin_id": "bin-07"
}
```

**Behavior:**
- If bin doesn't exist: Creates new bin with metadata + initializes with 0% fill
- If bin exists: Updates name and location, preserves existing telemetry data
- Sets `last_emptied_at` to current time for new bins
- Initializes `distance_cm` to 60.0 (empty) and `fill_percent` to 0.0

### DELETE /bins/{bin_id}
Delete a bin from the system.

**Response:**
```json
{
  "status": "deleted",
  "bin_id": "bin-07"
}
```

**Behavior:**
- Returns 404 if bin doesn't exist
- Deletes bin document from `bins` collection
- Preserves telemetry history in `telemetry` collection for audit trail

## Using the Admin CLI

### 1. Configure Backend URL

The admin tool connects to your backend. Set the URL via environment variable:

```bash
# For local development
export BACKEND_URL=http://localhost:8000

# For production Railway deployment
export BACKEND_URL=https://your-app.up.railway.app
```

Or edit `BACKEND_URL` directly in `sensor/admin.py` (line 13).

### 2. Run the Admin Tool

```bash
cd sensor
python admin.py
```

### 3. Menu Options

```
1. List all bins       - Shows table of all registered bins with fill levels
2. Add new bin         - Register new bin with metadata + initial telemetry
3. Delete bin          - Remove bin from system (requires confirmation)
4. Exit               - Quit the tool
```

## Example Workflows

### Adding a New Bin

1. Select option **2** (Add new bin)
2. Enter bin details:
   ```
   Bin ID: bin-07
   Location Name: Norman Hall
   Latitude: 29.6475
   Longitude: -82.3420
   ```
3. Tool will:
   - Register metadata via `POST /bins/register`
   - Send initial telemetry (0% fill, 60cm distance)
   - Display success message

### Deleting a Bin

1. Select option **3** (Delete bin)
2. Enter bin ID to delete: `bin-07`
3. Confirm deletion: `y`
4. Tool will delete the bin via `DELETE /bins/{bin_id}`

### Listing Bins

1. Select option **1** (List all bins)
2. View table showing:
   - Bin ID
   - Location name
   - Current fill percentage
   - Status indicator (🟢 OK / 🟡 MEDIUM / 🔴 FULL)

## Backend Implementation Details

### Data Flow for New Bins

Before this feature:
```
Sensor → POST /telemetry → Bin auto-created with upsert=True
Problem: Missing name, location, last_emptied_at
```

After this feature:
```
Admin → POST /bins/register → Create bin with full metadata
                            → Initialize with 0% fill
Sensor → POST /telemetry → Update fill level
```

### MongoDB Schema

```json
{
  "bin_id": "bin-07",
  "name": "Norman Hall",
  "location": {"lat": 29.6475, "lng": -82.3420},
  "fill_percent": 0.0,
  "distance_cm": 60.0,
  "last_seen_at": 1770563300.28,
  "last_emptied_at": 1770563300.28
}
```

### Code Locations

**backend/main.py:**
- Line 36-40: `BinRegister` Pydantic model
- Line 225-258: `POST /bins/register` endpoint
- Line 260-271: `DELETE /bins/{bin_id}` endpoint

## Production Deployment

### Railway Backend

The admin tool works with your Railway-hosted backend. Just set:

```bash
export BACKEND_URL=https://your-railway-app.up.railway.app
```

### Security Considerations

⚠️ **Important:** These are admin-level endpoints without authentication.

For production, consider adding:
- API key authentication via headers
- Admin user authentication
- Rate limiting
- Audit logging of admin actions

Example quick fix (add to backend):
```python
API_KEY = os.getenv("ADMIN_API_KEY", "your-secret-key")

@app.post("/bins/register")
def register_bin(data: BinRegister, api_key: str = Header(None)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... rest of endpoint
```

## Testing

Run automated tests:

```bash
# Start backend
cd backend
source .venv/bin/activate
python main.py

# In another terminal, run tests
cd /Users/felixchang/Desktop/shpeC4C
python test_admin_endpoints.py
```

## Troubleshooting

### "Could not connect to backend"
- Verify backend is running: `curl http://localhost:8000/bins`
- Check BACKEND_URL is correct
- For Railway: verify app is deployed and URL is correct

### "Bin already exists"
- This is expected behavior - use option 1 to list bins first
- Delete the old bin if you want to recreate it

### Changes not appearing in frontend
- Frontend must fetch data from `/bins` endpoint
- Refresh the dashboard to see new bins
- Check browser console for API errors

## Future Enhancements

- [ ] Batch import from CSV: `admin.py import bins.csv`
- [ ] Update endpoint: `PATCH /bins/{bin_id}` for editing metadata
- [ ] Soft delete with `deleted: true` flag instead of hard delete
- [ ] Web-based admin dashboard (no CLI needed)
- [ ] Audit log: track who added/deleted bins and when
