#!/usr/bin/env python3
"""
MongoDB Data Analysis Script
============================

This script analyzes the current MongoDB database structure to understand
what data we have and what needs to be improved.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def test_mongodb_connection():
    """Test MongoDB connection and analyze data"""
    print("🗄️ MONGODB DATA ANALYSIS")
    print("=" * 50)
    
    try:
        from app.generator.data_collector import (
            get_collections, get_faculties, get_spaces, get_activities,
            get_modules, get_teachers, get_students, get_years,
            get_days, get_periods, get_timetables
        )
        
        print("✅ Successfully connected to MongoDB")
        
        # Get all collections
        collections = get_collections()
        print(f"\n📊 Available Collections: {collections}")
        
        # Analyze each data type
        print(f"\n📋 DATA SUMMARY:")
        print(f"   Faculties: {len(get_faculties())}")
        print(f"   Spaces: {len(get_spaces())}")
        print(f"   Activities: {len(get_activities())}")
        print(f"   Modules: {len(get_modules())}")
        print(f"   Teachers: {len(get_teachers())}")
        print(f"   Students: {len(get_students())}")
        print(f"   Years: {len(get_years())}")
        print(f"   Days: {len(get_days())}")
        print(f"   Periods: {len(get_periods())}")
        print(f"   Timetables: {len(get_timetables())}")
        
        # Sample data analysis
        print(f"\n🔍 SAMPLE DATA:")
        
        spaces = get_spaces()
        if spaces:
            print(f"   First Space: {spaces[0]}")
        else:
            print("   No spaces found!")
        
        activities = get_activities()
        if activities:
            print(f"   First Activity: {activities[0]}")
        else:
            print("   No activities found!")
        
        faculties = get_faculties()
        if faculties:
            print(f"   First Faculty: {faculties[0]}")
        else:
            print("   No faculties found!")
        
        return {
            'collections': collections,
            'spaces': spaces,
            'activities': activities,
            'faculties': faculties
        }
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return None

def identify_mongodb_issues(data):
    """Identify issues with the MongoDB data"""
    print(f"\n🚨 MONGODB ISSUES ANALYSIS")
    print("=" * 50)
    
    if not data:
        print("❌ Cannot analyze - no data available")
        return
    
    issues = []
    
    # Check for empty collections
    if len(data['spaces']) == 0:
        issues.append("🔴 CRITICAL: No spaces/rooms in database")
    
    if len(data['activities']) == 0:
        issues.append("🔴 CRITICAL: No activities to schedule")
    
    if len(data['faculties']) == 0:
        issues.append("🔴 CRITICAL: No faculties defined")
    
    # Check data structure
    if data['spaces']:
        space = data['spaces'][0]
        required_fields = ['name', 'capacity']
        missing_fields = [field for field in required_fields if field not in space]
        if missing_fields:
            issues.append(f"🟡 WARNING: Spaces missing fields: {missing_fields}")
    
    if issues:
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ No critical issues found")
    
    return issues

def main():
    """Main function"""
    print("🗄️ MONGODB DATABASE ANALYSIS")
    print("=" * 60)
    
    # Test connection and get data
    data = test_mongodb_connection()
    
    # Identify issues
    issues = identify_mongodb_issues(data)
    
    print("\n" + "=" * 60)
    print("✅ MONGODB ANALYSIS COMPLETE")
    print("=" * 60)
    
    if issues:
        print(f"\n🎯 NEXT STEPS:")
        print("1. Fix the identified critical issues")
        print("2. Populate missing data in MongoDB")
        print("3. Ensure data structure matches algorithm requirements")
        print("4. Test algorithms with improved MongoDB data")

if __name__ == "__main__":
    main() 