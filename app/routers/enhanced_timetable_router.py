"""
Enhanced Timetable Router for FastAPI Backend
Provides endpoints for running algorithms with enhanced HTML generation and student ID mappings
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
import asyncio
from datetime import datetime

# Import the enhanced algorithm runner
import sys
sys.path.append('app/algorithms_2')
from enhanced_algorithm_runner import EnhancedAlgorithmRunner
from enhanced_data_loader import enhanced_data_loader

router = APIRouter(prefix="/api/enhanced-timetable", tags=["Enhanced Timetable"])

# Global runner instance
enhanced_runner = EnhancedAlgorithmRunner()

# Pydantic models for request/response
class AlgorithmRequest(BaseModel):
    algorithm: str
    mode: str = "standard"
    generate_html: bool = True

class AlgorithmResponse(BaseModel):
    success: bool
    message: str
    html_path: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

class BatchAlgorithmRequest(BaseModel):
    mode: str = "standard"
    generate_html: bool = True
    algorithms: Optional[List[str]] = None  # If None, run all algorithms

class DatasetStatsResponse(BaseModel):
    total_students: int
    total_activities: int
    total_groups: int
    total_lecturers: int
    total_rooms: int
    total_slots: int
    student_id_sample: List[str]
    group_sample: List[str]

class StudentMappingResponse(BaseModel):
    student_id: str
    group_id: str
    activities: List[str]
    total_activities: int

@router.get("/", summary="Enhanced Timetable API Info")
async def get_api_info():
    """Get information about the Enhanced Timetable API"""
    return {
        "name": "Enhanced SLIIT Computing Timetable API",
        "version": "1.0.0",
        "description": "API for running optimization algorithms with enhanced HTML generation and student ID mappings",
        "features": [
            "Student ID key-value pair mappings",
            "Enhanced HTML timetable generation",
            "Multiple algorithm support",
            "Configurable run modes",
            "Real-time progress tracking"
        ],
        "available_algorithms": list(enhanced_runner.available_algorithms.keys()),
        "available_modes": list(enhanced_runner.run_modes.keys())
    }

@router.get("/dataset-stats", response_model=DatasetStatsResponse, summary="Get Dataset Statistics")
async def get_dataset_stats():
    """Get comprehensive statistics about the dataset including student ID mappings"""
    try:
        stats = enhanced_runner.get_algorithm_statistics()
        mappings = enhanced_data_loader.export_student_mappings()
        
        # Get sample student IDs and groups
        student_sample = list(mappings['student_id_to_activities'].keys())[:10]
        group_sample = list(mappings['group_id_to_students'].keys())[:5]
        
        return DatasetStatsResponse(
            total_students=stats['total_students'],
            total_activities=stats['total_activities'],
            total_groups=stats['total_groups'],
            total_lecturers=stats['total_lecturers'],
            total_rooms=stats['total_rooms'],
            total_slots=stats['total_slots'],
            student_id_sample=student_sample,
            group_sample=group_sample
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dataset stats: {str(e)}")

@router.get("/student-mapping/{student_id}", response_model=StudentMappingResponse, summary="Get Student Mapping")
async def get_student_mapping(student_id: str):
    """Get detailed mapping information for a specific student ID"""
    try:
        activities = enhanced_data_loader.get_student_activities(student_id)
        group_id = enhanced_data_loader.get_student_group(student_id)
        
        if group_id is None:
            raise HTTPException(status_code=404, detail=f"Student ID {student_id} not found")
        
        return StudentMappingResponse(
            student_id=student_id,
            group_id=group_id,
            activities=activities,
            total_activities=len(activities)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting student mapping: {str(e)}")

@router.get("/algorithms", summary="Get Available Algorithms")
async def get_available_algorithms():
    """Get list of available algorithms with descriptions"""
    return {
        "algorithms": enhanced_runner.available_algorithms,
        "run_modes": enhanced_runner.run_modes
    }

@router.post("/run-algorithm", response_model=AlgorithmResponse, summary="Run Single Algorithm")
async def run_algorithm(request: AlgorithmRequest):
    """Run a single optimization algorithm with enhanced HTML generation"""
    try:
        # Validate algorithm and mode
        if request.algorithm not in enhanced_runner.available_algorithms:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid algorithm. Available: {list(enhanced_runner.available_algorithms.keys())}"
            )
        
        if request.mode not in enhanced_runner.run_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode. Available: {list(enhanced_runner.run_modes.keys())}"
            )
        
        # Run the algorithm
        start_time = datetime.now()
        success, message, html_path = enhanced_runner.run_single_algorithm(
            request.algorithm, 
            request.mode, 
            request.generate_html
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare response
        response = AlgorithmResponse(
            success=success,
            message=message,
            html_path=html_path,
            execution_time=execution_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running algorithm: {str(e)}")

@router.post("/run-all-algorithms", summary="Run All Algorithms")
async def run_all_algorithms(request: BatchAlgorithmRequest):
    """Run all algorithms or a subset with enhanced HTML generation"""
    try:
        start_time = datetime.now()
        
        # If specific algorithms are requested, validate them
        if request.algorithms:
            invalid_algorithms = [alg for alg in request.algorithms 
                                if alg not in enhanced_runner.available_algorithms]
            if invalid_algorithms:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid algorithms: {invalid_algorithms}"
                )
        
        # Run algorithms
        if request.algorithms:
            # Run only specified algorithms
            results = {}
            for algorithm in request.algorithms:
                success, message, html_path = enhanced_runner.run_single_algorithm(
                    algorithm, request.mode, request.generate_html
                )
                results[algorithm] = {
                    'success': success,
                    'message': message,
                    'html_path': html_path,
                    'description': enhanced_runner.available_algorithms[algorithm]
                }
        else:
            # Run all algorithms
            results = enhanced_runner.run_all_algorithms(request.mode, request.generate_html)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Generate summary
        successful = [alg for alg, result in results.items() if result['success']]
        failed = [alg for alg, result in results.items() if not result['success']]
        
        return {
            "success": True,
            "message": f"Batch execution completed in {execution_time:.1f}s",
            "execution_time": execution_time,
            "results": results,
            "summary": {
                "total_algorithms": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(results) * 100 if results else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running algorithms: {str(e)}")

@router.get("/download-html/{filename}", summary="Download Enhanced HTML")
async def download_html(filename: str):
    """Download generated enhanced HTML timetable file"""
    try:
        # Construct file path
        file_path = os.path.join(enhanced_runner.output_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="HTML file not found")
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='text/html'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.get("/view-html/{filename}", summary="View Enhanced HTML")
async def view_html(filename: str):
    """View generated enhanced HTML timetable file in browser"""
    try:
        # Construct file path
        file_path = os.path.join(enhanced_runner.output_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="HTML file not found")
        
        # Return file for viewing
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='text/html'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing file: {str(e)}")

@router.delete("/delete-html/{filename}", summary="Delete Enhanced HTML")
async def delete_html(filename: str):
    """Delete generated enhanced HTML timetable file"""
    try:
        # Construct file path
        file_path = os.path.join(enhanced_runner.output_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="HTML file not found")
        
        # Delete the file
        os.remove(file_path)
        
        return {
            "success": True,
            "message": f"File '{filename}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@router.get("/list-generated-files", summary="List Generated Files")
async def list_generated_files():
    """List all generated HTML files and reports"""
    try:
        output_dir = enhanced_runner.output_dir
        
        if not os.path.exists(output_dir):
            return {"html_files": [], "report_files": [], "total_files": 0}
        
        all_files = os.listdir(output_dir)
        
        # Categorize files
        html_files = [f for f in all_files if f.endswith('.html')]
        report_files = [f for f in all_files if f.endswith('.txt')]
        other_files = [f for f in all_files if not f.endswith(('.html', '.txt'))]
        
        # Get file details
        def get_file_info(filename):
            file_path = os.path.join(output_dir, filename)
            stat = os.stat(file_path)
            return {
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        
        return {
            "html_files": [get_file_info(f) for f in sorted(html_files, reverse=True)],
            "report_files": [get_file_info(f) for f in sorted(report_files, reverse=True)],
            "other_files": [get_file_info(f) for f in sorted(other_files, reverse=True)],
            "total_files": len(all_files),
            "output_directory": output_dir
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.post("/generate-test-html", summary="Generate Test HTML")
async def generate_test_html():
    """Generate a test enhanced HTML timetable without running any algorithm"""
    try:
        from Data_Loading import slots, spaces_dict
        
        # Create empty timetable for testing
        test_timetable = {slot: {room: None for room in spaces_dict} for slot in slots}
        
        # Generate HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"test_enhanced_timetable_{timestamp}.html"
        html_path = os.path.join(enhanced_runner.output_dir, html_filename)
        
        from enhanced_html_generator import generate_enhanced_timetable_html
        generated_path = generate_enhanced_timetable_html(test_timetable, html_path)
        
        return {
            "success": True,
            "message": "Test HTML generated successfully",
            "html_path": generated_path,
            "filename": html_filename,
            "download_url": f"/api/enhanced-timetable/download-html/{html_filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating test HTML: {str(e)}")

@router.delete("/cleanup-files", summary="Cleanup Generated Files")
async def cleanup_files(keep_latest: int = 5):
    """Clean up old generated files, keeping only the latest ones"""
    try:
        output_dir = enhanced_runner.output_dir
        
        if not os.path.exists(output_dir):
            return {"message": "No files to cleanup", "deleted_count": 0}
        
        all_files = os.listdir(output_dir)
        
        # Sort files by modification time (newest first)
        files_with_time = []
        for filename in all_files:
            file_path = os.path.join(output_dir, filename)
            mtime = os.path.getmtime(file_path)
            files_with_time.append((filename, mtime))
        
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        # Keep only the latest files
        files_to_delete = files_with_time[keep_latest:]
        deleted_count = 0
        
        for filename, _ in files_to_delete:
            file_path = os.path.join(output_dir, filename)
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Could not delete {filename}: {e}")
        
        return {
            "message": f"Cleanup completed. Kept {min(len(files_with_time), keep_latest)} latest files.",
            "deleted_count": deleted_count,
            "remaining_files": len(files_with_time) - deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")

@router.get("/health", summary="Health Check")
async def health_check():
    """Check the health of the enhanced timetable service"""
    try:
        # Test data loader
        stats = enhanced_runner.get_algorithm_statistics()
        
        # Test output directory
        output_dir_exists = os.path.exists(enhanced_runner.output_dir)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "data_loader": "operational",
            "output_directory": "accessible" if output_dir_exists else "not_accessible",
            "dataset_loaded": stats['total_students'] > 0,
            "available_algorithms": len(enhanced_runner.available_algorithms),
            "student_mappings": "active"
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}") 