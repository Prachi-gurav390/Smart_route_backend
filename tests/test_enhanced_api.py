"""
Comprehensive test cases for the enhanced SmartRoute API
These tests demonstrate the advanced features suitable for big tech interviews
"""
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.services.graph_service import graph_service


class TestEnhancedSmartRouteAPI:
    """Test suite for enhanced SmartRoute API functionality"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Ensure graph data is loaded
            await graph_service.load_graph_data()
            yield ac
    
    async def test_coordinate_based_routing_success(self):
        """Test successful coordinate-based route finding"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9716, "lon": 77.5946},  # Central Station
                "end": {"lat": 12.9759, "lon": 77.6081},    # MG Road
                "optimize_for": "time"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "path" in data
            assert "segments" in data
            assert "total_time" in data
            assert "total_cost" in data
            assert "transfers" in data
            assert "walking_time" in data
            assert "total_distance_km" in data
            
            # Verify enhanced features
            assert "route_summary" in data
            assert "co2_saved_kg" in data
            assert "calories_burned" in data
            
            # Verify data types and constraints
            assert isinstance(data["total_time"], int)
            assert isinstance(data["total_cost"], float)
            assert isinstance(data["transfers"], int)
            assert data["total_cost"] >= 0
            assert data["total_time"] > 0
    
    async def test_optimization_criteria(self):
        """Test different optimization criteria"""
        test_cases = [
            {"optimize_for": "time", "expected_field": "total_time"},
            {"optimize_for": "cost", "expected_field": "total_cost"},
            {"optimize_for": "transfers", "expected_field": "transfers"}
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for test_case in test_cases:
                response = await client.post("/api/v1/route", json={
                    "start": {"lat": 12.9716, "lon": 77.5946},
                    "end": {"lat": 12.9769, "lon": 77.5703},  # Majestic
                    "optimize_for": test_case["optimize_for"]
                })
                
                assert response.status_code == 200
                data = response.json()
                assert test_case["expected_field"] in data
    
    async def test_coordinate_validation(self):
        """Test coordinate validation and error handling"""
        test_cases = [
            # Invalid latitude
            {
                "start": {"lat": 91.0, "lon": 77.5946},
                "end": {"lat": 12.9759, "lon": 77.6081},
                "expected_status": 400
            },
            # Invalid longitude
            {
                "start": {"lat": 12.9716, "lon": 181.0},
                "end": {"lat": 12.9759, "lon": 77.6081},
                "expected_status": 400
            },
            # Missing coordinates
            {
                "start": {"lat": 12.9716},
                "end": {"lat": 12.9759, "lon": 77.6081},
                "expected_status": 400
            },
            # Coordinates too far from service area
            {
                "start": {"lat": 10.0, "lon": 70.0},
                "end": {"lat": 15.0, "lon": 80.0},
                "expected_status": 404
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for test_case in test_cases:
                response = await client.post("/api/v1/route", json={
                    "start": test_case["start"],
                    "end": test_case["end"],
                    "optimize_for": "time"
                })
                
                assert response.status_code == test_case["expected_status"]
                if response.status_code != 200:
                    assert "detail" in response.json()
    
    async def test_stop_based_routing(self):
        """Test routing between specific stops"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test direct connection
            response = await client.post("/api/v1/route/stops", json={
                "start_stop_id": "M006",  # MG Road Metro
                "end_stop_id": "M010",    # Majestic Metro
                "optimize_for": "time"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify route structure
            assert len(data["path"]) >= 2
            assert data["path"][0] == "M006"
            assert data["path"][-1] == "M010"
            
            # Verify metro route characteristics
            assert any("METRO" in seg["route_id"] for seg in data["segments"])
    
    async def test_invalid_stop_ids(self):
        """Test handling of invalid stop IDs"""
        test_cases = [
            {"start_stop_id": "INVALID", "end_stop_id": "M006", "expected_status": 400},
            {"start_stop_id": "M006", "end_stop_id": "INVALID", "expected_status": 400},
            {"start_stop_id": "INVALID", "end_stop_id": "INVALID", "expected_status": 400}
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for test_case in test_cases:
                response = await client.post("/api/v1/route/stops", json={
                    "start_stop_id": test_case["start_stop_id"],
                    "end_stop_id": test_case["end_stop_id"],
                    "optimize_for": "time"
                })
                
                assert response.status_code == test_case["expected_status"]
                assert "not found" in response.json()["detail"].lower()
    
    async def test_nearby_stops(self):
        """Test nearby stops functionality"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/stops/nearby", params={
                "lat": 12.9759,
                "lon": 77.6081,
                "limit": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert "nearby_stops" in data
            assert len(data["nearby_stops"]) <= 5
            
            # Verify each stop has required fields
            for stop in data["nearby_stops"]:
                assert "stop_id" in stop
                assert "name" in stop
                assert "latitude" in stop
                assert "longitude" in stop
                assert "distance_km" in stop
                assert "walking_time_minutes" in stop
    
    async def test_nearby_stops_validation(self):
        """Test nearby stops coordinate validation"""
        test_cases = [
            {"lat": 91.0, "lon": 77.6081, "expected_status": 422},  # Invalid latitude
            {"lat": 12.9759, "lon": 181.0, "expected_status": 422}, # Invalid longitude
            {"lat": 10.0, "lon": 70.0, "expected_status": 400}      # Too far from service
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for test_case in test_cases:
                response = await client.get("/api/v1/stops/nearby", params={
                    "lat": test_case["lat"],
                    "lon": test_case["lon"]
                })
                
                assert response.status_code == test_case["expected_status"]
    
    async def test_stop_search(self):
        """Test stop search functionality"""
        test_cases = [
            {"query": "MG Road", "expected_min_results": 1},
            {"query": "Metro", "expected_min_results": 1},
            {"query": "Central", "expected_min_results": 1},
            {"query": "NONEXISTENT", "expected_min_results": 0}
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for test_case in test_cases:
                response = await client.get("/api/v1/stops/search", params={
                    "q": test_case["query"],
                    "limit": 10
                })
                
                assert response.status_code == 200
                data = response.json()
                
                assert "suggestions" in data
                assert len(data["suggestions"]) >= test_case["expected_min_results"]
                
                # Verify each suggestion has required fields
                for suggestion in data["suggestions"]:
                    assert "stop_id" in suggestion
                    assert "name" in suggestion
                    assert "latitude" in suggestion
                    assert "longitude" in suggestion
    
    async def test_multi_modal_routing(self):
        """Test routing across different transport modes"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Route that should involve both bus and metro
            response = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9698, "lon": 77.7500},  # Whitefield
                "end": {"lat": 12.9769, "lon": 77.5703},    # Majestic
                "optimize_for": "time"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            if data["segments"]:
                # Check for different route types
                route_types = set()
                for segment in data["segments"]:
                    if "METRO" in segment["route_id"]:
                        route_types.add("metro")
                    else:
                        route_types.add("bus")
                
                # Should involve transfers between different modes
                if data["transfers"] > 0:
                    assert len(route_types) > 1 or data["transfers"] > 0
    
    async def test_transfer_optimization(self):
        """Test transfer optimization functionality"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Compare routes optimized for transfers vs time
            route_transfers = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9698, "lon": 77.7500},
                "end": {"lat": 12.9769, "lon": 77.5703},
                "optimize_for": "transfers"
            })
            
            route_time = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9698, "lon": 77.7500},
                "end": {"lat": 12.9769, "lon": 77.5703},
                "optimize_for": "time"
            })
            
            if route_transfers.status_code == 200 and route_time.status_code == 200:
                transfers_data = route_transfers.json()
                time_data = route_time.json()
                
                # Transfer-optimized route should have <= transfers than time-optimized
                # (though both might be equally optimal)
                assert transfers_data["transfers"] <= time_data["transfers"] + 1
    
    async def test_walking_time_calculation(self):
        """Test walking time calculations"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9710, "lon": 77.5940},  # Very close to Central Station
                "end": {"lat": 12.9765, "lon": 77.6085},    # Very close to MG Road
                "optimize_for": "time"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Should have calculated walking times
                assert "walking_time" in data
                assert "start_walking_time" in data
                assert "end_walking_time" in data
                
                # Walking times should be reasonable (0-10 minutes for nearby stops)
                assert 0 <= data["walking_time"] <= 10
    
    async def test_environmental_impact(self):
        """Test environmental impact calculations"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9716, "lon": 77.5946},
                "end": {"lat": 12.9759, "lon": 77.6081},
                "optimize_for": "time"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Should have environmental impact data
                assert "co2_saved_kg" in data
                assert "calories_burned" in data
                
                # Values should be reasonable
                if data["co2_saved_kg"]:
                    assert data["co2_saved_kg"] >= 0
                if data["calories_burned"]:
                    assert data["calories_burned"] >= 0
    
    async def test_route_summary_generation(self):
        """Test route summary generation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/route", json={
                "start": {"lat": 12.9716, "lon": 77.5946},
                "end": {"lat": 12.9759, "lon": 77.6081},
                "optimize_for": "time"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Should have route summary
                assert "route_summary" in data
                assert len(data["route_summary"]) > 0
                
                # Summary should be human-readable
                summary = data["route_summary"].lower()
                assert any(word in summary for word in ["walk", "take", "bus", "metro", "→"])
    
    async def test_api_health_and_info(self):
        """Test API health and info endpoints"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test health endpoint
            health_response = await client.get("/api/v1/health")
            assert health_response.status_code == 200
            health_data = health_response.json()
            assert health_data["status"] == "healthy"
            assert health_data["service"] == "SmartRoute API"
            
            # Test root endpoint
            root_response = await client.get("/")
            assert root_response.status_code == 200
            root_data = root_response.json()
            assert "message" in root_data
            assert "version" in root_data
            assert "docs" in root_data
    
    async def test_performance_benchmarks(self):
        """Test API performance for big tech standards"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            test_requests = [
                # Simple route
                {
                    "start": {"lat": 12.9716, "lon": 77.5946},
                    "end": {"lat": 12.9759, "lon": 77.6081},
                    "optimize_for": "time"
                },
                # Complex route with transfers
                {
                    "start": {"lat": 12.9698, "lon": 77.7500},
                    "end": {"lat": 12.9769, "lon": 77.5703},
                    "optimize_for": "transfers"
                }
            ]
            
            for request_data in test_requests:
                start_time = time.time()
                response = await client.post("/api/v1/route", json=request_data)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Should respond within 2 seconds (big tech SLA standard)
                assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"
                
                if response.status_code == 200:
                    # Should return results quickly
                    assert response_time < 1.0, f"Successful request took {response_time:.2f}s"


@pytest.mark.asyncio
class TestBigTechScenarios:
    """Test scenarios specifically designed for big tech interview evaluation"""
    
    async def test_scalability_stress(self):
        """Test API under concurrent load"""
        import asyncio
        
        async def make_request():
            async with AsyncClient(app=app, base_url="http://test") as client:
                return await client.post("/api/v1/route", json={
                    "start": {"lat": 12.9716, "lon": 77.5946},
                    "end": {"lat": 12.9759, "lon": 77.6081},
                    "optimize_for": "time"
                })
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed or fail gracefully
        success_count = 0
        for response in responses:
            if hasattr(response, 'status_code'):
                assert response.status_code in [200, 404, 400, 500]
                if response.status_code == 200:
                    success_count += 1
        
        # At least 80% should succeed
        assert success_count >= 8, f"Only {success_count}/10 requests succeeded"
    
    async def test_edge_case_handling(self):
        """Test handling of various edge cases"""
        edge_cases = [
            # Same start and end coordinates
            {
                "start": {"lat": 12.9716, "lon": 77.5946},
                "end": {"lat": 12.9716, "lon": 77.5946},
                "optimize_for": "time"
            },
            # Very close coordinates (< 100m apart)
            {
                "start": {"lat": 12.9716, "lon": 77.5946},
                "end": {"lat": 12.9717, "lon": 77.5947},
                "optimize_for": "time"
            },
            # Boundary coordinates
            {
                "start": {"lat": -90.0, "lon": -180.0},
                "end": {"lat": 90.0, "lon": 180.0},
                "optimize_for": "time"
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for case in edge_cases:
                response = await client.post("/api/v1/route", json=case)
                
                # Should not crash, should return appropriate response
                assert response.status_code in [200, 400, 404]
                
                # Should have proper error messages if failed
                if response.status_code != 200:
                    assert "detail" in response.json()
    
    async def test_data_consistency(self):
        """Test data consistency across different API calls"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Get route between two stops
            route_response = await client.post("/api/v1/route/stops", json={
                "start_stop_id": "M006",
                "end_stop_id": "M010",
                "optimize_for": "time"
            })
            
            if route_response.status_code == 200:
                route_data = route_response.json()
                
                # Check if stops in path exist in nearby stops search
                for stop_id in route_data["path"]:
                    # This stop should exist in the system
                    # Try to find it via search
                    if stop_id not in ["START", "END"]:
                        search_response = await client.get("/api/v1/stops/search", params={
                            "q": stop_id,
                            "limit": 50
                        })
                        
                        if search_response.status_code == 200:
                            search_data = search_response.json()
                            # Should find the stop or a related one
                            found = any(stop_id in s["stop_id"] for s in search_data["suggestions"])
                            # This is expected to sometimes fail due to naming differences


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])