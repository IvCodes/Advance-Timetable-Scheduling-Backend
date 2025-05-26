"""
Test script for Enhanced Timetable API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Timetable API Endpoints")
    print("=" * 50)
    
    # Test health check
    test_endpoint("/api/enhanced-timetable/health")
    
    # Test dataset stats
    test_endpoint("/api/enhanced-timetable/dataset-stats")
    
    # Test algorithms
    test_endpoint("/api/enhanced-timetable/algorithms")
    
    # Test list files
    test_endpoint("/api/enhanced-timetable/list-generated-files")
    
    # Test generate test HTML
    test_endpoint("/api/enhanced-timetable/generate-test-html", "POST")
    
    # Test run algorithm
    test_data = {
        "algorithm": "nsga2",
        "mode": "quick",
        "generate_html": True
    }
    test_endpoint("/api/enhanced-timetable/run-algorithm", "POST", test_data)
    
    print("\n🏁 Testing completed!")

if __name__ == "__main__":
    main() 