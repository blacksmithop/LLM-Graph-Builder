from pydantic import BaseModel
from typing import Union, List

class InsightNode(BaseModel):
    id: int
    text: str
    insightID: int
