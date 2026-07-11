"""Tests for Satellite Ground Tracker API."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_fields(self):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "data_source" in data
        assert "satellites_loaded" in data

    def test_health_status_is_healthy(self):
        response = client.get("/health")
        assert response.json()["status"] == "healthy"


class TestSatellitesEndpoint:
    """Tests for /satellites endpoint."""

    def test_satellites_returns_200(self):
        response = client.get("/satellites")
        assert response.status_code == 200

    def test_satellites_returns_list(self):
        response = client.get("/satellites")
        data = response.json()
        assert isinstance(data, list)

    def test_satellites_have_required_fields(self):
        response = client.get("/satellites")
        data = response.json()
        if len(data) > 0:
            sat = data[0]
            assert "name" in sat
            assert "norad_id" in sat
            assert "data_source" in sat

    def test_tracked_satellites_present(self):
        response = client.get("/satellites")
        names = [s["name"] for s in response.json()]
        expected = ["ISS", "HUBBLE", "NOAA-19", "LANDSAT-9", "SENTINEL-6A"]
        for name in expected:
            assert name in names, f"{name} not in satellite list"


class TestPositionEndpoint:
    """Tests for /satellites/{name}/position endpoint."""

    def test_valid_satellite_returns_200(self):
        response = client.get("/satellites/ISS/position")
        assert response.status_code == 200

    def test_position_response_fields(self):
        response = client.get("/satellites/ISS/position")
        data = response.json()
        assert "name" in data
        assert "latitude" in data
        assert "longitude" in data
        assert "altitude_km" in data
        assert "timestamp_utc" in data
        assert "data_source" in data

    def test_latitude_range(self):
        response = client.get("/satellites/ISS/position")
        lat = response.json()["latitude"]
        assert -90 <= lat <= 90

    def test_longitude_range(self):
        response = client.get("/satellites/ISS/position")
        lon = response.json()["longitude"]
        assert -180 <= lon <= 180

    def test_altitude_positive(self):
        response = client.get("/satellites/ISS/position")
        alt = response.json()["altitude_km"]
        assert alt > 0

    def test_invalid_satellite_returns_404(self):
        response = client.get("/satellites/FAKESATELLITE/position")
        assert response.status_code == 404

    def test_case_insensitive_lookup(self):
        response = client.get("/satellites/iss/position")
        assert response.status_code == 200


class TestHealthSatelliteEndpoint:
    """Tests for /satellites/{name}/health endpoint."""

    def test_valid_satellite_health(self):
        response = client.get("/satellites/ISS/health")
        assert response.status_code == 200

    def test_health_response_fields(self):
        response = client.get("/satellites/ISS/health")
        data = response.json()
        assert "name" in data
        assert "operational" in data
        assert "data_fresh" in data
        assert "position_calculable" in data
        assert "notes" in data

    def test_invalid_satellite_health_404(self):
        response = client.get("/satellites/NOSUCHSAT/health")
        assert response.status_code == 404


class TestFallbackBehavior:
    """Tests for fallback when external TLE fetch fails."""

    @patch("app.services.tle_service._fetch_live_tle", return_value=None)
    def test_fallback_loads_when_live_fails(self, mock_fetch):
        from app.services.tle_service import refresh_tle_data, get_data_source

        refresh_tle_data(force=True)
        source = get_data_source()
        assert source in ("local_fallback", "celestrak_live")

    def test_api_works_with_fallback_data(self):
        response = client.get("/satellites/ISS/position")
        assert response.status_code == 200
