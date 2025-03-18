# app/routers/timetable_sliit.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, HTMLResponse
from typing import List, Optional
from datetime import datetime
import os

from app.models.timetable_Sliit_model import (
    TimetableModel,
    TimetableParameters,
    TimetableMetrics
)
from app.utils.database import db
from app.algorithms_2.runner import run_optimization_algorithm

# Pydantic model for timetable creation request
from pydantic import BaseModel, Field

class TimetableCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the timetable")
    algorithm: str = Field(..., description="Algorithm to use: spea2, nsga2, moead, dqn, sarsa, or implicit_q")
    dataset: str = Field("sliit", description="Dataset to use")
    parameters: TimetableParameters = Field(default_factory=TimetableParameters, description="Algorithm parameters")
    user_id: Optional[str] = Field(None, description="ID of the user creating the timetable")
    useAlgorithm2: Optional[bool] = Field(False, description="Flag to use algorithms from algorithms_2 directory")

# Create a dependency function to get the database
def get_db():
    return db

router = APIRouter(
    tags=["timetable_sliit"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate", response_description="Generate new timetable")
async def generate_timetable(
    request: TimetableCreateRequest = Body(...),
    db = Depends(get_db)
):
    try:
        # Prepare a new timetable entry
        new_timetable = TimetableModel(
            name=request.name,
            dataset=request.dataset,
            algorithm=request.algorithm,
            parameters=request.parameters,
            metrics=TimetableMetrics(),  # Initialize with empty metrics
            timetable={},  # Will be populated by the algorithm
            useAlgorithm2=request.useAlgorithm2  # Store which algorithm version was used
        )
        
        # Run optimization algorithm - always use the algorithms_2 module
        # The useAlgorithm2 flag is stored in the database for reference
        result = run_optimization_algorithm(
            algorithm=request.algorithm,
            population=request.parameters.population,
            generations=request.parameters.generations,
            enable_plotting=False,  # Disable plotting for API requests to avoid errors
            learning_rate=request.parameters.learning_rate,
            episodes=request.parameters.episodes,
            epsilon=request.parameters.epsilon
        )
        
        # Save timetable HTML content separately
        timetable_html = result.get("timetable_html", "")
        timetable_html_path = ""
        if timetable_html:
            # Store the HTML content in a separate field for easy access
            timetable_html_path = f"/api/v1/timetable/sliit/html/{result.get('timetable_id', '')}"
        
        # Update the timetable data dictionary directly instead of using the model constructor
        new_timetable.timetable = result["timetable"]
        new_timetable.metrics.hardConstraintViolations = result.get("hardConstraintViolations", 0)
        new_timetable.metrics.softConstraintScore = result.get("softConstraintScore", 0.0)
        new_timetable.metrics.unassignedActivities = result.get("unassignedActivities", 0)
        new_timetable.stats = result.get("stats", {})
        new_timetable.createdAt = datetime.now()
        new_timetable.createdBy = request.user_id
        new_timetable.timetableHtmlPath = timetable_html_path
        
        # Fix: Handle MongoDB operations properly based on client type
        try:
            # Try synchronous operation first
            new_timetable_id = db["timetable_sliit"].insert_one(jsonable_encoder(new_timetable)).inserted_id
            created_timetable = db["timetable_sliit"].find_one({"_id": new_timetable_id})
        except (AttributeError, TypeError):
            # If that fails, try async operation
            new_timetable = await db["timetable_sliit"].insert_one(jsonable_encoder(new_timetable))
            created_timetable = await db["timetable_sliit"].find_one({"_id": new_timetable.inserted_id})
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, 
            content=jsonable_encoder(created_timetable)
        )
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        error_type = type(e).__name__
        error_message = str(e)
        
        # Log the detailed error
        print(f"Error generating timetable: {error_type}: {error_message}\n{traceback_str}")
        
        # Return a more informative error message
        if "object has no attribute" in error_message:
            detail = f"Data model error: {error_message}. The Activity model might be missing required attributes."
        elif "index out of range" in error_message:
            detail = f"Data processing error: {error_message}. There might be an issue with the dataset structure."
        else:
            detail = f"Failed to generate timetable: {error_message}"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

@router.get("/", response_description="List all SLIIT timetables")
async def list_timetables(db = Depends(get_db)):
    try:
        # Try async first
        try:
            timetables = await db["timetable_sliit"].find().to_list(100)
        except (AttributeError, TypeError):
            # Fall back to sync for non-async MongoDB clients
            timetables = list(db["timetable_sliit"].find().limit(100))
        
        return JSONResponse(content=jsonable_encoder(timetables))
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error listing timetables: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list timetables: {str(e)}"
        )

@router.get("/{id}", response_description="Get a single SLIIT timetable")
async def show_timetable(id: str, db = Depends(get_db)):
    try:
        # Try async first
        try:
            timetable = await db["timetable_sliit"].find_one({"_id": id})
        except (AttributeError, TypeError):
            # Fall back to sync for non-async MongoDB clients
            timetable = db["timetable_sliit"].find_one({"_id": id})
        
        if timetable is not None:
            return JSONResponse(content=jsonable_encoder(timetable))
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Timetable with ID {id} not found"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error getting timetable: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timetable: {str(e)}"
        )

@router.get("/html/{timetable_id}", response_description="Get timetable HTML visualization")
async def get_timetable_html(timetable_id: str, db = Depends(get_db)):
    try:
        # Try async first
        try:
            timetable = await db["timetable_sliit"].find_one({"_id": timetable_id})
        except (AttributeError, TypeError):
            # Fall back to sync for non-async MongoDB clients
            timetable = db["timetable_sliit"].find_one({"_id": timetable_id})
        
        if timetable is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Timetable with ID {timetable_id} not found"
            )
        
        # Import the timetable converter
        from app.algorithms_2.timetable_converter import convert_mongodb_timetable
        from app.algorithms_2.timetable_html_generator import generate_timetable_html
        import importlib
        import sys
        
        # Add necessary paths for imports used by the HTML generator
        scheduler_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "TimeTableScheduler")
        if scheduler_path not in sys.path:
            sys.path.append(scheduler_path)
        
        # Ensure the Data_Loading module can be imported by dynamically creating it if needed
        try:
            import Data_Loading
        except ImportError:
            # Create temporary module with mock data structures
            data_loading_module = type(sys)(name="Data_Loading")
            data_loading_module.__file__ = "Data_Loading.py"
            
            # Add mock data structures needed by html generator
            data_loading_module.slots = ["MON1", "MON2", "MON3", "MON4", "MON5", "MON6", "MON7", "MON8", 
                                         "TUE1", "TUE2", "TUE3", "TUE4", "TUE5", "TUE6", "TUE7", "TUE8",
                                         "WED1", "WED2", "WED3", "WED4", "WED5", "WED6", "WED7", "WED8",
                                         "THU1", "THU2", "THU3", "THU4", "THU5", "THU6", "THU7", "THU8",
                                         "FRI1", "FRI2", "FRI3", "FRI4", "FRI5", "FRI6", "FRI7", "FRI8"]
            data_loading_module.activities_dict = {}
            data_loading_module.groups_dict = {}
            data_loading_module.spaces_dict = {}
            data_loading_module.lecturers_dict = {}
            
            # Add the module to sys.modules
            sys.modules["Data_Loading"] = data_loading_module
        
        # Check if output directory exists, create if not
        output_dir = os.environ.get("OUTPUT_DIR", "./app/algorithms_2/output")
        os.makedirs(output_dir, exist_ok=True)
        html_file_path = os.path.join(output_dir, "timetable.html")
        
        # Convert MongoDB timetable to the format expected by the HTML generator
        converted_data = convert_mongodb_timetable(timetable["timetable"])
        
        # Update the required module variables
        import Data_Loading
        Data_Loading.activities_dict = converted_data["activities_dict"]
        Data_Loading.groups_dict = converted_data["groups_dict"]
        Data_Loading.spaces_dict = converted_data["spaces_dict"]
        Data_Loading.lecturers_dict = converted_data["lecturers_dict"]
        
        # Generate HTML from the converted timetable data
        generate_timetable_html(converted_data["timetable"], os.path.join(output_dir, "timetable.html"))
            
        # Return the HTML content
        try:
            with open(html_file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
                
            return HTMLResponse(content=html_content, status_code=200)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading timetable HTML: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error generating HTML for timetable: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate timetable visualization: {str(e)}"
        )

@router.get("/stats/{timetable_id}", response_description="Get timetable statistics")
async def get_timetable_stats(timetable_id: str, db = Depends(get_db)):
    try:
        # Try async first
        try:
            timetable = await db["timetable_sliit"].find_one({"_id": timetable_id})
        except (AttributeError, TypeError):
            # Fall back to sync for non-async MongoDB clients
            timetable = db["timetable_sliit"].find_one({"_id": timetable_id})
        
        if timetable is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Timetable with ID {timetable_id} not found"
            )
        
        # Basic metrics from the timetable
        metrics = timetable.get("metrics", {})
        stats = timetable.get("stats", {})
        
        # Return combined statistics
        response_data = {
            "metrics": {
                # Include optimization metrics for frontend display
                "room_utilization": metrics.get("room_utilization", 0.0),
                "teacher_satisfaction": metrics.get("teacher_satisfaction", 0.0),
                "student_satisfaction": metrics.get("student_satisfaction", 0.0),
                "time_efficiency": metrics.get("time_efficiency", 0.0)
            },
            "basic": {
                "hardConstraintViolations": metrics.get("hardConstraintViolations", 0),
                "softConstraintScore": metrics.get("softConstraintScore", 0.0),
                "unassignedActivities": metrics.get("unassignedActivities", 0)
            },
            "detailed": {
                "hard_constraints": {
                    "room_conflicts": 0,
                    "time_conflicts": 0, 
                    "distribution_conflicts": 0,
                    "student_conflicts": 0,
                    "capacity_violations": 0
                },
                "soft_constraints": {
                    "room_preferences": 0.0,
                    "time_preferences": 0.0,
                    "distribution_preferences": 0.0
                }
            },
            "algorithm": {
                "name": timetable.get("algorithm", ""),
                "parameters": timetable.get("parameters", {}),
                "runTime": stats.get("execution_time", stats.get("runTime", ""))
            },
            "timetable": {
                "id": timetable_id,
                "name": timetable.get("name", ""),
                "createdAt": timetable.get("createdAt", ""),
                "totalSlots": len(timetable.get("timetable", {})),
                "totalRooms": sum(1 for slot in timetable.get("timetable", {}).values() 
                                if isinstance(slot, dict) for _ in slot.keys())
            }
        }
        
        # Add performance metrics if available
        if "performanceMetrics" in stats:
            response_data["performance"] = stats["performanceMetrics"]
        
        # Add constraint violations breakdown if available
        if "constraint_violations" in stats:
            violations = stats["constraint_violations"]
            if "total_counts" in violations:
                response_data["constraints"] = violations["total_counts"]
                
                # Also update the detailed metrics
                total_counts = violations["total_counts"]
                response_data["detailed"]["hard_constraints"] = {
                    "room_conflicts": total_counts.get("room_conflicts", 0),
                    "time_conflicts": total_counts.get("time_conflicts", 0),
                    "distribution_conflicts": total_counts.get("distribution_conflicts", 0),
                    "student_conflicts": total_counts.get("student_conflicts", 0),
                    "capacity_violations": total_counts.get("capacity_violations", 0)
                }
        
        return JSONResponse(content=jsonable_encoder(response_data))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error getting timetable stats: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timetable stats: {str(e)}"
        )