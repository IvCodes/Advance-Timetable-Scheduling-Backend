"""
Enhanced Timetable API Router
Provides endpoints for enhanced exam timetable generation with student ID mappings
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import numpy as np
import re

# Add the exams directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'exams'))

# Try to import the enhanced modules
ENHANCED_MODULES_AVAILABLE = False

try:
    from app.exams.core.sta83_data_loader import STA83DataLoader
    from app.exams.utilities.enhanced_exam_timetable_html_generator import EnhancedExamTimetableHTMLGenerator
    from app.exams.algorithm_runner import AlgorithmRunner
    ENHANCED_MODULES_AVAILABLE = True
    print("Successfully imported enhanced modules")
except ImportError as e:
    print(f"Warning: Could not import primary enhanced modules: {e}. Enhanced features will be unavailable.")
    ENHANCED_MODULES_AVAILABLE = False
    # Set to None for type checking
    STA83DataLoader = None
    EnhancedExamTimetableHTMLGenerator = None
    AlgorithmRunner = None

router = APIRouter(prefix="/api/enhanced-timetable", tags=["Enhanced Timetable"])

# Request/Response Models
class AlgorithmRunRequest(BaseModel):
    algorithm: str
    mode: str = "standard"
    generate_html: bool = True

class BatchRunRequest(BaseModel):
    mode: str = "standard"
    generate_html: bool = True

class AlgorithmRunResponse(BaseModel):
    success: bool
    message: str
    algorithm: str
    mode: str
    execution_time: Optional[float] = None
    html_path: Optional[str] = None

class BatchRunResponse(BaseModel):
    success: bool
    message: str
    summary: Dict[str, Any]

class DatasetStatsResponse(BaseModel):
    total_students: int
    total_activities: int
    total_groups: int
    total_slots: int
    student_id_sample: List[str]
    activities_per_student_avg: float
    students_per_activity_avg: float
    students_per_group_avg: float

class AlgorithmsResponse(BaseModel):
    algorithms: Dict[str, str]
    run_modes: Dict[str, Dict[str, Any]]

class GeneratedFilesResponse(BaseModel):
    html_files: List[Dict[str, Any]]

# Global variables for caching
_data_loader = None
_algorithm_runner = None

def get_data_loader():
    """Get or create the STA83 data loader (primarily for /dataset-stats)"""
    global _data_loader
    if _data_loader is None and ENHANCED_MODULES_AVAILABLE and STA83DataLoader is not None:
        try:
            _data_loader = STA83DataLoader(crs_file='app/exams/data/sta-f-83.crs', 
                                           stu_file='app/exams/data/sta-f-83.stu')
            if not _data_loader.load_data():
                print("Error: Global STA83DataLoader failed to load data.")
                _data_loader = None
        except Exception as e:
            print(f"Error creating global STA83DataLoader: {e}")
            _data_loader = None
    return _data_loader

def get_html_generator(data_loader_instance):
    """Get or create the HTML generator instance. Requires a data_loader."""
    if (ENHANCED_MODULES_AVAILABLE and EnhancedExamTimetableHTMLGenerator is not None and 
        data_loader_instance and hasattr(data_loader_instance, 'is_loaded') and data_loader_instance.is_loaded):
        try:
            return EnhancedExamTimetableHTMLGenerator(data_loader_instance)
        except Exception as e:
            print(f"Error creating EnhancedExamTimetableHTMLGenerator: {e}")
            return None
    return None

def get_algorithm_runner():
    """Get or create the algorithm runner instance"""
    global _algorithm_runner
    if _algorithm_runner is None and ENHANCED_MODULES_AVAILABLE and AlgorithmRunner is not None:
        try:
            _algorithm_runner = AlgorithmRunner()
        except Exception as e:
            print(f"Error creating AlgorithmRunner: {e}")
            _algorithm_runner = None
    return _algorithm_runner

@router.get("/health")
async def health_check():
    loader = get_data_loader()
    runner = get_algorithm_runner()
    return {
        "status": "healthy",
        "enhanced_modules_available": ENHANCED_MODULES_AVAILABLE,
        "data_loader_for_stats": "available" if loader and hasattr(loader, 'is_loaded') and loader.is_loaded else "unavailable",
        "algorithm_runner": "available" if runner else "unavailable",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/dataset-stats", response_model=DatasetStatsResponse)
async def get_dataset_stats():
    if not ENHANCED_MODULES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced modules not available. Cannot provide dataset stats.")
    
    loader = get_data_loader()
    if not loader or not hasattr(loader, 'is_loaded') or not loader.is_loaded:
        raise HTTPException(status_code=503, detail="STA83 Data loader not available or data not loaded for stats.")
    
    try:
        stats = loader.analyze_dataset()
        return DatasetStatsResponse(
            total_students=stats.get('num_students', 0),
            total_activities=stats.get('num_exams', 0),
            total_groups=0,
            total_slots=0,
            student_id_sample=[],
            activities_per_student_avg=stats.get('avg_exams_per_student', 0.0),
            students_per_activity_avg=float(np.mean(list(loader.exam_student_counts.values()))) if loader.exam_student_counts else 0.0,
            students_per_group_avg=0.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dataset stats: {str(e)}")

@router.get("/algorithms", response_model=AlgorithmsResponse)
async def get_algorithms_from_runner():
    if not ENHANCED_MODULES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced modules not available. Cannot provide algorithms.")
    
    runner = get_algorithm_runner()
    if not runner:
        raise HTTPException(status_code=503, detail="Algorithm runner not available")
    
    algo_descriptions = {
        "nsga2": "NSGA-II: Multi-objective genetic algorithm for Pareto optimization.",
        "moead": "MOEA/D: Multi-objective evolutionary algorithm based on decomposition.",
        "cp": "Constraint Programming: Exact solver for combinatorial problems.",
        "dqn": "DQN: Deep Q-Network, a reinforcement learning algorithm.",
        "sarsa": "SARSA: On-policy reinforcement learning algorithm.",
        "hybrid": "Hybrid NSGA2-DQN: Combines NSGA-II with DQN for refinement.",
        "hybrid_sarsa": "Hybrid NSGA2-SARSA: Combines NSGA-II with SARSA for refinement."
    }
    
    available_algos = {key: algo_descriptions.get(key, "N/A") for key in runner.run_modes['standard'].keys()}
    return AlgorithmsResponse(algorithms=available_algos, run_modes=runner.run_modes)

@router.post("/run-algorithm", response_model=AlgorithmRunResponse)
async def run_algorithm_endpoint(request: AlgorithmRunRequest, background_tasks: BackgroundTasks):
    if not ENHANCED_MODULES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced modules not available. Cannot run algorithms.")
    
    runner = get_algorithm_runner()
    if not runner:
        raise HTTPException(status_code=503, detail="Algorithm runner not available")

    try:
        success, message, schedule_data, runtime_seconds = runner.run_single_algorithm(request.algorithm, request.mode)
        
        html_path_generated = None
        if success and schedule_data and request.generate_html and STA83DataLoader is not None:
            try:
                temp_data_loader_for_html = STA83DataLoader(crs_file='app/exams/data/sta-f-83.crs', 
                                                            stu_file='app/exams/data/sta-f-83.stu')
                if temp_data_loader_for_html.load_data():
                    html_generator_instance = get_html_generator(temp_data_loader_for_html)
                    if html_generator_instance:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_filename = f"timetable_{request.algorithm}_{request.mode}_{timestamp}.html"
                        output_dir = "app/exams/output/html"
                        os.makedirs(output_dir, exist_ok=True)
                        full_output_path = os.path.join(output_dir, output_filename)
                        
                        # Convert schedule_data format from algorithm runner to HTML generator format
                        # Algorithm runner returns: {'slot_to_exams': {slot_id: [exam_id1, exam_id2, ...]}} (1-indexed exam IDs)
                        # HTML generator expects: {slot_id: [exam_idx1, exam_idx2, ...]} (0-indexed exam indices)
                        html_schedule_data = {}
                        if 'slot_to_exams' in schedule_data:
                            for slot_id, exam_ids in schedule_data['slot_to_exams'].items():
                                # Convert 1-indexed exam IDs to 0-indexed exam indices
                                exam_indices = [exam_id - 1 for exam_id in exam_ids]
                                html_schedule_data[slot_id] = exam_indices
                        else:
                            print("Warning: schedule_data does not contain 'slot_to_exams' key")
                            html_schedule_data = schedule_data  # Fallback to original format
                        
                        # Extract penalty information from algorithm results
                        penalty_info = None
                        if isinstance(schedule_data, dict):
                            penalty_info = {
                                'total_penalty': schedule_data.get('penalty', 0),
                                'conflict_count': schedule_data.get('conflicts', 0),
                                'proximity_penalty': schedule_data.get('proximity_penalty', 0),
                                'penalty_breakdown': {
                                    'direct_conflicts': schedule_data.get('conflicts', 0) * 100,
                                    'proximity_conflicts': schedule_data.get('proximity_penalty', 0)
                                }
                            }
                        
                        html_content = html_generator_instance.generate_html_timetable_from_schedule_dict(
                            schedule_data=html_schedule_data, 
                            output_file=full_output_path,
                            penalty_info=penalty_info
                        )
                        
                        if html_content and os.path.exists(full_output_path):
                            html_path_generated = full_output_path
                            print(f"HTML generated successfully: {html_path_generated}")
                        else:
                            print("HTML generation failed - no content or file not created")
                else:
                    print("Warning: Failed to load data for HTML generation in API.")
            except Exception as html_e:
                print(f"Error generating HTML in API: {html_e}")
                import traceback
                traceback.print_exc()

        return AlgorithmRunResponse(
            success=success,
            message=message,
            algorithm=request.algorithm,
            mode=request.mode,
            execution_time=runtime_seconds,
            html_path=html_path_generated
        )
        
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error running algorithm endpoint: {str(e)}\n{tb_str}")

@router.post("/run-all-algorithms", response_model=BatchRunResponse)
async def run_all_algorithms_endpoint(request: BatchRunRequest, background_tasks: BackgroundTasks):
    if not ENHANCED_MODULES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced modules not available. Cannot run algorithms.")
    
    runner = get_algorithm_runner()
    if not runner:
        raise HTTPException(status_code=503, detail="Algorithm runner not available")
    
    try:
        results = runner.run_all_algorithms(request.mode)
        
        batch_success = True 
        batch_message = "Batch algorithm run process initiated or completed. Check summary for details."
        if isinstance(results, dict) and "error" in results:
            batch_success = False
            error_value = results.get("error", "An error occurred during batch processing.")
            batch_message = str(error_value) if not isinstance(error_value, str) else error_value

        return BatchRunResponse(
            success=batch_success, 
            message=batch_message, 
            summary=results
        )

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error in run all algorithms endpoint: {str(e)}\n{tb_str}")

@router.get("/list-generated-files", response_model=GeneratedFilesResponse)
async def list_generated_files():
    """List all generated HTML files"""
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'exams', 'output', 'html')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        html_files = []
        pattern = os.path.join(output_dir, "*.html")
        
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            stat = os.stat(filepath)
            
            html_files.append({
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        html_files.sort(key=lambda x: x["created"], reverse=True)
        return GeneratedFilesResponse(html_files=html_files)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.get("/view-html/{filename}")
async def view_html(filename: str):
    """View a generated HTML file in browser"""
    try:
        if not filename.endswith('.html') or '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'exams', 'output', 'html')
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read and return HTML content directly for viewing
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@router.get("/download-html/{filename}")
async def download_html(filename: str):
    """Download a generated HTML file"""
    try:
        if not filename.endswith('.html') or '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'exams', 'output', 'html')
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            filepath,
            media_type="application/octet-stream",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@router.post("/generate-test-html")
async def generate_test_html_endpoint():
    """Generates a test HTML timetable using a dummy schedule and the HTML generator."""
    if not ENHANCED_MODULES_AVAILABLE:
        raise HTTPException(status_code=501, detail="HTML generation modules not available.")

    if STA83DataLoader is None:
        raise HTTPException(status_code=500, detail="STA83DataLoader not available.")
    
    try:
        test_data_loader_for_html = STA83DataLoader(crs_file='app/exams/data/sta-f-83.crs', 
                                                    stu_file='app/exams/data/sta-f-83.stu')
        if not test_data_loader_for_html.load_data():
            raise HTTPException(status_code=500, detail="Failed to load test data for HTML generation.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading test data: {str(e)}")

    html_generator = get_html_generator(test_data_loader_for_html)
    if not html_generator:
        raise HTTPException(status_code=500, detail="Failed to create HTML generator instance.")

    test_schedule = {
        0: [0, 1],
        1: [2, 3, 4],
        2: [5]
    }

    try:
        output_dir = "app/exams/output/html"
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"test_timetable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        full_output_path = os.path.join(output_dir, output_filename)

        html_content = html_generator.generate_html_timetable_from_schedule_dict(
            schedule_data=test_schedule, 
            output_file=full_output_path
        )
        
        if html_content and os.path.exists(full_output_path):
            return {"message": "Test HTML generated successfully", "path": full_output_path, "content_length": len(html_content)}
        else:
            raise HTTPException(status_code=500, detail="HTML content generation failed.")
            
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error generating test HTML: {str(e)}\n{tb_str}")

@router.delete("/delete-html/{filename}")
async def delete_html_file(filename: str):
    """Delete a specific HTML file"""
    try:
        if not filename.endswith('.html') or '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'exams', 'output', 'html')
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(filepath)
        
        return {
            "success": True,
            "message": f"File '{filename}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@router.delete("/cleanup-files")
async def cleanup_old_files(days_old: int = 7):
    """Clean up HTML files older than specified days"""
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'exams', 'output', 'html')
        if not os.path.exists(output_dir):
            return {"success": True, "message": "No files to clean up", "deleted_count": 0}
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for filepath in glob.glob(os.path.join(output_dir, "*.html")):
            if os.path.getctime(filepath) < cutoff_time:
                os.remove(filepath)
                deleted_count += 1
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} files older than {days_old} days",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up files: {str(e)}")

def get_router():
    """Get the enhanced timetable router"""
    return router 