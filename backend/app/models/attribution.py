from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import Latitude, LeadTime, Longitude, VarCode


class DriverAttribution(BaseModel):
    channel_code: str  # PRD 0.4 code
    channel_name: str
    score: float = Field(ge=0.0, le=1.0)  # normalized magnitude
    sign: Literal["+", "-"]


class AttributionResponse(BaseModel):
    run_id: str
    variable: VarCode
    lead_time: LeadTime
    lat: Latitude
    lon: Longitude
    drivers: list[DriverAttribution]     # length 10, sorted desc by score
    spatial_gradcam: list[list[float]]   # 128x128 in [0,1]
    narrative: str
