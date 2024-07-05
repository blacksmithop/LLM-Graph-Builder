from pydantic import BaseModel
from typing import Union, List

class InsightNode(BaseModel):
    text: str
    insightID: int
