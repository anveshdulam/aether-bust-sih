from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.common import Confidence, GridMeta, LeadTime, VarCode

SourceModel = Literal["GFS", "ECMWF", "SYNTHETIC"]
RunStatus = Literal["PENDING", "RUNNING", "COMPLETE", "FAILED"]


class ForecastRunSummary(BaseModel):
    run_id: str
    init_time: datetime
    source_model: SourceModel
    n_lead_times: int = 10
    created_at: datetime
    mean_confidence: Confidence


class ForecastRunDetail(ForecastRunSummary):
    grid: GridMeta
    variables: list[VarCode]
    norm_stats_ref: str


class ConfidenceMapResponse(BaseModel):
    run_id: str
    lead_time: LeadTime
    grid: GridMeta
    # 128x128 row-major, north-up at the API boundary (PRD 0.1), values in [0,100]
    values: list[list[Confidence]]
    stats: dict[str, float]  # {"min","max","mean","p10","p90"}
