"""Pydantic response schemas for API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="1.0.0")
    data_source: str = Field(..., example="celestrak_live")
    satellites_loaded: int = Field(..., example=5)


class SatelliteInfo(BaseModel):
    name: str = Field(..., example="ISS (ZARYA)")
    norad_id: str = Field(..., example="25544")
    data_source: str = Field(..., example="celestrak_live")


class SatellitePosition(BaseModel):
    name: str
    latitude: float = Field(..., example=41.264)
    longitude: float = Field(..., example=-95.009)
    altitude_km: float = Field(..., example=420.5)
    timestamp_utc: str
    data_source: str


class SatelliteHealth(BaseModel):
    name: str
    operational: bool
    data_fresh: bool
    tle_age_hours: Optional[float] = None
    position_calculable: bool
    notes: str


class ErrorResponse(BaseModel):
    detail: str
