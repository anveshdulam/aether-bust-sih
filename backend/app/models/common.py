from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.constants import (
    DELTA,
    H,
    LAMBDA_MAX,
    LAMBDA_MIN,
    PHI_MAX,
    PHI_MIN,
    W,
)

VarCode = Literal["t2m", "tp", "z500", "ws850"]
LayerCode = Literal["confidence", "p_bust", "error"]
ExportFormat = Literal["geojson", "geotiff", "netcdf"]

Latitude = Annotated[float, Field(ge=PHI_MIN, le=PHI_MAX)]
Longitude = Annotated[float, Field(ge=LAMBDA_MIN, le=LAMBDA_MAX)]
LeadTime = Annotated[int, Field(ge=1, le=10)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
Confidence = Annotated[float, Field(ge=0.0, le=100.0)]

# [lon_min, lat_min, lon_max, lat_max] -- GeoJSON axis order (RFC 7946)
BBox = tuple[Longitude, Latitude, Longitude, Latitude]

CHANNEL_NAMES: dict[str, str] = {
    "t2m": "2 m Temperature",
    "tp": "Total Precipitation (24h)",
    "z500": "500 hPa Geopotential Height",
    "u850": "850 hPa Zonal Wind",
    "v850": "850 hPa Meridional Wind",
    "ws850": "850 hPa Wind Speed",
    "cape": "Convective Available Potential Energy",
    "mslp": "Mean Sea Level Pressure",
    "z500_anom": "500 hPa Geopotential Height Anomaly",
    "shear_850_250": "Deep-layer bulk wind shear (250-850hPa)",
}

VAR_NAMES: dict[str, str] = {
    "t2m": "2 m Temperature",
    "tp": "Total Precipitation",
    "z500": "500 hPa Geopotential Height",
    "ws850": "850 hPa Wind Speed",
}

VAR_UNITS: dict[str, str] = {"t2m": "K", "tp": "mm", "z500": "gpm", "ws850": "m s-1"}

VAR_STANDARD_NAMES: dict[str, str] = {
    "t2m": "air_temperature",
    "tp": "precipitation_amount",
    "z500": "geopotential_height",
    "ws850": "wind_speed",
}


class GridMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat_min: float = PHI_MIN
    lat_max: float = PHI_MAX
    lon_min: float = LAMBDA_MIN
    lon_max: float = LAMBDA_MAX
    resolution: float = DELTA
    n_rows: int = H
    n_cols: int = W


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: Annotated[int, Field(ge=1, le=500)] = 50
    offset: Annotated[int, Field(ge=0)] = 0


class Problem(BaseModel):
    """RFC 9457 Problem Details (TRD 5.1)."""

    model_config = ConfigDict(extra="forbid")

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
