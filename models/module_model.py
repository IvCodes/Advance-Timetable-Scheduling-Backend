from pydantic import BaseModel
from typing import Optional


class Module(BaseModel):
    code: str
    name: str
    long_name: str
    description: Optional[str]
