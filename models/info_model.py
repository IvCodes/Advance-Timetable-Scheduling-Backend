from pydantic import BaseModel
from typing import List

class UniversityInfo(BaseModel):
    institution_name: str
    description: str

class DayOfOperation(BaseModel):
    name: str
    long_name: str

class PeriodOfOperation(BaseModel):
    name: str
    long_name: str
    is_interval: bool
