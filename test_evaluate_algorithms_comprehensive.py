import requests
import json

def test_valid_data():
    """Test with valid complete data"""
    url = "http://localhost:8000/api/v1/timetable/evaluate-algorithms"
    
    test_data = {
        "scores": {
            "GA": {
                "average_score": 85.5,
                "conflicts": 2.0,
                "room_utilization": 78.3,
                "period_distribution": 92.1
            },
            "CO": {
                "average_score": 78.2,
                "conflicts": 3.5,
                "room_utilization": 82.1,
                "period_distribution": 88.7
            },
            "RL": {
                "average_score": 82.8,
                "conflicts": 2.8,
                "room_utilization": 75.9,
                "period_distribution": 89.3
            }
        }
    }
    
    print("🧪 Testing with valid complete data...")
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Source: {result.get('source', 'unknown')}")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Analysis preview: {result.get('analysis', '')[:100]}...")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_missing_fields():
    """Test with missing required fields"""
    url = "http://localhost:8000/api/v1/timetable/evaluate-algorithms"
    
    test_data = {
        "scores": {
            "GA": {
                "average_score": 85.5,
                "conflicts": 2.0,
                # Missing room_utilization and period_distribution
            },
            "CO": {
                "average_score": 78.2,
                "conflicts": 3.5,
                "room_utilization": 82.1,
                "period_distribution": 88.7
            }
        }
    }
    
    print("\n🧪 Testing with missing required fields...")
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Correctly rejected invalid data!")
            print(f"Error: {response.text}")
            return True
        else:
            print(f"❌ Should have returned 422, got: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_empty_scores():
    """Test with empty scores"""
    url = "http://localhost:8000/api/v1/timetable/evaluate-algorithms"
    
    test_data = {
        "scores": {}
    }
    
    print("\n🧪 Testing with empty scores...")
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Handled empty data gracefully!")
            print(f"Analysis: {result.get('analysis', '')}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_non_target_algorithms():
    """Test with algorithms other than GA, RL, CO"""
    url = "http://localhost:8000/api/v1/timetable/evaluate-algorithms"
    
    test_data = {
        "scores": {
            "PSO": {
                "average_score": 85.5,
                "conflicts": 2.0,
                "room_utilization": 78.3,
                "period_distribution": 92.1
            },
            "BC": {
                "average_score": 78.2,
                "conflicts": 3.5,
                "room_utilization": 82.1,
                "period_distribution": 88.7
            }
        }
    }
    
    print("\n🧪 Testing with non-target algorithms (PSO, BC)...")
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Handled non-target algorithms!")
            print(f"Analysis: {result.get('analysis', '')}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Comprehensive Testing of evaluate-algorithms endpoint")
    print("=" * 60)
    
    tests = [
        test_valid_data,
        test_missing_fields,
        test_empty_scores,
        test_non_target_algorithms
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main() 