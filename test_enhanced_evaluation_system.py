#!/usr/bin/env python3
"""
Test script for the Enhanced Exam Algorithm Evaluation System
Tests the complete flow: run algorithm -> evaluate -> store in MongoDB -> retrieve results
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the app directory to the path
sys.path.append('app')
sys.path.append('app/exams')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_evaluation_system():
    """Test the complete enhanced evaluation system"""
    
    print("🚀 Testing Enhanced Exam Algorithm Evaluation System")
    print("=" * 60)
    
    try:
        # Import the enhanced runner
        from app.exams.enhanced_algorithm_runner import enhanced_runner
        from app.exams.analysis.database_service import exam_db_service
        
        # Step 1: Initialize the system
        print("\\n📡 Step 1: Initializing system...")
        await enhanced_runner.initialize()
        
        if not enhanced_runner.db_connected:
            print("❌ Database connection failed!")
            return False
        
        print("✅ System initialized successfully!")
        
        # Step 2: Test single algorithm run with evaluation
        print("\\n🧪 Step 2: Testing single algorithm run (NSGA2 - Quick mode)...")
        result = await enhanced_runner.run_algorithm_with_evaluation('nsga2', 'quick')
        
        print(f"Algorithm: {result['algorithm']}")
        print(f"Success: {result['success']}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        
        if result['success'] and 'evaluation' in result:
            eval_data = result['evaluation']
            print(f"Proximity Penalty: {eval_data['proximity_penalty']:.2f}")
            print(f"Efficiency Score: {eval_data['efficiency_score']:.2f}")
            print(f"Slot Utilization: {eval_data['slot_utilization']:.2f}%")
            print(f"Run ID: {result.get('run_id', 'N/A')}")
        else:
            print(f"❌ Run failed: {result.get('message', 'Unknown error')}")
        
        # Step 3: Test database storage verification
        print("\\n💾 Step 3: Verifying database storage...")
        recent_runs = await enhanced_runner.get_recent_runs(limit=5)
        print(f"Found {len(recent_runs)} recent runs in database")
        
        for i, run in enumerate(recent_runs[:3]):  # Show first 3
            print(f"  {i+1}. {run['algorithm_name']} - {run['run_timestamp']} - "
                  f"Penalty: {run['metrics']['proximity_penalty']:.2f}")
        
        # Step 4: Test algorithm statistics
        print("\\n📊 Step 4: Getting algorithm statistics...")
        stats = await enhanced_runner.get_algorithm_statistics()
        
        if 'error' not in stats:
            print(f"Total runs in database: {stats['total_runs']}")
            print("Algorithm performance summary:")
            for algo_stat in stats['algorithm_stats'][:5]:  # Show first 5
                print(f"  {algo_stat['_id']}: {algo_stat['total_runs']} runs, "
                      f"Avg penalty: {algo_stat['avg_proximity_penalty']:.2f}")
        else:
            print(f"❌ Failed to get statistics: {stats['error']}")
        
        # Step 5: Test running multiple algorithms (optional - takes longer)
        run_multiple = input("\\n🔄 Run multiple algorithms for comparison? (y/N): ").lower().strip()
        
        if run_multiple == 'y':
            print("\\n🏃 Step 5: Running multiple algorithms...")
            # Run a few quick algorithms
            algorithms_to_test = ['nsga2', 'moead', 'cp']
            run_ids = []
            
            for algo in algorithms_to_test:
                print(f"  Running {algo.upper()}...")
                result = await enhanced_runner.run_algorithm_with_evaluation(algo, 'quick')
                if result['success'] and result.get('run_id'):
                    run_ids.append(result['run_id'])
                    print(f"    ✅ {algo.upper()} completed")
                else:
                    print(f"    ❌ {algo.upper()} failed: {result.get('message', 'Unknown')}")
            
            # Generate comparison
            if len(run_ids) > 1:
                print("\\n📈 Generating algorithm comparison...")
                comparison = await exam_db_service.get_algorithm_comparison(run_ids)
                print(f"Best Algorithm: {comparison['best_algorithm']}")
                print(f"Worst Algorithm: {comparison['worst_algorithm']}")
                print(f"Performance Gap: {comparison['performance_gap']:.2f}")
                
                print("\\nOverall Ranking:")
                for rank_data in comparison['overall_ranking']:
                    print(f"  {rank_data['rank']}. {rank_data['algorithm_name']} "
                          f"(Score: {rank_data['overall_score']:.2f})")
        
        print("\\n🎉 Enhanced Evaluation System Test Completed Successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're running this from the correct directory and all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_connection():
    """Test basic database connection"""
    print("🔌 Testing MongoDB connection...")
    
    try:
        from app.exams.analysis.database_service import exam_db_service
        await exam_db_service.connect()
        print("✅ MongoDB connection successful!")
        
        # Test basic operations
        from app.exams.analysis.models import AlgorithmRunResult, ExamMetrics
        
        # Create a test record
        test_metrics = ExamMetrics(
            proximity_penalty=100.0,
            conflict_violations=0,
            room_capacity_violations=0,
            slot_utilization=85.5,
            student_load_variance=2.3,
            max_exams_per_day=3,
            avg_exams_per_day=2.1,
            total_students_affected=50,
            fairness_score=0.8,
            efficiency_score=0.75
        )
        
        test_result = AlgorithmRunResult(
            algorithm_name="test_algorithm",
            execution_time_seconds=10.5,
            algorithm_parameters={"test_param": "test_value"},
            solution=[1, 2, 3, 4, 5],
            objective_values={"obj1": 100.0, "obj2": 200.0},
            metrics=test_metrics,
            dataset_info={"dataset": "test", "num_exams": 5, "num_students": 100},
            success=True
        )
        
        # Store test record
        run_id = await exam_db_service.store_algorithm_run(test_result)
        print(f"✅ Test record stored with ID: {run_id}")
        
        # Retrieve test record
        recent_runs = await exam_db_service.get_algorithm_runs(limit=1)
        if recent_runs:
            print(f"✅ Test record retrieved: {recent_runs[0]['algorithm_name']}")
        
        await exam_db_service.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 Enhanced Exam Algorithm Evaluation System - Test Suite")
    print("=" * 70)
    
    # Test 1: Database connection
    print("\\n" + "="*50)
    print("TEST 1: Database Connection")
    print("="*50)
    db_success = await test_database_connection()
    
    if not db_success:
        print("❌ Database test failed. Please check your MongoDB connection.")
        return
    
    # Test 2: Full system test
    print("\\n" + "="*50)
    print("TEST 2: Full Enhanced Evaluation System")
    print("="*50)
    system_success = await test_enhanced_evaluation_system()
    
    if system_success:
        print("\\n🎉 All tests passed! The Enhanced Evaluation System is working correctly.")
    else:
        print("\\n❌ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 