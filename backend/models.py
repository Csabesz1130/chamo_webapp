from pydantic import BaseModel
from typing import Dict, Any, Optional
class AnalysisRequest(BaseModel):
    parameters: Dict[str, Any] = {}
class AnalysisResult(BaseModel):
    task_id: str
    status: str
    payload: Optional[Dict[str, Any]]
