# app/etl/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.etl.processors import activity_processor, module_processor, space_processor, year_processor
from typing import Optional

router = APIRouter(prefix="/etl", tags=["ETL"])

@router.post("/upload/{entity_type}")
async def upload_file(entity_type: str, file: UploadFile = File(...)):
    """
    Upload and process files for various entity types.
    """
    if file.content_type not in ["text/csv", "application/vnd.ms-excel", 
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload CSV or Excel files.")
    
    try:
        # Route to appropriate processor based on entity type
        if entity_type == "activities":
            result = await activity_processor.process(file)
        elif entity_type == "modules":
            result = await module_processor.process(file)
        elif entity_type == "years":
            result = await year_processor.process(file)
        elif entity_type == "spaces":
            result = await space_processor.process(file)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported entity type: {entity_type}")
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{entity_type}")
async def get_template(entity_type: str, format: str = "xlsx"):
    """
    Generate and return a template file for a specific entity type.
    Supports both Excel (.xlsx) and CSV (.csv) formats.
    
    Args:
        entity_type: Type of entity (activities, modules, spaces, years)
        format: File format (xlsx or csv)
    """
    from app.etl.template_generators import get_template_generator
    
    if entity_type not in ["activities", "modules", "spaces", "years"]:
        raise HTTPException(status_code=400, detail=f"Unsupported entity type: {entity_type}")
        
    if format.lower() not in ["xlsx", "csv"]:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'xlsx' or 'csv'.")
    
    template = get_template_generator(entity_type, format.lower())
    
    if not template:
        raise HTTPException(status_code=500, detail=f"Failed to generate template for {entity_type}")
        
    return template