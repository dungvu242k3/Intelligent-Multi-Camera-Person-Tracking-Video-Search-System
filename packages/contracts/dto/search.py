from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class SearchByImageRequest(BaseModel):
    embedding: List[float] = Field(..., min_length=512, max_length=512, description="512-dimensional ReID embedding vector of target person")
    limit: Optional[int] = Field(5, ge=1, le=50)
    threshold: Optional[float] = Field(0.70, ge=0.0, le=1.0)

    @field_validator("embedding")
    @classmethod
    def validate_embedding_values(cls, v: List[float]) -> List[float]:
        if any(not isinstance(item, (float, int)) for item in v):
            raise ValueError("Embedding values must be numeric")
        return [float(item) for item in v]

class SearchResult(BaseModel):
    person_id: str
    score: float
    payload: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]
