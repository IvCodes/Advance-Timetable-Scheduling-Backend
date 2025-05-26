#!/usr/bin/env python3
"""
Detailed GA Analysis Script
===========================

This script analyzes the GA algorithm results in detail to understand
the period conflicts and verify the algorithm is working correctly.
"""

import sys
import os
from collections import defaultdict

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def analyze_ga_solution():
    """Run GA and analyze the solution in detail"""
    print("🧬 DETAILED GA SOLUTION ANALYSIS")
    print("=" * 50)
    
    try:
        from app.generator.algorithms.ga.ga import generate_ga
        
        print("🚀 Running GA algorithm...")
        result = generate_ga()
        
        if isinstance(result, tuple) and len(result) == 4:
            pop, log, hof, formatted_solution = result
            
            if hof and len(hof) > 0:
                best_individual = hof[0]
                best_fitness = best_individual.fitness.values
                
                print(f"\n🎯 Best Solution Analysis:")
                print(f"   Teacher conflicts: {best_fitness[0]}")
                print(f"   Room conflicts: {best_fitness[1]}")
                print(f"   Interval conflicts: {best_fitness[2]}")
                print(f"   Period conflicts: {best_fitness[3]}")
                
                # Analyze the actual solution
                print(f"\n📋 Solution Details:")
                print(f"   Total activities scheduled: {len(best_individual)}")
                
                # Group by subgroup to analyze conflicts
                subgroup_schedules = defaultdict(list)
                for activity in best_individual:
                    subgroup = activity["subgroup"]
                    subgroup_schedules[subgroup].append(activity)
                
                print(f"   Subgroups in solution: {len(subgroup_schedules)}")
                
                # Check for actual period conflicts within each subgroup
                total_real_conflicts = 0
                for subgroup, activities in subgroup_schedules.items():
                    subgroup_conflicts = 0
                    period_usage = defaultdict(list)
                    
                    for activity in activities:
                        day_id = activity["day"]["_id"]
                        for period in activity["period"]:
                            key = (day_id, period["_id"])
                            period_usage[key].append(activity["activity_id"])
                    
                    for key, activity_ids in period_usage.items():
                        if len(activity_ids) > 1:
                            conflicts = len(activity_ids) - 1
                            subgroup_conflicts += conflicts
                            print(f"     Subgroup {subgroup}: {conflicts} conflicts in period {key}")
                    
                    total_real_conflicts += subgroup_conflicts
                    if subgroup_conflicts > 0:
                        print(f"   Subgroup {subgroup}: {subgroup_conflicts} period conflicts")
                
                print(f"\n📊 Conflict Verification:")
                print(f"   Calculated period conflicts: {total_real_conflicts}")
                print(f"   Reported period conflicts: {best_fitness[3]}")
                
                if total_real_conflicts == best_fitness[3]:
                    print("   ✅ VERIFIED: Conflict calculation is correct!")
                else:
                    print("   ⚠️  DISCREPANCY: Conflict calculation may have issues")
                
                # Check interval violations
                interval_violations = 0
                for activity in best_individual:
                    for period in activity["period"]:
                        if period.get("is_interval", False):
                            interval_violations += 1
                            print(f"     ❌ Interval violation: {activity['activity_id']} in {period['name']}")
                
                if interval_violations == 0:
                    print("   ✅ VERIFIED: No interval violations!")
                else:
                    print(f"   ❌ PROBLEM: {interval_violations} interval violations found")
                
                return best_individual
        
        return None
        
    except Exception as e:
        print(f"❌ Error in GA analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main analysis function"""
    print("🧪 DETAILED GA ALGORITHM ANALYSIS")
    print("=" * 60)
    
    solution = analyze_ga_solution()
    
    print("\n" + "=" * 60)
    print("✅ GA ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main() 