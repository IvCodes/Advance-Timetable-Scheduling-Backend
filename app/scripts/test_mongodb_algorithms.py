#!/usr/bin/env python3
"""
MongoDB Algorithm Testing Script
===============================

This script tests the algorithms with the current MongoDB data to identify
specific errors and issues.
"""

import sys
import os
import traceback

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def test_data_collection():
    """Test data collection from MongoDB"""
    print("📥 TESTING MONGODB DATA COLLECTION")
    print("=" * 50)
    
    try:
        from app.generator.data_collector import (
            get_collections, get_faculties, get_spaces, get_activities,
            get_modules, get_teachers, get_students, get_years,
            get_days, get_periods, get_timetables
        )
        
        print("✅ Successfully imported data collector")
        
        # Test each data collection function
        collections = get_collections()
        print(f"📊 Collections: {collections}")
        
        spaces = get_spaces()
        print(f"🏢 Spaces: {len(spaces)} found")
        if spaces:
            print(f"   Sample: {spaces[0]}")
        
        activities = get_activities()
        print(f"📅 Activities: {len(activities)} found")
        if activities:
            print(f"   Sample: {activities[0]}")
        
        teachers = get_teachers()
        print(f"👨‍🏫 Teachers: {len(teachers)} found")
        if teachers:
            print(f"   Sample: {teachers[0].get('first_name', 'N/A')} {teachers[0].get('last_name', 'N/A')}")
        
        years = get_years()
        print(f"📚 Years: {len(years)} found")
        if years:
            print(f"   Sample: {years[0]}")
        
        days = get_days()
        print(f"📆 Days: {len(days)} found")
        if days:
            print(f"   Sample: {days[0]}")
        
        periods = get_periods()
        print(f"⏰ Periods: {len(periods)} found")
        if periods:
            print(f"   Sample: {periods[0]}")
        
        return {
            'spaces': spaces,
            'activities': activities,
            'teachers': teachers,
            'years': years,
            'days': days,
            'periods': periods
        }
        
    except Exception as e:
        print(f"❌ Error in data collection: {e}")
        traceback.print_exc()
        return None

def test_generator_ga_algorithm(data):
    """Test the GA algorithm from generator"""
    print("\n🧬 TESTING GENERATOR GA ALGORITHM")
    print("=" * 50)
    
    if not data:
        print("❌ No data available for testing")
        return None
    
    try:
        # Try to import and run GA
        from app.generator.algorithms.ga.ga import generate_ga
        print("✅ Successfully imported GA algorithm")
        
        print("🚀 Attempting to run GA with MongoDB data...")
        result = generate_ga()
        
        print(f"✅ GA completed successfully!")
        print(f"📊 Result type: {type(result)}")
        if result is not None and hasattr(result, '__len__'):
            print(f"📋 Result length: {len(result)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in GA algorithm: {e}")
        traceback.print_exc()
        return None

def test_generator_co_algorithm(data):
    """Test the Colony Optimization algorithm from generator"""
    print("\n🐜 TESTING GENERATOR CO ALGORITHM")
    print("=" * 50)
    
    if not data:
        print("❌ No data available for testing")
        return None
    
    try:
        # Try to import and run CO
        from app.generator.algorithms.co.co import generate_co
        print("✅ Successfully imported CO algorithm")
        
        print("🚀 Attempting to run CO with MongoDB data...")
        result = generate_co()
        
        print(f"✅ CO completed successfully!")
        print(f"📊 Result type: {type(result)}")
        if result is not None and hasattr(result, '__len__'):
            print(f"📋 Result length: {len(result)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in CO algorithm: {e}")
        traceback.print_exc()
        return None

def analyze_data_structure_issues(data):
    """Analyze potential data structure issues"""
    print("\n🔍 ANALYZING DATA STRUCTURE ISSUES")
    print("=" * 50)
    
    if not data:
        print("❌ No data to analyze")
        return
    
    issues = []
    
    # Check activities structure
    if data['activities']:
        activity = data['activities'][0]
        print(f"📋 Activity structure: {list(activity.keys())}")
        
        # Check for missing fields that algorithms might expect
        expected_fields = [
            'space_requirements', 'type', 'room_type', 
            'capacity_needed', 'equipment_needed'
        ]
        
        missing_fields = [field for field in expected_fields if field not in activity]
        if missing_fields:
            issues.append(f"Activities missing fields: {missing_fields}")
    
    # Check spaces structure
    if data['spaces']:
        space = data['spaces'][0]
        print(f"🏢 Space structure: {list(space.keys())}")
        
        # Check for missing fields
        expected_space_fields = ['type', 'equipment', 'room_type']
        missing_space_fields = [field for field in expected_space_fields if field not in space]
        if missing_space_fields:
            issues.append(f"Spaces missing fields: {missing_space_fields}")
    
    # Check if activities reference valid subgroups
    if data['activities'] and data['years']:
        activity_subgroups = set()
        for activity in data['activities']:
            if 'subgroup_ids' in activity:
                activity_subgroups.update(activity['subgroup_ids'])
        
        valid_subgroups = set()
        for year in data['years']:
            if 'subgroups' in year:
                for subgroup in year['subgroups']:
                    valid_subgroups.add(subgroup.get('code', ''))
        
        invalid_subgroups = activity_subgroups - valid_subgroups
        if invalid_subgroups:
            issues.append(f"Activities reference invalid subgroups: {invalid_subgroups}")
    
    # Report issues
    if issues:
        print("🚨 Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No obvious data structure issues found")
    
    return issues

def test_simple_scheduling_logic():
    """Test basic scheduling logic"""
    print("\n⚙️ TESTING BASIC SCHEDULING LOGIC")
    print("=" * 50)
    
    try:
        # Try to create a simple schedule manually
        from app.generator.data_collector import get_spaces, get_activities, get_days, get_periods
        
        spaces = get_spaces()
        activities = get_activities()
        days = get_days()
        periods = get_periods()
        
        print(f"📊 Available resources:")
        print(f"   Spaces: {len(spaces)}")
        print(f"   Activities: {len(activities)}")
        print(f"   Days: {len(days)}")
        print(f"   Periods: {len(periods)}")
        print(f"   Total time slots: {len(days) * len(periods)}")
        
        # Calculate basic scheduling feasibility
        total_time_slots = len(days) * len(periods)
        total_activity_duration = sum(activity.get('duration', 1) for activity in activities)
        
        print(f"📈 Scheduling analysis:")
        print(f"   Total time slots available: {total_time_slots}")
        print(f"   Total activity duration needed: {total_activity_duration}")
        print(f"   Utilization: {(total_activity_duration / total_time_slots * 100):.1f}%")
        
        if total_activity_duration > total_time_slots:
            print("🚨 WARNING: Not enough time slots for all activities!")
        else:
            print("✅ Sufficient time slots available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in scheduling logic test: {e}")
        traceback.print_exc()
        return False

def main():
    """Main testing function"""
    print("🧪 MONGODB ALGORITHM TESTING")
    print("=" * 60)
    
    # Step 1: Test data collection
    data = test_data_collection()
    
    # Step 2: Analyze data structure
    if data:
        analyze_data_structure_issues(data)
    
    # Step 3: Test basic scheduling logic
    test_simple_scheduling_logic()
    
    # Step 4: Test GA algorithm
    ga_result = test_generator_ga_algorithm(data)
    
    # Step 5: Test CO algorithm
    co_result = test_generator_co_algorithm(data)
    
    print("\n" + "=" * 60)
    print("✅ ALGORITHM TESTING COMPLETE")
    print("=" * 60)
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print(f"   Data Collection: {'✅ Success' if data else '❌ Failed'}")
    print(f"   GA Algorithm: {'✅ Success' if ga_result is not None else '❌ Failed'}")
    print(f"   CO Algorithm: {'✅ Success' if co_result is not None else '❌ Failed'}")

if __name__ == "__main__":
    main() 