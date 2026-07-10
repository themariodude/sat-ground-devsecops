"""Application configuration via environment variables."""
import os

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_NAME = os.getenv("APP_NAME", "Satellite Ground Tracker API")
TLE_SOURCE_URL = os.getenv(
    "TLE_SOURCE_URL",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
)
TLE_FALLBACK_PATH = os.getenv("TLE_FALLBACK_PATH", "data/fallback_tle.txt")
TLE_REFRESH_SECONDS = int(os.getenv("TLE_REFRESH_SECONDS", "3600"))
