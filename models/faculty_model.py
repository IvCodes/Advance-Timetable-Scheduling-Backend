from pydantic import BaseModel
from typing import Optional

class Faculty(BaseModel):
    code: str
    short_name: str
    long_name: str


