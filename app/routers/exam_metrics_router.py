"""
Exam Algorithm Evaluation Metrics Router
Provides endpoints for running exam algorithms with evaluation and retrieving performance metrics
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import sys
import os

# Add paths for exam imports
sys.path.append('app/exams')

router = APIRouter(tags=["Exam Algorithm Metrics"])

# Pydantic models for request/response
class ExamAlgorithmRequest(BaseModel):
    algorithm: str
    mode: str = "standard"

class ExamAlgorithmResponse(BaseModel):
    success: bool
    message: str
    run_id: Optional[str] = None
    execution_time: Optional[float] = None
    evaluation: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None

class ExamBatchRequest(BaseModel):
    mode: str = "standard"
    algorithms: Optional[List[str]] = None

# Global variables for lazy loading
_exam_runner = None
_exam_db_service = None

async def get_exam_runner():
    """Lazy load the exam runner to avoid import issues at startup"""
    global _exam_runner
    if _exam_runner is None:
        try:
            from app.exams.enhanced_algorithm_runner import EnhancedAlgorithmRunner
            _exam_runner = EnhancedAlgorithmRunner()
            await _exam_runner.initialize()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize exam runner: {str(e)}")
    return _exam_runner

async def get_exam_db_service():
    """Lazy load the database service"""
    global _exam_db_service
    if _exam_db_service is None:
        try:
            from app.exams.analysis.database_service import ExamEvaluationDatabaseService
            _exam_db_service = ExamEvaluationDatabaseService()
            await _exam_db_service.connect()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize database service: {str(e)}")
    return _exam_db_service

@router.get("/", summary="Exam Metrics API Info")
async def get_api_info():
    """Get information about the Exam Algorithm Evaluation API"""
    return {
        "name": "Exam Algorithm Evaluation API",
        "version": "1.0.0",
        "description": "API for running exam timetabling algorithms with comprehensive evaluation metrics",
        "features": [
            "Algorithm performance evaluation",
            "Proximity penalty calculation",
            "Student load analysis",
            "Conflict detection",
            "Performance comparison",
            "Historical tracking"
        ],
        "available_algorithms": ['nsga2', 'moead', 'cp', 'dqn', 'sarsa', 'hybrid'],
        "available_modes": ['quick', 'standard', 'full']
    }

@router.get("/runs", summary="Get Algorithm Run Results")
async def get_algorithm_runs(
    algorithm_name: Optional[str] = None,
    limit: int = 50,
    sort_by: str = "run_timestamp",
    sort_order: int = -1
):
    """Get algorithm run results with evaluation metrics"""
    try:
        db_service = await get_exam_db_service()
        
        runs = await db_service.get_algorithm_runs(
            algorithm_name=algorithm_name,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "success": True,
            "runs": runs,
            "total": len(runs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving algorithm runs: {str(e)}")

@router.get("/statistics", summary="Get Algorithm Performance Statistics")
async def get_algorithm_statistics():
    """Get overall algorithm performance statistics"""
    try:
        db_service = await get_exam_db_service()
        stats = await db_service.get_algorithm_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

@router.post("/compare", summary="Compare Algorithm Runs")
async def compare_algorithm_runs(run_ids: List[str]):
    """Compare multiple algorithm runs and generate ranking"""
    try:
        if len(run_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 run IDs required for comparison")
        
        db_service = await get_exam_db_service()
        comparison = await db_service.get_algorithm_comparison(run_ids)
        
        return {
            "success": True,
            "comparison": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing algorithms: {str(e)}")

@router.post("/run-with-evaluation", response_model=ExamAlgorithmResponse, summary="Run Algorithm with Evaluation")
async def run_algorithm_with_evaluation(request: ExamAlgorithmRequest):
    """Run an algorithm and store evaluation results in database"""
    try:
        # Validate algorithm
        available_algorithms = ['nsga2', 'moead', 'cp', 'dqn', 'sarsa', 'hybrid']
        if request.algorithm not in available_algorithms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid algorithm. Available: {available_algorithms}"
            )
        
        exam_runner = await get_exam_runner()
        
        # Run algorithm with evaluation
        result = await exam_runner.run_algorithm_with_evaluation(request.algorithm, request.mode)
        
        return ExamAlgorithmResponse(
            success=result["success"],
            message=result["message"],
            run_id=result.get("run_id"),
            execution_time=result.get("execution_time"),
            evaluation=result.get("evaluation"),
            metrics=result.get("metrics")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running algorithm with evaluation: {str(e)}")

@router.post("/run-all-with-evaluation", summary="Run All Algorithms with Evaluation")
async def run_all_algorithms_with_evaluation(request: ExamBatchRequest):
    """Run all algorithms with evaluation and store results"""
    try:
        exam_runner = await get_exam_runner()
        
        # Run all algorithms with evaluation
        results = await exam_runner.run_all_algorithms_with_evaluation(request.mode)
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "total_algorithms": len(results),
                "successful": sum(1 for r in results.values() if r.get("success", False)),
                "failed": sum(1 for r in results.values() if not r.get("success", False))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running all algorithms with evaluation: {str(e)}")

@router.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint for exam metrics service"""
    try:
        # Try to initialize services
        exam_runner = await get_exam_runner()
        db_service = await get_exam_db_service()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_connected": True,
            "exam_runner_initialized": True,
            "available_algorithms": ['nsga2', 'moead', 'cp', 'dqn', 'sarsa', 'hybrid']
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        } 