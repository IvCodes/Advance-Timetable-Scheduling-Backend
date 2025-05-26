"""
Enhanced STA83 Algorithm Runner with Evaluation and Database Storage
Runs algorithms, evaluates results, and stores them in MongoDB for comparison
"""
import numpy as np
import time
import sys
import os
import asyncio
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, List
import logging

# Add paths for imports
sys.path.append('.')
sys.path.append('./core')
sys.path.append('./algorithms')
sys.path.append('./constraint_programming')
sys.path.append('./rl')
sys.path.append('./analysis')

from .algorithm_runner import AlgorithmRunner
from .analysis.exam_evaluation_metrics import ExamEvaluationMetrics
from .analysis.database_service import exam_db_service
from .analysis.models import AlgorithmRunResult, ExamMetrics

logger = logging.getLogger(__name__)

class EnhancedAlgorithmRunner(AlgorithmRunner):
    """Enhanced algorithm runner with evaluation and database storage"""
    
    def __init__(self):
        super().__init__()
        self.evaluator = None
        self.db_connected = False
    
    async def initialize(self):
        """Initialize database connection and evaluator"""
        try:
            await exam_db_service.connect()
            self.db_connected = True
            logger.info("Enhanced Algorithm Runner initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Algorithm Runner: {e}")
            self.db_connected = False
    
    def _setup_evaluator(self):
        """Setup the evaluation metrics calculator"""
        try:
            from .core.sta83_data_loader import STA83DataLoader
            
            # Base directory for the exams module
            BASE_EXAMS_DIR = os.path.dirname(os.path.abspath(__file__))
            crs_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.crs')
            stu_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.stu')
            
            data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)
            if data_loader.load_data():
                self.evaluator = ExamEvaluationMetrics(data_loader)
                return True
            else:
                logger.error("Failed to load data for evaluator")
                return False
        except Exception as e:
            logger.error(f"Failed to setup evaluator: {e}")
            return False
    
    async def run_algorithm_with_evaluation(self, algorithm: str, mode: str = 'standard') -> Dict[str, Any]:
        """Run an algorithm and store the evaluation results in the database"""
        
        # Ensure evaluator is setup
        if self.evaluator is None:
            if not self._setup_evaluator():
                return {
                    "success": False,
                    "error": "Failed to setup evaluator",
                    "algorithm": algorithm,
                    "mode": mode
                }
        
        # Run the algorithm
        start_time = time.time()
        success, message, schedule_data, runtime = self.run_single_algorithm(algorithm, mode)
        execution_time = time.time() - start_time
        
        result_data = {
            "algorithm": algorithm,
            "mode": mode,
            "success": success,
            "message": message,
            "execution_time": execution_time,
            "runtime": runtime,
            "schedule_data": schedule_data
        }
        
        if not success or schedule_data is None:
            # Store failed run
            if self.db_connected:
                try:
                    failed_result = AlgorithmRunResult(
                        algorithm_name=algorithm,
                        execution_time_seconds=execution_time,
                        algorithm_parameters=self.run_modes[mode].get(algorithm, {}),
                        solution=[],
                        objective_values={},
                        metrics=ExamMetrics(
                            proximity_penalty=float('inf'),
                            conflict_violations=999999,
                            room_capacity_violations=999999,
                            slot_utilization=0.0,
                            student_load_variance=float('inf'),
                            max_exams_per_day=999,
                            avg_exams_per_day=999.0,
                            total_students_affected=999999,
                            fairness_score=0.0,
                            efficiency_score=0.0
                        ),
                        dataset_info={
                            "num_exams": self.evaluator.num_exams if self.evaluator else 0,
                            "num_students": self.evaluator.num_students if self.evaluator else 0,
                            "dataset": "STA-F-83"
                        },
                        success=False,
                        error_message=message
                    )
                    
                    run_id = await exam_db_service.store_algorithm_run(failed_result)
                    result_data["run_id"] = run_id
                    logger.info(f"Stored failed run for {algorithm} with ID: {run_id}")
                except Exception as e:
                    logger.error(f"Failed to store failed run: {e}")
            
            return result_data
        
        # Extract solution for evaluation
        solution = self._extract_solution_from_schedule(schedule_data, algorithm)
        
        if solution is None:
            result_data["error"] = "Could not extract solution for evaluation"
            return result_data
        
        # Evaluate the solution
        try:
            evaluation_result = self.evaluator.evaluate_solution(solution)
            
            # Create detailed metrics
            metrics = ExamMetrics(
                proximity_penalty=evaluation_result["proximity_penalty"],
                conflict_violations=evaluation_result["conflict_violations"],
                room_capacity_violations=evaluation_result.get("room_capacity_violations", 0),
                slot_utilization=evaluation_result["slot_utilization"],
                student_load_variance=evaluation_result["student_load_variance"],
                max_exams_per_day=evaluation_result["max_exams_per_day"],
                avg_exams_per_day=evaluation_result["avg_exams_per_day"],
                total_students_affected=evaluation_result["total_students_affected"],
                fairness_score=evaluation_result["fairness_score"],
                efficiency_score=evaluation_result["efficiency_score"]
            )
            
            # Store in database if connected
            if self.db_connected:
                algorithm_result = AlgorithmRunResult(
                    algorithm_name=algorithm,
                    execution_time_seconds=execution_time,
                    algorithm_parameters=self.run_modes[mode].get(algorithm, {}),
                    solution=solution,
                    objective_values=evaluation_result.get("objective_values", {}),
                    metrics=metrics,
                    dataset_info={
                        "num_exams": self.evaluator.num_exams,
                        "num_students": self.evaluator.num_students,
                        "dataset": "STA-F-83"
                    },
                    success=True
                )
                
                run_id = await exam_db_service.store_algorithm_run(algorithm_result)
                result_data["run_id"] = run_id
                logger.info(f"Stored successful run for {algorithm} with ID: {run_id}")
            
            # Add evaluation results to return data
            result_data["evaluation"] = evaluation_result
            result_data["metrics"] = metrics.dict()
            
        except Exception as e:
            logger.error(f"Failed to evaluate solution: {e}")
            result_data["error"] = f"Evaluation failed: {str(e)}"
        
        return result_data
    
    def _extract_solution_from_schedule(self, schedule_data: Dict, algorithm: str) -> Optional[List[int]]:
        """Extract solution permutation from schedule data based on algorithm type"""
        try:
            if algorithm in ['nsga2', 'moead', 'hybrid', 'hybrid_sarsa']:
                # For genetic algorithms, the solution might be in different formats
                if 'exam_assignments' in schedule_data:
                    # Convert exam assignments to permutation
                    assignments = schedule_data['exam_assignments']
                    if isinstance(assignments, dict):
                        # Sort by exam ID and extract timeslots
                        sorted_exams = sorted(assignments.items())
                        return [assignments[exam_id] for exam_id, _ in sorted_exams]
                    elif isinstance(assignments, list):
                        return assignments
                
                # Try to find permutation in other fields
                for key in ['permutation', 'solution', 'best_solution']:
                    if key in schedule_data and schedule_data[key] is not None:
                        return list(schedule_data[key])
            
            elif algorithm == 'cp':
                # For CP, extract from exam_assignments
                if 'exam_assignments' in schedule_data:
                    assignments = schedule_data['exam_assignments']
                    if isinstance(assignments, dict):
                        # Convert to permutation (exam_id -> timeslot)
                        num_exams = len(assignments)
                        permutation = [0] * num_exams
                        for exam_id, timeslot in assignments.items():
                            if isinstance(exam_id, str) and exam_id.startswith('exam_'):
                                exam_idx = int(exam_id.split('_')[1]) - 1  # Convert to 0-indexed
                            else:
                                exam_idx = int(exam_id) - 1  # Assume 1-indexed
                            if 0 <= exam_idx < num_exams:
                                permutation[exam_idx] = timeslot
                        return permutation
            
            elif algorithm in ['dqn', 'sarsa']:
                # For RL algorithms, check for action sequence or final state
                if 'final_schedule' in schedule_data:
                    return schedule_data['final_schedule']
                elif 'action_sequence' in schedule_data:
                    return schedule_data['action_sequence']
            
            # Fallback: try to find any list-like structure
            for key, value in schedule_data.items():
                if isinstance(value, (list, np.ndarray)) and len(value) > 0:
                    return list(value)
            
            logger.warning(f"Could not extract solution from schedule_data for {algorithm}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting solution for {algorithm}: {e}")
            return None
    
    async def run_all_algorithms_with_evaluation(self, mode: str = 'standard') -> Dict[str, Any]:
        """Run all algorithms with evaluation and store results"""
        algorithms = ['nsga2', 'moead', 'cp', 'dqn', 'sarsa', 'hybrid', 'hybrid_sarsa']
        results = {}
        run_ids = []
        
        print(f"\\n=== Running All Algorithms ({mode} mode) with Evaluation ===")
        
        for algorithm in algorithms:
            print(f"\\n--- Running {algorithm.upper()} ---")
            try:
                result = await self.run_algorithm_with_evaluation(algorithm, mode)
                results[algorithm] = result
                
                if result.get("run_id"):
                    run_ids.append(result["run_id"])
                
                # Print summary
                if result["success"]:
                    if "evaluation" in result:
                        eval_data = result["evaluation"]
                        print(f"✓ {algorithm.upper()}: Proximity Penalty: {eval_data['proximity_penalty']:.2f}, "
                              f"Efficiency: {eval_data['efficiency_score']:.2f}, "
                              f"Time: {result['execution_time']:.1f}s")
                    else:
                        print(f"✓ {algorithm.upper()}: {result['message']}")
                else:
                    print(f"✗ {algorithm.upper()}: {result['message']}")
                    
            except Exception as e:
                logger.error(f"Error running {algorithm}: {e}")
                results[algorithm] = {
                    "success": False,
                    "error": str(e),
                    "algorithm": algorithm,
                    "mode": mode
                }
        
        # Generate comparison if we have successful runs
        comparison_data = None
        if len(run_ids) > 1 and self.db_connected:
            try:
                comparison_data = await exam_db_service.get_algorithm_comparison(run_ids)
                print(f"\\n=== Algorithm Comparison Generated ===")
                print(f"Best Algorithm: {comparison_data['best_algorithm']}")
                print(f"Worst Algorithm: {comparison_data['worst_algorithm']}")
                print(f"Performance Gap: {comparison_data['performance_gap']:.2f}")
            except Exception as e:
                logger.error(f"Failed to generate comparison: {e}")
        
        return {
            "mode": mode,
            "results": results,
            "run_ids": run_ids,
            "comparison": comparison_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_algorithm_statistics(self) -> Dict[str, Any]:
        """Get algorithm performance statistics from database"""
        if not self.db_connected:
            return {"error": "Database not connected"}
        
        try:
            return await exam_db_service.get_algorithm_statistics()
        except Exception as e:
            logger.error(f"Failed to get algorithm statistics: {e}")
            return {"error": str(e)}
    
    async def get_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent algorithm runs from database"""
        if not self.db_connected:
            return []
        
        try:
            return await exam_db_service.get_algorithm_runs(limit=limit)
        except Exception as e:
            logger.error(f"Failed to get recent runs: {e}")
            return []

# Global instance
enhanced_runner = EnhancedAlgorithmRunner()

async def main():
    """Test the enhanced algorithm runner"""
    await enhanced_runner.initialize()
    
    # Run a single algorithm
    print("Testing single algorithm run...")
    result = await enhanced_runner.run_algorithm_with_evaluation('nsga2', 'quick')
    print(f"Result: {result}")
    
    # Get statistics
    print("\\nGetting statistics...")
    stats = await enhanced_runner.get_algorithm_statistics()
    print(f"Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main()) 