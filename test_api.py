"""
Simple script to test the rate limiting API endpoints.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_ping():
    """Test the ping endpoint."""
    print("=" * 50)
    print("Testing GET /api/ping/")
    print("=" * 50)
    
    for i in range(6):
        try:
            response = requests.get(f"{BASE_URL}/api/ping/")
            print(f"Request {i+1}: Status {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print()
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure it's running:")
            print("  python manage.py runserver")
            return
        except Exception as e:
            print(f"Error: {e}")
            return

def test_custom_limit():
    """Test the custom limit endpoint."""
    print("=" * 50)
    print("Testing POST /api/custom-limit/")
    print("=" * 50)
    
    data = {
        "identifier": "test_user_123",
        "limit": 3,
        "window": 60
    }
    
    for i in range(4):
        try:
            response = requests.post(
                f"{BASE_URL}/api/custom-limit/",
                json=data
            )
            print(f"Request {i+1}: Status {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print()
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server.")
            return
        except Exception as e:
            print(f"Error: {e}")
            return

def test_stats():
    """Test the stats endpoint."""
    print("=" * 50)
    print("Testing GET /api/stats/<identifier>/")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats/test_user_123/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("\n🚀 Testing Rate Limiter API\n")
    print("Make sure the server is running: python manage.py runserver\n")
    
    test_ping()
    print("\n")
    test_custom_limit()
    print("\n")
    test_stats()
    
    print("\n✅ Testing complete!")


