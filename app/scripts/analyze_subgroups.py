#!/usr/bin/env python3
"""
Subgroup Activity Analysis Script
================================

This script analyzes activities by subgroups to understand the real scheduling
constraints and why there are period conflicts.
"""

import sys
import os
from collections import defaultdict

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def analyze_activities_by_subgroup():
    """Analyze activities grouped by subgroups"""
    print("📊 SUBGROUP ACTIVITY ANALYSIS")
    print("=" * 50)
    
    try:
        from app.generator.data_collector import get_activities, get_days, get_periods, get_years
        
        activities = get_activities()
        days = get_days()
        periods = get_periods()
        years = get_years()
        
        # Filter non-interval periods
        non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
        
        print(f"📈 Basic Info:")
        print(f"   Total activities: {len(activities)}")
        print(f"   Available days: {len(days)}")
        print(f"   Non-interval periods: {len(non_interval_periods)}")
        print(f"   Total time slots: {len(days) * len(non_interval_periods)}")
        
        # Group activities by subgroup
        subgroup_activities = defaultdict(list)
        for activity in activities:
            for subgroup_id in activity.get("subgroup_ids", []):
                subgroup_activities[subgroup_id].append(activity)
        
        print(f"\n📋 Subgroup Analysis:")
        print(f"   Number of subgroups: {len(subgroup_activities)}")
        
        total_duration_all = 0
        max_subgroup_duration = 0
        
        for subgroup_id, subgroup_acts in subgroup_activities.items():
            total_duration = sum(act.get("duration", 1) for act in subgroup_acts)
            total_duration_all += total_duration
            max_subgroup_duration = max(max_subgroup_duration, total_duration)
            
            print(f"\n   Subgroup {subgroup_id}:")
            print(f"     Activities: {len(subgroup_acts)}")
            print(f"     Total duration: {total_duration}")
            print(f"     Sample activities: {[act['code'] for act in subgroup_acts[:3]]}")
            
            # Check feasibility for this subgroup
            available_slots = len(days) * len(non_interval_periods)
            if total_duration > available_slots:
                print(f"     ❌ INFEASIBLE: Needs {total_duration} slots, only {available_slots} available")
            else:
                utilization = (total_duration / available_slots) * 100
                print(f"     ✅ FEASIBLE: {utilization:.1f}% time utilization")
        
        print(f"\n📊 Overall Analysis:")
        print(f"   Total duration across all subgroups: {total_duration_all}")
        print(f"   Maximum subgroup duration: {max_subgroup_duration}")
        print(f"   Available time slots per subgroup: {len(days) * len(non_interval_periods)}")
        
        if max_subgroup_duration <= len(days) * len(non_interval_periods):
            print("   ✅ ALL SUBGROUPS FEASIBLE: Each subgroup can fit in available time slots")
        else:
            print("   ❌ SOME SUBGROUPS INFEASIBLE: At least one subgroup has too many activities")
        
        return subgroup_activities
        
    except Exception as e:
        print(f"❌ Error in subgroup analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_algorithm_period_conflicts():
    """Analyze why the algorithm is reporting period conflicts"""
    print("\n🔍 ALGORITHM PERIOD CONFLICT ANALYSIS")
    print("=" * 50)
    
    print("Looking at the current algorithm logic...")
    print("""
Current period conflict calculation:
```python
# Period conflicts: check for overlapping multi-period activities
all_period_assignments = {}
for schedule in individual:
    for per in schedule["period"]:
        key = (schedule["day"]["_id"], per["_id"])
        if key not in all_period_assignments:
            all_period_assignments[key] = []
        all_period_assignments[key].append(schedule["activity_id"])

for key, activities in all_period_assignments.items():
    if len(activities) > 1:
        period_conflicts += len(activities) - 1
```

🚨 PROBLEM IDENTIFIED:
This counts ANY two activities in the same time period as a conflict,
regardless of whether they're for different subgroups!

✅ CORRECT LOGIC SHOULD BE:
Only count conflicts when activities for the SAME subgroup overlap.
Different subgroups SHOULD be able to have activities simultaneously.
""")

def main():
    """Main analysis function"""
    print("🧪 SUBGROUP SCHEDULING ANALYSIS")
    print("=" * 60)
    
    # Analyze activities by subgroup
    subgroup_data = analyze_activities_by_subgroup()
    
    # Analyze algorithm logic
    analyze_algorithm_period_conflicts()
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)
    
    print(f"\n📋 CONCLUSION:")
    print(f"   The 79 period conflicts are likely due to incorrect conflict calculation.")
    print(f"   The algorithm is treating activities for different subgroups as conflicts.")
    print(f"   This needs to be fixed to only count same-subgroup conflicts.")

if __name__ == "__main__":
    main() 