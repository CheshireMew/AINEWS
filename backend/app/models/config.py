
from typing import Optional, Dict
from pydantic import BaseModel

class TimeWindowsConfig(BaseModel):
    article: Optional[dict] = None
    news: Optional[dict] = None
