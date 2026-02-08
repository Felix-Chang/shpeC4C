#!/usr/bin/env python3
"""
Admin CLI for managing waste bins.
Supports adding new bins with metadata and deleting bins.
"""
import os
import requests
import sys
import time
from datetime import datetime

# Backend URL - use Railway production or local
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://shpec4c-production.up.railway.app"  # Update with your Railway URL
)

def send_to_backend(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Send HTTP request to backend."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error communicating with backend: {e}")
        sys.exit(1)

def list_bins():
    """List all bins in the system."""
    print("\n📋 Fetching bin list...")
    bins = send_to_backend("/bins")

    if not bins:
        print("No bins registered in the system.")
        return

    print(f"\n{'Bin ID':<15} {'Name':<25} {'Fill %':<8} {'Status':<10}")
    print("=" * 70)

    for bin_data in bins:
        bin_id = bin_data["bin_id"]
        name = bin_data["name"]
        fill = bin_data["fill_percent"]

        # Determine status based on fill level
        if fill >= 80:
            status = "🔴 FULL"
        elif fill >= 50:
            status = "🟡 MEDIUM"
        else:
            status = "🟢 OK"

        print(f"{bin_id:<15} {name:<25} {fill:<8.1f} {status:<10}")

    print(f"\nTotal bins: {len(bins)}")

def add_bin():
    """Add a new bin with metadata."""
    print("\n➕ Add New Bin")
    print("=" * 50)

    # Get bin details from user
    bin_id = input("Bin ID (e.g., bin-07): ").strip()
    if not bin_id:
        print("❌ Bin ID cannot be empty")
        return

    name = input("Location Name (e.g., Norman Hall): ").strip()
    if not name:
        print("❌ Name cannot be empty")
        return

    try:
        lat = float(input("Latitude (e.g., 29.6475): ").strip())
        lng = float(input("Longitude (e.g., -82.3420): ").strip())
    except ValueError:
        print("❌ Invalid coordinates")
        return

    # Register bin metadata
    print(f"\n📝 Registering metadata for {bin_id}...")
    data = {
        "bin_id": bin_id,
        "name": name,
        "lat": lat,
        "lng": lng
    }
    result = send_to_backend("/bins/register", method="POST", data=data)

    if result["status"] == "created":
        print(f"✅ Bin {bin_id} created successfully!")
    else:
        print(f"✅ Bin {bin_id} metadata updated!")

    # Send initial telemetry
    print("\n📡 Initializing sensor data...")
    telemetry = {
        "bin_id": bin_id,
        "distance_cm": 60.0,  # Empty bin
        "fill_percent": 0.0,
        "ts": time.time()
    }
    send_to_backend("/telemetry", method="POST", data=telemetry)
    print(f"✅ Success: Telemetry sent for {bin_id}")

def delete_bin():
    """Delete a bin from the system."""
    print("\n🗑️  Delete Bin")
    print("=" * 50)

    bin_id = input("Bin ID to delete: ").strip()
    if not bin_id:
        print("❌ Bin ID cannot be empty")
        return

    # Confirm deletion
    confirm = input(f"⚠️  Confirm delete {bin_id}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Deletion cancelled")
        return

    # Delete bin
    print(f"\n🗑️  Deleting {bin_id}...")
    result = send_to_backend(f"/bins/{bin_id}", method="DELETE")
    print(f"✅ {result['status'].capitalize()}: {bin_id}")

def show_menu():
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("🗑️  Waste Management Admin Tool")
    print("=" * 50)
    print("1. List all bins")
    print("2. Add new bin")
    print("3. Delete bin")
    print("4. Exit")
    print("=" * 50)

def main():
    """Main menu loop."""
    print(f"Backend URL: {BACKEND_URL}")

    while True:
        show_menu()
        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            list_bins()
        elif choice == "2":
            add_bin()
        elif choice == "3":
            delete_bin()
        elif choice == "4":
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid option. Please select 1-4.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
