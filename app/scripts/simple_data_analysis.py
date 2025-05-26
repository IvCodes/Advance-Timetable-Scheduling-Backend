#!/usr/bin/env python3
"""
Simple Data Analysis Script for Timetable Scheduling System
===========================================================

This script analyzes the current data structure without complex imports.
"""

import json
import os
from collections import defaultdict

def analyze_algorithms2_dataset():
    """Analyze the algorithms_2 dataset"""
    print("🔍 ANALYZING ALGORITHMS_2 DATASET")
    print("=" * 50)
    
    dataset_path = "app/algorithms_2/sliit_computing_dataset.json"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset file not found: {dataset_path}")
        return {}
    
    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        print(f"\n📊 Dataset Structure: {list(data.keys())}")
        
        for key, value in data.items():
            print(f"\n📋 {key.upper()}:")
            if isinstance(value, list):
                print(f"   Count: {len(value)}")
                if value:
                    print(f"   Sample: {str(value[0])[:100]}...")
                    
                    # Special analysis for rooms
                    if key == 'rooms':
                        analyze_rooms(value)
                    elif key == 'events':
                        analyze_events(value)
                    elif key == 'time_slots':
                        analyze_time_slots(value)
                        
            else:
                print(f"   Type: {type(value)}")
                print(f"   Value: {str(value)[:100]}...")
        
        return data
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return {}

def analyze_rooms(rooms):
    """Analyze room data specifically"""
    print("\n   🏢 ROOM ANALYSIS:")
    
    if not rooms:
        print("     No rooms found!")
        return
    
    # Extract room information
    codes = []
    capacities = []
    types = []
    
    for room in rooms:
        if isinstance(room, dict):
            codes.append(room.get('code', 'Unknown'))
            capacities.append(room.get('capacity', 0))
            types.append(room.get('type', 'Unknown'))
    
    print(f"     Total rooms: {len(rooms)}")
    print(f"     Room codes: {codes}")
    print(f"     Capacity range: {min(capacities) if capacities else 0} - {max(capacities) if capacities else 0}")
    print(f"     Room types: {set(types)}")
    
    # Check for duplicates
    duplicates = [code for code in set(codes) if codes.count(code) > 1]
    if duplicates:
        print(f"     ⚠️  DUPLICATE CODES: {duplicates}")
        
        # Show duplicate details
        for dup_code in duplicates:
            dup_rooms = [r for r in rooms if r.get('code') == dup_code]
            print(f"       {dup_code}: {[r.get('capacity') for r in dup_rooms]} capacities")

def analyze_events(events):
    """Analyze event data specifically"""
    print("\n   📅 EVENT ANALYSIS:")
    
    if not events:
        print("     No events found!")
        return
    
    print(f"     Total events: {len(events)}")
    
    if events:
        sample_event = events[0]
        print(f"     Event structure: {list(sample_event.keys()) if isinstance(sample_event, dict) else 'Not a dict'}")

def analyze_time_slots(time_slots):
    """Analyze time slot data specifically"""
    print("\n   ⏰ TIME SLOT ANALYSIS:")
    
    if not time_slots:
        print("     No time slots found!")
        return
    
    print(f"     Total time slots: {len(time_slots)}")
    
    if time_slots:
        sample_slot = time_slots[0]
        print(f"     Time slot structure: {list(sample_slot.keys()) if isinstance(sample_slot, dict) else 'Not a dict'}")

def analyze_algorithm_files():
    """Analyze what algorithm files exist"""
    print("\n🧬 ALGORITHM FILE ANALYSIS")
    print("=" * 50)
    
    # Check generator algorithms
    print("\n📁 GENERATOR ALGORITHMS:")
    generator_path = "app/generator/algorithms"
    
    if os.path.exists(generator_path):
        for algo_type in ['ga', 'co', 'rl']:
            algo_dir = os.path.join(generator_path, algo_type)
            if os.path.exists(algo_dir):
                files = [f for f in os.listdir(algo_dir) if f.endswith('.py')]
                print(f"   {algo_type.upper()}: {files}")
            else:
                print(f"   {algo_type.upper()}: Directory not found")
    else:
        print("   Generator algorithms directory not found")
    
    # Check algorithms_2
    print("\n📁 ALGORITHMS_2:")
    algorithms2_path = "app/algorithms_2"
    
    if os.path.exists(algorithms2_path):
        py_files = [f for f in os.listdir(algorithms2_path) if f.endswith('.py')]
        print(f"   Main files: {py_files}")
        
        # Check RL subdirectory
        rl_path = os.path.join(algorithms2_path, "RL")
        if os.path.exists(rl_path):
            rl_files = [f for f in os.listdir(rl_path) if f.endswith('.py')]
            print(f"   RL files: {rl_files}")
    else:
        print("   Algorithms_2 directory not found")

def check_data_loading_mechanism():
    """Check how data is loaded in algorithms_2"""
    print("\n📥 DATA LOADING ANALYSIS")
    print("=" * 50)
    
    data_loading_file = "app/algorithms_2/Data_Loading.py"
    
    if os.path.exists(data_loading_file):
        print("✅ Data_Loading.py exists")
        
        try:
            with open(data_loading_file, 'r') as f:
                content = f.read()
            
            # Look for key patterns
            if 'sliit_computing_dataset.json' in content:
                print("✅ Uses sliit_computing_dataset.json")
            
            if 'load_data' in content:
                print("✅ Has load_data function")
                
            # Count lines to get file size
            lines = content.split('\n')
            print(f"📊 File size: {len(lines)} lines")
            
        except Exception as e:
            print(f"❌ Error reading Data_Loading.py: {e}")
    else:
        print("❌ Data_Loading.py not found")

def identify_critical_issues(dataset):
    """Identify critical issues that need fixing"""
    print("\n🚨 CRITICAL ISSUES IDENTIFIED")
    print("=" * 50)
    
    issues = []
    
    # Check room issues
    rooms = dataset.get('rooms', [])
    if len(rooms) < 5:
        issues.append(f"🔴 CRITICAL: Only {len(rooms)} rooms available - insufficient for complex scheduling")
    
    # Check for duplicate rooms
    if rooms:
        codes = [r.get('code', '') for r in rooms]
        duplicates = [code for code in set(codes) if codes.count(code) > 1]
        if duplicates:
            issues.append(f"🔴 CRITICAL: Duplicate room codes: {duplicates}")
    
    # Check events
    events = dataset.get('events', [])
    if len(events) == 0:
        issues.append("🔴 CRITICAL: No events to schedule")
    
    # Check time slots
    time_slots = dataset.get('time_slots', [])
    if len(time_slots) == 0:
        issues.append("🔴 CRITICAL: No time slots available")
    
    if issues:
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ No critical issues found")
    
    return issues

def generate_simple_recommendations(dataset, issues):
    """Generate simple, actionable recommendations"""
    print("\n💡 SIMPLE RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = []
    
    # Room recommendations
    rooms = dataset.get('rooms', [])
    if len(rooms) < 10:
        recommendations.append("1. 📈 Add more rooms to the dataset (aim for 10+ rooms)")
    
    # Duplicate room fix
    if any('Duplicate room codes' in issue for issue in issues):
        recommendations.append("2. 🔧 Fix duplicate room codes in sliit_computing_dataset.json")
    
    # Data structure recommendations
    recommendations.append("3. ✅ Add data validation before running algorithms")
    recommendations.append("4. 🔄 Ensure MongoDB data matches algorithms_2 data structure")
    recommendations.append("5. 📊 Test algorithms with current data to see actual performance")
    
    for rec in recommendations:
        print(f"   {rec}")

def main():
    """Main analysis function"""
    print("🔍 SIMPLE TIMETABLE SCHEDULING DATA ANALYSIS")
    print("=" * 60)
    
    # Analyze the main dataset
    dataset = analyze_algorithms2_dataset()
    
    # Analyze algorithm files
    analyze_algorithm_files()
    
    # Check data loading
    check_data_loading_mechanism()
    
    # Identify issues
    issues = identify_critical_issues(dataset)
    
    # Generate recommendations
    generate_simple_recommendations(dataset, issues)
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Fix the identified critical issues")
    print("2. Test current algorithms with existing data")
    print("3. Gradually improve data quality")
    print("4. Ensure algorithms can handle the current dataset")

if __name__ == "__main__":
    main() 