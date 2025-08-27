import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPI:

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_find_route_invalid_coordinates(self):
        """Test route finding with invalid coordinates"""
        response = client.post("/api/v1/route", json={
            "start": {"lat": "invalid", "lon": 77.5946},
            "end": {"lat": 12.9833, "lon": 77.6097},
            "optimize_for": "time"
        })
        assert response.status_code == 422  # Validation error

    def test_find_route_invalid_optimization(self):
        """Test route finding with invalid optimization parameter"""
        response = client.post("/api/v1/route", json={
            "start": {"lat": 12.9716, "lon": 77.5946},
            "end": {"lat": 12.9833, "lon": 77.6097},
            "optimize_for": "invalid"
        })
        assert response.status_code == 400

    def test_search_stops_empty_query(self):
        """Test stop search with empty query"""
        response = client.get("/api/v1/stops/search")
        assert response.status_code == 422  # Missing required parameter

    def test_search_stops_valid_query(self):
        """Test stop search with valid query"""
        response = client.get("/api/v1/stops/search?q=Central")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    def test_nearby_stops_invalid_coordinates(self):
        """Test nearby stops with invalid coordinates"""
        response = client.get("/api/v1/stops/nearby?lat=invalid&lon=77.5946")
        assert response.status_code == 422

    def test_nearby_stops_valid_coordinates(self):
        """Test nearby stops with valid coordinates"""
        response = client.get("/api/v1/stops/nearby?lat=12.9716&lon=77.5946")
        assert response.status_code == 200
        data = response.json()
        assert "nearby_stops" in data
        assert isinstance(data["nearby_stops"], list)

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
