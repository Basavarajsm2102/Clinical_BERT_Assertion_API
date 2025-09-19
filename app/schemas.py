# Standard library imports
from enum import Enum
from typing import Any, Dict, List, Optional

# Third party imports
from pydantic import BaseModel, Field, validator


class AssertionLabel(str, Enum):
    """Possible assertion labels"""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    POSSIBLE = "POSSIBLE"
    CONDITIONAL = "CONDITIONAL"


class PredictionRequest(BaseModel):
    """Request model for single prediction"""

    sentence: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Clinical sentence to classify",
    )

    @validator("sentence")
    def validate_sentence(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Sentence cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {"example": {"sentence": "The patient denies chest pain."}}
        protected_namespaces = ()


class PredictionResponse(BaseModel):
    """Response model for single prediction"""

    label: str = Field(
        ..., description="Final assertion label (may be enhanced by rules)"
    )
    model_label: str = Field(..., description="Raw model prediction label")
    score: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    rule_applied: Optional[str] = Field(
        None, description="Rule applied for label enhancement"
    )
    prediction_time_ms: Optional[float] = Field(
        None, description="Prediction time in milliseconds"
    )
    request_id: Optional[str] = Field(None, description="Request identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "label": "CONDITIONAL",
                "model_label": "PRESENT",
                "score": 0.9842,
                "rule_applied": "conditional_trigger",
                "prediction_time_ms": 45.2,
                "request_id": "req-12345",
            }
        }
        protected_namespaces = ()


class BatchPredictionRequest(BaseModel):
    """Request model for batch prediction"""

    sentences: List[str] = Field(..., description="List of sentences")

    @validator("sentences")
    def validate_sentences(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Sentences list cannot be empty")

        for i, sentence in enumerate(v):
            if not sentence or not sentence.strip():
                raise ValueError(f"Sentence at index {i} cannot be empty")
            if len(sentence) > 1000:
                raise ValueError(f"Sentence at index {i} too long")

        return [sentence.strip() for sentence in v]


class BatchPredictionResponse(BaseModel):
    """Response model for batch prediction"""

    predictions: List[PredictionResponse] = Field(
        ..., description="List of predictions"
    )
    batch_size: int = Field(..., description="Number of sentences processed")
    total_prediction_time_ms: Optional[float] = Field(
        None, description="Total prediction time"
    )
    request_id: Optional[str] = Field(None, description="Request identifier")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Health status")
    model_loaded: bool = Field(..., description="Model loaded status")
    timestamp: float = Field(..., description="Check timestamp")
    version: Optional[str] = Field("1.0.0", description="API version")
    environment: Optional[str] = Field(None, description="Environment")
    uptime_seconds: Optional[float] = Field(None, description="Uptime in seconds")
    total_predictions: Optional[int] = Field(None, description="Total predictions made")
    system_metrics: Optional[Dict[str, Any]] = Field(None, description="System metrics")
    model_info: Optional[Dict[str, Any]] = Field(None, description="Model information")


class MetricsResponse(BaseModel):
    """System metrics response"""

    total_predictions: int = Field(..., description="Total predictions")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")
    model_loaded: bool = Field(..., description="Model loaded status")


class ModelInfoResponse(BaseModel):
    """Model information response"""

    model_name: str = Field(..., description="Hugging Face model name")
    device: str = Field(..., description="Device model is running on")
    loaded: bool = Field(..., description="Model loaded status")
    labels: List[str] = Field(..., description="Possible prediction labels")
    cuda_available: bool = Field(..., description="CUDA availability")
