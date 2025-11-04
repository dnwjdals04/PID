from pydantic import BaseModel
from typing import List, Dict, Any


class Detection(BaseModel):
    type: str
    bbox: List[int]  # [x, y, w, h]
    confidence: float


class FrameResult(BaseModel):
    frame: str
    detections: List[Detection]


class AnalysisResult(BaseModel):
    file_id: str
    analysis: List[FrameResult]
