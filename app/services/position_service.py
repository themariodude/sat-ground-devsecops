"""Satellite position calculation using sgp4."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

from sgp4.api import Satrec, WGS72
from sgp4.api import jday

from app.services.tle_service import get_tle

logger = logging.getLogger(__name__)


def _ecef_to_latlon(x: float, y: float, z: float) -> Dict[str, float]:
    """Convert TEME position (km) to approximate lat/lon/alt."""
    import math

    r = math.sqrt(x**2 + y**2 + z**2)
    lat = math.degrees(math.asin(z / r)) if r > 0 else 0.0
    lon = math.degrees(math.atan2(y, x))
    earth_radius_km = 6371.0
    alt = r - earth_radius_km

    return {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "altitude_km": round(alt, 2),
    }


def calculate_position(sat_name: str) -> Optional[Dict]:
    """Calculate current position for a tracked satellite."""
    tle = get_tle(sat_name)
    if not tle:
        return None

    line1, line2 = tle
    try:
        satellite = Satrec.twoline2rv(line1, line2, WGS72)
    except Exception as exc:
        logger.error("Failed to parse TLE for %s: %s", sat_name, exc)
        return None

    now = datetime.now(timezone.utc)
    jd, fr = jday(
        now.year, now.month, now.day, now.hour, now.minute, now.second
    )

    error_code, position, velocity = satellite.sgp4(jd, fr)
    if error_code != 0:
        logger.error(
            "SGP4 propagation error %d for %s", error_code, sat_name
        )
        return None

    x, y, z = position
    coords = _ecef_to_latlon(x, y, z)

    return {
        "name": sat_name.upper(),
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "altitude_km": coords["altitude_km"],
        "timestamp_utc": now.isoformat(),
    }
