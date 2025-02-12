from pydantic import BaseModel, Field, EmailStr, constr, field_validator, validator
from typing import List, Optional

class Timetable(BaseModel):
    code : str
    algorithm: Optional[str] = None
    semester: str  
    timetable: List[dict] = []  