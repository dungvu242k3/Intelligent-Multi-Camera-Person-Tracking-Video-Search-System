from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchByImageRequest(BaseModel):
    embedding: List[float] = Field(..., description="512-dimensional ReID embedding vector of target person")
    limit: Optional[int] = Field(5, ge=1, le=100)
    threshold: Optional[float] = Field(0.70, ge=0.0, le=1.0)

class SearchResult(BaseModel):
    person_id: str
    score: float
    payload: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]
