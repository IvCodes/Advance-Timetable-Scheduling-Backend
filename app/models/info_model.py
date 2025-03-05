from typing import List, Optional
from app.models.base_model import MongoBaseModel

class UniversityInfo(MongoBaseModel):
    institution_name: str
    description: str
    
    model_config = {
        "populate_by_name": True
    }

class DayOfOperation(MongoBaseModel):
    name: str 
    code: Optional[str] = None
    order: Optional[int] = None
    long_name: Optional[str] = None  
    
    model_config = {
        "populate_by_name": True
    }

class PeriodOfOperation(MongoBaseModel):
    name: str
    long_name: Optional[str] = None
    is_interval: Optional[bool] = False
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    order: Optional[int] = None
    
    model_config = {
        "populate_by_name": True
    }
