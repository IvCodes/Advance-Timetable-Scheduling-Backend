# Pydantic model for MongoDB with FastAPI
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from typing import Dict, List, Optional, Any, Annotated, ClassVar
from datetime import datetime
from bson import ObjectId
import json

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v, info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field_schema):
        return {"type": "string"}

class TimetableParameters(BaseModel):
    population: int = 20
    generations: int = 10
    learning_rate: float = 0.001
    episodes: int = 100
    epsilon: float = 0.1
    
class TimetableMetrics(BaseModel):
    hardConstraintViolations: int = 0
    softConstraintScore: float = 0.0
    unassignedActivities: int = 0
    
class TimetableModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    dataset: str
    algorithm: str
    parameters: TimetableParameters
    metrics: TimetableMetrics
    stats: Dict[str, Any] = Field(default_factory=dict)  # Additional algorithm statistics
    createdAt: datetime = Field(default_factory=datetime.now)
    createdBy: Optional[PyObjectId] = None
    timetable: Dict[str, Any]  # Store the timetable structure
    timetableHtmlPath: Optional[str] = None  # Path to the timetable HTML visualization
    useAlgorithm2: Optional[bool] = False  # Flag indicating if algorithms_2 directory was used
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "SPEA2 Timetable",
                "dataset": "sliit",
                "algorithm": "spea2",
                "parameters": {
                    "population": 20,
                    "generations": 10,
                    "learning_rate": 0.001,
                    "episodes": 100,
                    "epsilon": 0.1
                },
                "metrics": {
                    "hardConstraintViolations": 5,
                    "softConstraintScore": 0.85,
                    "unassignedActivities": 2
                },
                "stats": {
                    "convergenceData": [],
                    "generationStats": []
                },
                "timetable": {},  # Would contain actual timetable data
                "timetableHtmlPath": "/api/v1/timetable/sliit/html/some-id",
                "useAlgorithm2": False
            }
        }