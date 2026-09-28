from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import (
    BBox,
    Confidence,
    GridMeta,
    LeadTime,
    Probability,
    VarCode,
)

ALL_VARIABLES: list[VarCode] = ["t2m", "tp", "z500", "ws850"]
ALL_LEAD_TIMES: list[LeadTime] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class BustProbabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    variables: list[VarCode] = Field(default_factory=lambda: list(ALL_VARIABLES))
    lead_times: list[LeadTime] = Field(default_factory=lambda: list(ALL_LEAD_TIMES))
    bbox: BBox | None = None


class BustProbabilityLayer(BaseModel):
    variable: VarCode
    lead_time: LeadTime
    values: list[list[Probability]]  # 128x128, or bbox-cropped
    threshold: float                 # tau_v (PRD 0.6)
    bust_frequency: float            # BF_v(t,R) (PRD 2.3)


class BustProbabilityResponse(BaseModel):
    run_id: str
    grid: GridMeta
    layers: list[BustProbabilityLayer]


class BustDetection(BaseModel):
    detection_id: str
    run_id: str
    variable: VarCode
    lead_time: LeadTime
    bbox: BBox
    polygon: dict  # GeoJSON Polygon geometry
    peak_probability: Probability
    mean_probability: Probability
    area_km2: float
    dominant_driver: str  # input channel code (PRD 0.4)
    confidence: Confidence
    created_at: datetime


class BaselineStats(BaseModel):
    mean_rmse: float = Field(ge=0.0)
    mean_mae: float = Field(ge=0.0)
    bust_frequency: float = Field(ge=0.0, le=1.0)
    p90_abs_error: float = Field(ge=0.0)
    std_abs_error: float | None = Field(default=None, ge=0.0)


class BaselinePeriod(BaseModel):
    start: datetime
    end: datetime


class HistoricalBaseline(BaseModel):
    baseline_id: str
    region_label: str
    region_geometry: dict
    variable: VarCode
    lead_time: LeadTime
    sample_count: int = Field(ge=1)
    period: BaselinePeriod
    stats: BaselineStats
    threshold: float | None = None
    created_at: datetime
