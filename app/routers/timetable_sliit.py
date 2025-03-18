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
    algorithm: str = Field(..., description="Algorithm to use: spea2, nsga2, or moead")
    dataset: str = Field("sliit", description="Dataset to use")
    parameters: TimetableParameters = Field(default_factory=TimetableParameters, description="Algorithm parameters")
    user_id: Optional[str] = Field(None, description="ID of the user creating the timetable")

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
        # Run optimization algorithm
        result = run_optimization_algorithm(
            algorithm=request.algorithm,
            population=request.parameters.population,
            generations=request.parameters.generations,
            dataset=request.dataset,
            enable_plotting=False  # Disable plotting for API requests to avoid errors
        )
        
        # Save timetable HTML content separately
        timetable_html = result.get("timetable_html", "")
        timetable_html_path = ""
        if timetable_html:
            # Store the HTML content in a separate field for easy access
            timetable_html_path = f"/api/v1/timetable/sliit/html/{result.get('timetable_id', '')}"
        
        # Prepare the timetable data dictionary directly instead of using the model constructor
        timetable_data = {
            "name": request.name,
            "dataset": request.dataset,
            "algorithm": request.algorithm,
            "parameters": jsonable_encoder(request.parameters),
            "metrics": {
                "hardConstraintViolations": result.get("hardConstraintViolations", 0),
                "softConstraintScore": result.get("softConstraintScore", 0.0),
                "unassignedActivities": result.get("unassignedActivities", 0)
            },
            "stats": result.get("stats", {}),
            "createdAt": datetime.now(),
            "createdBy": request.user_id,
            "timetable": result["timetable"],
            "timetableHtmlPath": timetable_html_path
        }
        
        # Fix: Handle MongoDB operations properly based on client type
        try:
            # Try synchronous operation first
            new_timetable_id = db["timetable_sliit"].insert_one(timetable_data).inserted_id
            created_timetable = db["timetable_sliit"].find_one({"_id": new_timetable_id})
        except (AttributeError, TypeError):
            # If that fails, try async operation
            new_timetable = await db["timetable_sliit"].insert_one(timetable_data)
            created_timetable = await db["timetable_sliit"].find_one({"_id": new_timetable.inserted_id})
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, 
            content=jsonable_encoder(created_timetable)
        )
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error generating timetable: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate timetable: {str(e)}"
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
        
        # Check if HTML file exists
        output_dir = os.environ.get("OUTPUT_DIR", "./app/algorithms_2/output")
        html_file_path = os.path.join(output_dir, "timetable.html")
        
        if not os.path.exists(html_file_path):
            # If file doesn't exist, try to generate it from timetable data
            from app.algorithms_2.timetable_html_generator import generate_timetable_html
            
            try:
                # Generate HTML from the timetable data
                generate_timetable_html(timetable["timetable"], output_dir)
            except Exception as e:
                print(f"Error generating HTML for timetable: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not generate HTML visualization for this timetable"
                )
        
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
        print(f"Error getting timetable HTML: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timetable HTML: {str(e)}"
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
        
        # Extract the statistics from the timetable
        stats = {
            "metrics": timetable.get("metrics", {}),
            "stats": timetable.get("stats", {}),
            "algorithm": timetable.get("algorithm", ""),
            "parameters": timetable.get("parameters", {})
        }
        
        return JSONResponse(content=jsonable_encoder(stats))
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