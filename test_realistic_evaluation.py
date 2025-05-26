import requests
import json

def test_realistic_timetable_data():
    """Test with realistic timetable evaluation data"""
    url = "http://localhost:8000/api/v1/timetable/evaluate-algorithms"
    
    # Data matching the user's example
    test_data = {
        "scores": {
            "GA": {
                "average_score": 17.4,
                "conflicts": 0.0,
                "room_utilization": 11.6,
                "period_distribution": 100.0
            },
            "CO": {
                "average_score": 24.1,
                "conflicts": 1.0,
                "room_utilization": 11.8,
                "period_distribution": 100.0
            },
            "RL": {
                "average_score": 26.1,
                "conflicts": 1.3,
                "room_utilization": 13.1,
                "period_distribution": 100.0
            }
        }
    }
    
    print("🧪 Testing with realistic timetable evaluation data...")
    print(f"URL: {url}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"\nSource: {result.get('source', 'unknown')}")
            print(f"Status: {result.get('status', 'unknown')}")
            print("\n" + "="*60)
            print("ANALYSIS RESULT:")
            print("="*60)
            print(result.get('analysis', ''))
            print("="*60)
            return result
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = test_realistic_timetable_data() 