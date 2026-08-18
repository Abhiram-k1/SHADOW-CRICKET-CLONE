from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class PredictionResponse(BaseModel):
    stance_class: Optional[str] = None
    shot_class: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

class ScoreResponse(BaseModel):
    balance: Optional[float] = None
    alignment: Optional[float] = None
    stance: Optional[float] = None
    power_proxy: Optional[float] = None

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: str
    priority: int
    text: str
    category: Optional[str] = None

    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    id: str
    user_id: str
    image_uri: str
    status: str
    model_version: Optional[str] = None
    created_at: datetime
    prediction: Optional[PredictionResponse] = None
    scores: Optional[ScoreResponse] = None
    recommendations: List[RecommendationResponse] = []

    class Config:
        from_attributes = True
