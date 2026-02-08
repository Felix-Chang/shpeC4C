#!/usr/bin/env python3
"""
Quick test script for the new admin endpoints.
Run this with the backend server running.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register_bin():
    """Test POST /bins/register"""
    print("\n=== Test 1: Register new bin ===")
    data = {
        "bin_id": "test-bin-99",
        "name": "Test Location",
        "lat": 29.65,
        "lng": -82.34
    }
    response = requests.post(f"{BASE_URL}/bins/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] in ["created", "updated"]
    return response.json()["bin_id"]

def test_get_bin(bin_id):
    """Test GET /bins/{bin_id}"""
    print(f"\n=== Test 2: Get bin {bin_id} ===")
    response = requests.get(f"{BASE_URL}/bins/{bin_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    bin_data = response.json()
    assert bin_data["bin_id"] == bin_id
    assert bin_data["name"] == "Test Location"
    assert bin_data["lat"] == 29.65
    assert bin_data["lng"] == -82.34

def test_update_bin():
    """Test updating existing bin metadata"""
    print("\n=== Test 3: Update existing bin ===")
    data = {
        "bin_id": "test-bin-99",
        "name": "Updated Location",
        "lat": 29.66,
        "lng": -82.35
    }
    response = requests.post(f"{BASE_URL}/bins/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "updated"

def test_delete_bin(bin_id):
    """Test DELETE /bins/{bin_id}"""
    print(f"\n=== Test 4: Delete bin {bin_id} ===")
    response = requests.delete(f"{BASE_URL}/bins/{bin_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_delete_nonexistent():
    """Test deleting non-existent bin"""
    print("\n=== Test 5: Delete non-existent bin ===")
    response = requests.delete(f"{BASE_URL}/bins/nonexistent-bin")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 404

def test_get_deleted_bin(bin_id):
    """Test that deleted bin returns 404"""
    print(f"\n=== Test 6: Get deleted bin {bin_id} ===")
    response = requests.get(f"{BASE_URL}/bins/{bin_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 404

if __name__ == "__main__":
    try:
        print("Testing Admin Endpoints")
        print("=" * 50)

        # Register a test bin
        bin_id = test_register_bin()

        # Verify it was created
        test_get_bin(bin_id)

        # Update its metadata
        test_update_bin()

        # Verify update worked
        test_get_bin(bin_id)

        # Delete the bin
        test_delete_bin(bin_id)

        # Test deleting non-existent bin
        test_delete_nonexistent()

        # Verify deletion
        test_get_deleted_bin(bin_id)

        print("\n" + "=" * 50)
        print("✅ All tests passed!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {BASE_URL}")
        print("Make sure the backend server is running:")
        print("  cd backend && source .venv/bin/activate && python main.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
