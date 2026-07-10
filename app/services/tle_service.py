"""TLE data retrieval with live fetch and local fallback."""
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx

from app.config import TLE_FALLBACK_PATH, TLE_SOURCE_URL, TLE_REFRESH_SECONDS

logger = logging.getLogger(__name__)

# Satellites we track — NORAD catalog IDs
TRACKED_SATELLITES: Dict[str, str] = {
    "ISS": "25544",
    "HUBBLE": "20580",
    "NOAA-19": "33591",
    "LANDSAT-9": "49260",
    "SENTINEL-6A": "46984",
}

# In-memory TLE cache
_tle_cache: Dict[str, Tuple[str, str]] = {}
_cache_timestamp: float = 0.0
_data_source: str = "none"


def get_data_source() -> str:
    """Return current data source label."""
    return _data_source


def _parse_tle_text(raw: str) -> Dict[str, Tuple[str, str]]:
    """Parse raw TLE text into {name: (line1, line2)} dict."""
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    parsed: Dict[str, Tuple[str, str]] = {}
    i = 0
    while i + 2 < len(lines):
        name_line = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]
        if line1.startswith("1 ") and line2.startswith("2 "):
            norad_id = line1[2:7].strip()
            for sat_name, sat_id in TRACKED_SATELLITES.items():
                if norad_id == sat_id:
                    parsed[sat_name] = (line1, line2)
            i += 3
        else:
            i += 1
    return parsed


def _fetch_live_tle() -> Optional[Dict[str, Tuple[str, str]]]:
    """Attempt to fetch TLE data from CelesTrak."""
    try:
        resp = httpx.get(TLE_SOURCE_URL, timeout=15.0)
        resp.raise_for_status()
        parsed = _parse_tle_text(resp.text)
        if parsed:
            logger.info("Fetched %d tracked satellites from CelesTrak", len(parsed))
            return parsed
    except Exception as exc:
        logger.warning("Live TLE fetch failed: %s", exc)
    return None


def _load_fallback_tle() -> Optional[Dict[str, Tuple[str, str]]]:
    """Load TLE data from local fallback file."""
    path = Path(TLE_FALLBACK_PATH)
    if not path.exists():
        logger.error("Fallback TLE file not found: %s", path)
        return None
    try:
        raw = path.read_text()
        parsed = _parse_tle_text(raw)
        if parsed:
            logger.info("Loaded %d tracked satellites from fallback", len(parsed))
            return parsed
    except Exception as exc:
        logger.warning("Fallback TLE load failed: %s", exc)
    return None


def refresh_tle_data(force: bool = False) -> None:
    """Refresh TLE cache from live source or fallback."""
    global _tle_cache, _cache_timestamp, _data_source

    if not force and (time.time() - _cache_timestamp) < TLE_REFRESH_SECONDS:
        return

    live = _fetch_live_tle()
    if live:
        _tle_cache = live
        _cache_timestamp = time.time()
        _data_source = "celestrak_live"
        return

    fallback = _load_fallback_tle()
    if fallback:
        _tle_cache = fallback
        _cache_timestamp = time.time()
        _data_source = "local_fallback"
        return

    logger.error("No TLE data available from any source")
    _data_source = "none"


def get_tle(sat_name: str) -> Optional[Tuple[str, str]]:
    """Get TLE lines for a tracked satellite."""
    refresh_tle_data()
    return _tle_cache.get(sat_name.upper())


def get_all_satellites() -> Dict[str, str]:
    """Return tracked satellites dict."""
    refresh_tle_data()
    return TRACKED_SATELLITES


def get_cache_age_hours() -> Optional[float]:
    """Return hours since last TLE cache refresh."""
    if _cache_timestamp == 0.0:
        return None
    return (time.time() - _cache_timestamp) / 3600.0
