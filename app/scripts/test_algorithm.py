#!/usr/bin/env python3
"""
Algorithm Test Script
====================

This script tests our algorithms with the current data to understand
exactly what happens and what errors occur.
"""

import sys
import os
import traceback

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_algorithms2_data_loading():
    """Test the algorithms_2 data loading mechanism"""
    print("🧪 TESTING ALGORITHMS_2 DATA LOADING")
    print("=" * 50)
    
    try:
        from app.algorithms_2.Data_Loading import load_data
        print("✅ Successfully imported Data_Loading")
        
        # Try to load data
        print("\n📥 Attempting to load data...")
        data = load_data()
        
        print(f"✅ Data loaded successfully!")
        print(f"📊 Data type: {type(data)}")
        
        if hasattr(data, '__dict__'):
            print(f"📋 Data attributes: {list(data.__dict__.keys())}")
        elif isinstance(data, dict):
            print(f"📋 Data keys: {list(data.keys())}")
        elif isinstance(data, tuple):
            print(f"📋 Data tuple length: {len(data)}")
            for i, item in enumerate(data):
                print(f"   Item {i}: {type(item)}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return None

def test_simple_algorithm():
    """Test a simple algorithm with current data"""
    print("\n🧬 TESTING SIMPLE ALGORITHM")
    print("=" * 50)
    
    try:
        # Try to import and run a simple algorithm
        from app.algorithms_2.runner import main as run_algorithm
        print("✅ Successfully imported algorithm runner")
        
        print("\n🚀 Attempting to run algorithm...")
        result = run_algorithm()
        
        print(f"✅ Algorithm completed!")
        print(f"📊 Result type: {type(result)}")
        print(f"📋 Result: {str(result)[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error running algorithm: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return None

def test_generator_algorithm():
    """Test a generator algorithm"""
    print("\n🧬 TESTING GENERATOR ALGORITHM")
    print("=" * 50)
    
    try:
        # Try to test GA algorithm
        from app.generator.algorithms.ga.ga import generate_ga
        print("✅ Successfully imported GA algorithm")
        
        print("\n🚀 Attempting to run GA...")
        result = generate_ga()
        
        print(f"✅ GA completed!")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, (list, tuple)) and len(result) > 0:
            print(f"📋 Result length: {len(result)}")
            print(f"📋 First item: {str(result[0])[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error running GA: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return None

def test_mongodb_connection():
    """Test MongoDB data collection"""
    print("\n🗄️ TESTING MONGODB CONNECTION")
    print("=" * 50)
    
    try:
        from app.generator.data_collector import get_spaces, get_activities
        print("✅ Successfully imported data collector")
        
        print("\n📥 Testing space collection...")
        spaces = get_spaces()
        print(f"✅ Spaces loaded: {len(spaces)} items")
        
        if spaces:
            print(f"📋 First space: {str(spaces[0])[:200]}...")
        
        print("\n📥 Testing activities collection...")
        activities = get_activities()
        print(f"✅ Activities loaded: {len(activities)} items")
        
        if activities:
            print(f"📋 First activity: {str(activities[0])[:200]}...")
        
        return {'spaces': spaces, 'activities': activities}
        
    except Exception as e:
        print(f"❌ Error testing MongoDB: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return None

def analyze_data_structure(data):
    """Analyze the structure of loaded data"""
    print("\n🔍 ANALYZING DATA STRUCTURE")
    print("=" * 50)
    
    if data is None:
        print("❌ No data to analyze")
        return
    
    try:
        if hasattr(data, 'spaces'):
            print(f"📊 Spaces: {len(data.spaces) if hasattr(data.spaces, '__len__') else 'Unknown'}")
        
        if hasattr(data, 'events'):
            print(f"📊 Events: {len(data.events) if hasattr(data.events, '__len__') else 'Unknown'}")
        
        if hasattr(data, 'time_slots'):
            print(f"📊 Time slots: {len(data.time_slots) if hasattr(data.time_slots, '__len__') else 'Unknown'}")
        
        if hasattr(data, 'groups'):
            print(f"📊 Groups: {len(data.groups) if hasattr(data.groups, '__len__') else 'Unknown'}")
        
        # Try to access specific attributes
        if hasattr(data, 'spaces') and data.spaces:
            first_space = list(data.spaces.values())[0] if hasattr(data.spaces, 'values') else data.spaces[0]
            print(f"📋 First space structure: {type(first_space)}")
            if hasattr(first_space, '__dict__'):
                print(f"   Attributes: {list(first_space.__dict__.keys())}")
        
    except Exception as e:
        print(f"❌ Error analyzing data structure: {e}")
        traceback.print_exc()

def main():
    """Main test function"""
    print("🧪 ALGORITHM AND DATA TESTING")
    print("=" * 60)
    
    # Test 1: Data loading
    data = test_algorithms2_data_loading()
    
    # Test 2: Analyze data structure
    if data:
        analyze_data_structure(data)
    
    # Test 3: Test MongoDB connection
    mongodb_data = test_mongodb_connection()
    
    # Test 4: Try to run a simple algorithm
    # algorithm_result = test_simple_algorithm()
    
    # Test 5: Try generator algorithm
    # ga_result = test_generator_algorithm()
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\n📋 SUMMARY:")
    print(f"   Data Loading: {'✅ Success' if data else '❌ Failed'}")
    print(f"   MongoDB: {'✅ Success' if mongodb_data else '❌ Failed'}")
    # print(f"   Algorithm: {'✅ Success' if algorithm_result else '❌ Failed'}")
    # print(f"   GA: {'✅ Success' if ga_result else '❌ Failed'}")

if __name__ == "__main__":
    main() 