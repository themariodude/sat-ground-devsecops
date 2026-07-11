"""Satellite Ground Tracker API — DevSecOps Demo."""
import logging
from typing import List

from fastapi import FastAPI, HTTPException

from app.config import APP_NAME, APP_VERSION
from app.models.schemas import (
    ErrorResponse,
    HealthResponse,
    SatelliteHealth,
    SatelliteInfo,
    SatellitePosition,
)
from app.services.tle_service import (
    get_all_satellites,
    get_cache_age_hours,
    get_data_source,
    refresh_tle_data,
)
from app.services.position_service import calculate_position

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "A DevSecOps demo API that tracks real satellite positions "
        "using public TLE orbital data. Built to demonstrate CI/CD, "
        "automated testing, security scanning, and containerized "
        "deployment for satellite ground-system style applications."
    ),
)


@app.on_event("startup")
async def startup_load_tle() -> None:
    """Pre-load TLE data on startup."""
    logger.info("Loading initial TLE data...")
    refresh_tle_data(force=True)
    logger.info("Data source: %s", get_data_source())


@app.get("/health", response_model=HealthResponse, tags=["Operations"])
async def health_check():
    """Service health, version, and data source status."""
    sats = get_all_satellites()
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        data_source=get_data_source(),
        satellites_loaded=len(sats),
    )


@app.get(
    "/satellites",
    response_model=List[SatelliteInfo],
    tags=["Satellites"],
)
async def list_satellites():
    """List all tracked satellites with basic metadata."""
    sats = get_all_satellites()
    source = get_data_source()
    return [
        SatelliteInfo(name=name, norad_id=norad_id, data_source=source)
        for name, norad_id in sats.items()
    ]


@app.get(
    "/satellites/{name}/position",
    response_model=SatellitePosition,
    responses={404: {"model": ErrorResponse}},
    tags=["Satellites"],
)
async def get_satellite_position(name: str):
    """Current approximate position of a tracked satellite."""
    sats = get_all_satellites()
    key = name.upper()

    if key not in sats:
        raise HTTPException(
            status_code=404,
            detail=f"Satellite '{name}' not found. Available: {list(sats.keys())}",
        )

    result = calculate_position(key)
    if not result:
        raise HTTPException(
            status_code=500,
            detail=f"Position calculation failed for '{key}'.",
        )

    return SatellitePosition(data_source=get_data_source(), **result)


@app.get(
    "/satellites/{name}/health",
    response_model=SatelliteHealth,
    responses={404: {"model": ErrorResponse}},
    tags=["Satellites"],
)
async def get_satellite_health(name: str):
    """Simulated operational health summary for a satellite."""
    sats = get_all_satellites()
    key = name.upper()

    if key not in sats:
        raise HTTPException(
            status_code=404,
            detail=f"Satellite '{name}' not found. Available: {list(sats.keys())}",
        )

    age = get_cache_age_hours()
    data_fresh = age is not None and age < 24.0
    position_ok = calculate_position(key) is not None

    notes = "All systems nominal." if (data_fresh and position_ok) else ""
    if not data_fresh:
        notes = "TLE data may be stale (>24h). "
    if not position_ok:
        notes += "Position calculation failed."

    return SatelliteHealth(
        name=key,
        operational=data_fresh and position_ok,
        data_fresh=data_fresh,
        tle_age_hours=round(age, 2) if age else None,
        position_calculable=position_ok,
        notes=notes.strip(),
    )
