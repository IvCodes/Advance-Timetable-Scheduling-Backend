#!/usr/bin/env python3
"""
Data Analysis Script for Timetable Scheduling System
===================================================

This script analyzes the current data structure and algorithm flow
to understand what data is being loaded and how algorithms process it.

Usage: python -m app.scripts.data_analysis
"""

import json
import sys
import os
from typing import Dict, List, Any
from collections import defaultdict

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.generator.data_collector import *
    from app.algorithms_2.Data_Loading import load_data
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

class DataAnalyzer:
    def __init__(self):
        self.mongodb_data = {}
        self.algorithms2_data = {}
        self.analysis_results = {}
        
    def analyze_mongodb_data(self):
        """Analyze data from MongoDB via data_collector.py"""
        print("=" * 60)
        print("ANALYZING MONGODB DATA")
        print("=" * 60)
        
        try:
            # Load all MongoDB collections
            self.mongodb_data = {
                'days': get_days(),
                'facilities': get_spaces(),
                'modules': get_modules(),
                'periods': get_periods(),
                'students': get_students(),
                'teachers': get_teachers(),
                'years': get_years(),
                'activities': get_activities(),
                'timetables': get_timetables()
            }
            
            # Analyze each collection
            for collection_name, data in self.mongodb_data.items():
                print(f"\n📊 {collection_name.upper()}:")
                print(f"   Count: {len(data)}")
                
                if data:
                    # Show structure of first item
                    first_item = data[0]
                    print(f"   Structure: {list(first_item.keys()) if isinstance(first_item, dict) else type(first_item)}")
                    
                    # Show sample data (first item)
                    print(f"   Sample: {self._truncate_dict(first_item)}")
                    
                    # Analyze specific collections
                    if collection_name == 'facilities':
                        self._analyze_facilities(data)
                    elif collection_name == 'activities':
                        self._analyze_activities(data)
                    elif collection_name == 'periods':
                        self._analyze_periods(data)
                else:
                    print("   ⚠️  No data found!")
                    
        except Exception as e:
            print(f"❌ Error analyzing MongoDB data: {e}")
            
    def analyze_algorithms2_data(self):
        """Analyze data from algorithms_2 directory"""
        print("\n" + "=" * 60)
        print("ANALYZING ALGORITHMS_2 DATA")
        print("=" * 60)
        
        try:
            # Load sliit_computing_dataset.json
            dataset_path = "app/algorithms_2/sliit_computing_dataset.json"
            if os.path.exists(dataset_path):
                with open(dataset_path, 'r') as f:
                    self.algorithms2_data = json.load(f)
                    
                print(f"\n📊 SLIIT COMPUTING DATASET:")
                print(f"   Structure: {list(self.algorithms2_data.keys())}")
                
                for key, value in self.algorithms2_data.items():
                    print(f"\n   {key.upper()}:")
                    print(f"     Count: {len(value) if isinstance(value, list) else 'N/A'}")
                    
                    if isinstance(value, list) and value:
                        print(f"     Sample: {self._truncate_dict(value[0])}")
                        
                        # Special analysis for rooms
                        if key == 'rooms':
                            self._analyze_rooms_algorithms2(value)
                            
            else:
                print(f"❌ Dataset file not found: {dataset_path}")
                
        except Exception as e:
            print(f"❌ Error analyzing algorithms_2 data: {e}")
            
    def compare_datasets(self):
        """Compare MongoDB and algorithms_2 datasets"""
        print("\n" + "=" * 60)
        print("DATASET COMPARISON")
        print("=" * 60)
        
        # Compare room data
        print("\n🏢 ROOM COMPARISON:")
        mongodb_rooms = self.mongodb_data.get('facilities', [])
        algorithms2_rooms = self.algorithms2_data.get('rooms', [])
        
        print(f"   MongoDB rooms: {len(mongodb_rooms)}")
        print(f"   Algorithms2 rooms: {len(algorithms2_rooms)}")
        
        if mongodb_rooms:
            print(f"   MongoDB room sample: {self._truncate_dict(mongodb_rooms[0])}")
        if algorithms2_rooms:
            print(f"   Algorithms2 room sample: {self._truncate_dict(algorithms2_rooms[0])}")
            
        # Compare activities/events
        print("\n📅 ACTIVITIES/EVENTS COMPARISON:")
        mongodb_activities = self.mongodb_data.get('activities', [])
        algorithms2_events = self.algorithms2_data.get('events', [])
        
        print(f"   MongoDB activities: {len(mongodb_activities)}")
        print(f"   Algorithms2 events: {len(algorithms2_events)}")
        
        if mongodb_activities:
            print(f"   MongoDB activity sample: {self._truncate_dict(mongodb_activities[0])}")
        if algorithms2_events:
            print(f"   Algorithms2 event sample: {self._truncate_dict(algorithms2_events[0])}")
            
    def analyze_algorithm_structure(self):
        """Analyze how algorithms are structured"""
        print("\n" + "=" * 60)
        print("ALGORITHM STRUCTURE ANALYSIS")
        print("=" * 60)
        
        # Analyze generator algorithms
        print("\n🧬 GENERATOR ALGORITHMS:")
        generator_algos = ['GA', 'CO', 'RL']
        
        for algo in generator_algos:
            print(f"\n   {algo} Algorithm:")
            self._analyze_generator_algorithm(algo)
            
        # Analyze algorithms_2
        print("\n🔬 ALGORITHMS_2:")
        algorithms2_files = [
            'Nsga_II.py', 'moead.py', 'spea2.py',
            'DQN.py', 'SARSA.py', 'ImplicitQlearning.py'
        ]
        
        for algo_file in algorithms2_files:
            if os.path.exists(f"app/algorithms_2/{algo_file}"):
                print(f"   ✅ {algo_file} exists")
            elif os.path.exists(f"app/algorithms_2/RL/{algo_file}"):
                print(f"   ✅ {algo_file} exists (in RL folder)")
            else:
                print(f"   ❌ {algo_file} not found")
                
    def identify_issues(self):
        """Identify potential issues in the current setup"""
        print("\n" + "=" * 60)
        print("IDENTIFIED ISSUES")
        print("=" * 60)
        
        issues = []
        
        # Check room data issues
        algorithms2_rooms = self.algorithms2_data.get('rooms', [])
        if algorithms2_rooms:
            room_codes = [room.get('code', '') for room in algorithms2_rooms]
            duplicates = [code for code in set(room_codes) if room_codes.count(code) > 1]
            if duplicates:
                issues.append(f"🔴 Duplicate room codes in algorithms_2: {duplicates}")
                
        # Check data availability
        mongodb_facilities = self.mongodb_data.get('facilities', [])
        if len(mongodb_facilities) == 0:
            issues.append("🔴 No facilities data in MongoDB")
            
        if len(algorithms2_rooms) < 5:
            issues.append(f"🔴 Very few rooms in algorithms_2 dataset: {len(algorithms2_rooms)}")
            
        # Check activities
        mongodb_activities = self.mongodb_data.get('activities', [])
        if len(mongodb_activities) == 0:
            issues.append("🔴 No activities data in MongoDB")
            
        # Print issues
        if issues:
            for issue in issues:
                print(f"   {issue}")
        else:
            print("   ✅ No major issues identified")
            
    def generate_recommendations(self):
        """Generate recommendations for improvement"""
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        
        recommendations = []
        
        # Room data recommendations
        mongodb_rooms = len(self.mongodb_data.get('facilities', []))
        algorithms2_rooms = len(self.algorithms2_data.get('rooms', []))
        
        if algorithms2_rooms < 10:
            recommendations.append("📈 Increase room diversity in algorithms_2 dataset")
            
        if mongodb_rooms > algorithms2_rooms:
            recommendations.append("🔄 Sync algorithms_2 rooms with MongoDB facilities")
            
        # Data structure recommendations
        recommendations.append("🔧 Standardize data structure between MongoDB and algorithms_2")
        recommendations.append("✅ Add data validation before algorithm execution")
        recommendations.append("📊 Implement data quality checks")
        
        for rec in recommendations:
            print(f"   {rec}")
            
    def save_analysis_report(self):
        """Save analysis results to a file"""
        report = {
            'mongodb_data_summary': {
                key: {
                    'count': len(value),
                    'sample': self._truncate_dict(value[0]) if value else None
                }
                for key, value in self.mongodb_data.items()
            },
            'algorithms2_data_summary': {
                key: {
                    'count': len(value) if isinstance(value, list) else 'N/A',
                    'sample': self._truncate_dict(value[0]) if isinstance(value, list) and value else None
                }
                for key, value in self.algorithms2_data.items()
            }
        }
        
        with open('data_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"\n💾 Analysis report saved to: data_analysis_report.json")
        
    def _analyze_facilities(self, facilities):
        """Analyze facilities data"""
        if not facilities:
            return
            
        capacities = [f.get('capacity', 0) for f in facilities if 'capacity' in f]
        types = [f.get('type', 'unknown') for f in facilities if 'type' in f]
        
        if capacities:
            print(f"   Capacity range: {min(capacities)} - {max(capacities)}")
        if types:
            type_counts = defaultdict(int)
            for t in types:
                type_counts[t] += 1
            print(f"   Types: {dict(type_counts)}")
            
    def _analyze_activities(self, activities):
        """Analyze activities data"""
        if not activities:
            return
            
        durations = [a.get('duration', 1) for a in activities if 'duration' in a]
        subjects = [a.get('subject', 'unknown') for a in activities if 'subject' in a]
        
        if durations:
            print(f"   Duration range: {min(durations)} - {max(durations)}")
        if subjects:
            unique_subjects = len(set(subjects))
            print(f"   Unique subjects: {unique_subjects}")
            
    def _analyze_periods(self, periods):
        """Analyze periods data"""
        if not periods:
            return
            
        intervals = [p for p in periods if p.get('is_interval', False)]
        regular_periods = [p for p in periods if not p.get('is_interval', False)]
        
        print(f"   Regular periods: {len(regular_periods)}")
        print(f"   Intervals: {len(intervals)}")
        
    def _analyze_rooms_algorithms2(self, rooms):
        """Analyze rooms in algorithms_2 dataset"""
        if not rooms:
            return
            
        capacities = [r.get('capacity', 0) for r in rooms]
        types = [r.get('type', 'unknown') for r in rooms]
        codes = [r.get('code', 'unknown') for r in rooms]
        
        print(f"     Capacity range: {min(capacities)} - {max(capacities)}")
        print(f"     Types: {set(types)}")
        print(f"     Codes: {codes}")
        
        # Check for duplicates
        duplicates = [code for code in set(codes) if codes.count(code) > 1]
        if duplicates:
            print(f"     ⚠️  Duplicate codes: {duplicates}")
            
    def _analyze_generator_algorithm(self, algo_name):
        """Analyze generator algorithm structure"""
        algo_path = f"app/generator/algorithms/{algo_name.lower()}/{algo_name.lower()}.py"
        if os.path.exists(algo_path):
            print(f"     ✅ {algo_name} implementation exists")
            # Could add more detailed analysis here
        else:
            print(f"     ❌ {algo_name} implementation not found")
            
    def _truncate_dict(self, obj, max_length=100):
        """Truncate dictionary representation for display"""
        if obj is None:
            return None
        str_repr = str(obj)
        if len(str_repr) > max_length:
            return str_repr[:max_length] + "..."
        return str_repr
        
    def run_full_analysis(self):
        """Run complete analysis"""
        print("🔍 TIMETABLE SCHEDULING SYSTEM DATA ANALYSIS")
        print("=" * 60)
        
        self.analyze_mongodb_data()
        self.analyze_algorithms2_data()
        self.compare_datasets()
        self.analyze_algorithm_structure()
        self.identify_issues()
        self.generate_recommendations()
        self.save_analysis_report()
        
        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.run_full_analysis() 