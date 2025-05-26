#!/usr/bin/env python3
"""
Fixed Algorithm Testing Script
=============================

This script tests all algorithms after the fixes to verify they work correctly
and no longer have the interval and period conflict issues.
"""

import sys
import os
import traceback

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def test_fixed_ga_algorithm():
    """Test the fixed GA algorithm"""
    print("🧬 TESTING FIXED GA ALGORITHM")
    print("=" * 50)
    
    try:
        from app.generator.algorithms.ga.ga import generate_ga
        print("✅ Successfully imported fixed GA algorithm")
        
        print("🚀 Running fixed GA algorithm...")
        result = generate_ga()
        
        print(f"✅ Fixed GA completed successfully!")
        print(f"📊 Result type: {type(result)}")
        
        # Check if it's the new format (pop, log, hof, formatted_solution)
        if isinstance(result, tuple) and len(result) == 4:
            pop, log, hof, formatted_solution = result
            print(f"📋 Population size: {len(pop)}")
            print(f"📈 Generations logged: {len(log)}")
            print(f"🏆 Hall of fame size: {len(hof)}")
            print(f"📅 Formatted solution activities: {len(formatted_solution)}")
            
            if hof and len(hof) > 0:
                best_fitness = hof[0].fitness.values
                print(f"🎯 Best fitness: {best_fitness}")
                print(f"   Teacher conflicts: {best_fitness[0]}")
                print(f"   Room conflicts: {best_fitness[1]}")
                print(f"   Interval conflicts: {best_fitness[2]} (should be 0!)")
                print(f"   Period conflicts: {best_fitness[3]}")
                
                # Check if interval conflicts are fixed
                if best_fitness[2] == 0:
                    print("🎉 SUCCESS: No interval conflicts! Lunch break is respected.")
                else:
                    print(f"⚠️  WARNING: Still {best_fitness[2]} interval conflicts")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in fixed GA algorithm: {e}")
        traceback.print_exc()
        return None

def test_fixed_co_algorithm():
    """Test the fixed CO algorithm"""
    print("\n🐜 TESTING FIXED CO ALGORITHM")
    print("=" * 50)
    
    try:
        from app.generator.algorithms.co.co import generate_co
        print("✅ Successfully imported fixed CO algorithm")
        
        print("🚀 Running fixed CO algorithm...")
        result = generate_co()
        
        print(f"✅ Fixed CO completed successfully!")
        print(f"📊 Result type: {type(result)}")
        if result is not None and hasattr(result, '__len__'):
            print(f"📋 Result length: {len(result)}")
            
            # Analyze the solution
            if result:
                print(f"📅 Sample activity: {result[0] if result else 'None'}")
                
                # Check for interval violations
                interval_violations = 0
                for activity in result:
                    for period in activity.get("period", []):
                        if period.get("is_interval", False):
                            interval_violations += 1
                
                if interval_violations == 0:
                    print("🎉 SUCCESS: No interval violations in CO solution!")
                else:
                    print(f"⚠️  WARNING: {interval_violations} interval violations found")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in fixed CO algorithm: {e}")
        traceback.print_exc()
        return None

def test_rl_algorithm():
    """Test the RL algorithm"""
    print("\n🤖 TESTING RL ALGORITHM")
    print("=" * 50)
    
    try:
        from app.generator.rl.rl import generate_rl
        print("✅ Successfully imported RL algorithm")
        
        print("🚀 Running RL algorithm...")
        result = generate_rl()
        
        print(f"✅ RL completed successfully!")
        print(f"📊 Result type: {type(result)}")
        if result is not None and hasattr(result, '__len__'):
            print(f"📋 Result length: {len(result)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in RL algorithm: {e}")
        traceback.print_exc()
        return None

def analyze_scheduling_capacity():
    """Analyze the theoretical scheduling capacity"""
    print("\n📊 SCHEDULING CAPACITY ANALYSIS")
    print("=" * 50)
    
    try:
        from app.generator.data_collector import (
            get_spaces, get_activities, get_days, get_periods
        )
        
        spaces = get_spaces()
        activities = get_activities()
        days = get_days()
        periods = get_periods()
        
        # Filter non-interval periods
        non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
        
        print(f"📈 Resource Analysis:")
        print(f"   Total spaces: {len(spaces)}")
        print(f"   Total activities: {len(activities)}")
        print(f"   Total days: {len(days)}")
        print(f"   Total periods: {len(periods)}")
        print(f"   Non-interval periods: {len(non_interval_periods)}")
        print(f"   Interval periods: {len(periods) - len(non_interval_periods)}")
        
        # Calculate capacity
        total_time_slots = len(days) * len(non_interval_periods)
        total_room_slots = total_time_slots * len(spaces)
        
        # Calculate activity requirements
        total_activity_duration = sum(activity.get("duration", 1) for activity in activities)
        
        print(f"\n📊 Capacity Analysis:")
        print(f"   Available time slots: {total_time_slots}")
        print(f"   Available room-time slots: {total_room_slots}")
        print(f"   Required activity slots: {total_activity_duration}")
        print(f"   Time utilization: {(total_activity_duration / total_time_slots * 100):.1f}%")
        print(f"   Room utilization: {(total_activity_duration / total_room_slots * 100):.1f}%")
        
        if total_activity_duration <= total_time_slots:
            print("✅ FEASIBLE: Enough time slots for all activities")
        else:
            print("❌ INFEASIBLE: Not enough time slots")
            
        if total_activity_duration <= total_room_slots:
            print("✅ FEASIBLE: Enough room capacity for all activities")
        else:
            print("❌ INFEASIBLE: Not enough room capacity")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in capacity analysis: {e}")
        traceback.print_exc()
        return False

def main():
    """Main testing function"""
    print("🧪 FIXED ALGORITHM TESTING")
    print("=" * 60)
    
    # Step 1: Analyze scheduling capacity
    analyze_scheduling_capacity()
    
    # Step 2: Test fixed GA algorithm
    ga_result = test_fixed_ga_algorithm()
    
    # Step 3: Test fixed CO algorithm
    co_result = test_fixed_co_algorithm()
    
    # Step 4: Test RL algorithm
    rl_result = test_rl_algorithm()
    
    print("\n" + "=" * 60)
    print("✅ FIXED ALGORITHM TESTING COMPLETE")
    print("=" * 60)
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print(f"   Fixed GA Algorithm: {'✅ Success' if ga_result is not None else '❌ Failed'}")
    print(f"   Fixed CO Algorithm: {'✅ Success' if co_result is not None else '❌ Failed'}")
    print(f"   RL Algorithm: {'✅ Success' if rl_result is not None else '❌ Failed'}")
    
    # Check if interval conflicts are resolved
    if ga_result and isinstance(ga_result, tuple) and len(ga_result) >= 3:
        hof = ga_result[2]
        if hof and len(hof) > 0:
            best_fitness = hof[0].fitness.values
            if best_fitness[2] == 0:
                print("🎉 INTERVAL CONFLICTS FIXED: GA no longer schedules during lunch break!")
            else:
                print(f"⚠️  INTERVAL CONFLICTS REMAIN: {best_fitness[2]} violations")

if __name__ == "__main__":
    main() 