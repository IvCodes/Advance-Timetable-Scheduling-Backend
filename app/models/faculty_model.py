from typing import Optional
from app.models.base_model import MongoBaseModel

class Faculty(MongoBaseModel):
    code: str
    short_name: str
    long_name: str
    
    model_config = {
        "populate_by_name": True
    }
