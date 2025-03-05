from typing import Optional
from app.models.base_model import MongoBaseModel


class Module(MongoBaseModel):
    code: str
    name: str
    long_name: str
    description: Optional[str] = None
    
    model_config = {
        "populate_by_name": True
    }
