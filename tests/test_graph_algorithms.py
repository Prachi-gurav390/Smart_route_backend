import pytest
import asyncio
from app.services.graph_service import GraphService
from app.models.stop import Stop, Connection, Location


class TestGraphAlgorithms:

    @pytest.fixture
    def mock_graph_service(self):
        """Create a mock graph service with test data"""
        service = GraphService()

        # Create test stops
        stops = {
            "S1": Stop(
                stop_id="S1",
                name="Stop 1",
                location=Location(coordinates=[77.5946, 12.9716]),
                connections=[
                    Connection(to_stop_id="S2", route_id="R1",
                               time=10, cost=2.0, sequence=1),
                    Connection(to_stop_id="S3", route_id="R2",
                               time=15, cost=3.0, sequence=1)
                ]
            ),
            "S2": Stop(
                stop_id="S2",
                name="Stop 2",
                location=Location(coordinates=[77.6081, 12.9759]),
                connections=[
                    Connection(to_stop_id="S3", route_id="R1",
                               time=8, cost=1.5, sequence=2),
                    Connection(to_stop_id="S4", route_id="R3",
                               time=12, cost=2.5, sequence=1)
                ]
            ),
            "S3": Stop(
                stop_id="S3",
                name="Stop 3",
                location=Location(coordinates=[77.6108, 12.9718]),
                connections=[
                    Connection(to_stop_id="S4", route_id="R2",
                               time=6, cost=1.0, sequence=2)
                ]
            ),
            "S4": Stop(
                stop_id="S4",
                name="Stop 4",
                location=Location(coordinates=[77.6097, 12.9833]),
                connections=[]
            )
        }

        service.stops_cache = stops
        service.routes_cache = {
            "R1": {"route_id": "R1", "name": "Route 1"},
            "R2": {"route_id": "R2", "name": "Route 2"},
            "R3": {"route_id": "R3", "name": "Route 3"}
        }

        return service

    @pytest.mark.asyncio
    async def test_shortest_path_by_time(self, mock_graph_service):
        """Test finding shortest path optimized for time"""
        route = await mock_graph_service._dijkstra_with_transfers("S1", "S4", "time")

        assert route is not None
        assert route.path[0] == "S1"
        assert route.path[-1] == "S4"
        assert route.total_time > 0
        assert len(route.segments) > 0

    @pytest.mark.asyncio
    async def test_shortest_path_by_cost(self, mock_graph_service):
        """Test finding shortest path optimized for cost"""
        route = await mock_graph_service._dijkstra_with_transfers("S1", "S4", "cost")

        assert route is not None
        assert route.total_cost > 0
        assert route.path[0] == "S1"
        assert route.path[-1] == "S4"

    @pytest.mark.asyncio
    async def test_transfer_penalty(self, mock_graph_service):
        """Test that transfers are penalized correctly"""
        route = await mock_graph_service._dijkstra_with_transfers("S1", "S4", "time")

        # Check if transfers are counted
        assert route.transfers >= 0

        # Route with transfers should have higher cost than direct route
        # (if direct route existed)

    def test_nearest_stops(self, mock_graph_service):
        """Test finding nearest stops to coordinates"""
        # Test coordinates near Stop 1
        nearest = mock_graph_service.find_nearest_stops(12.9716, 77.5946, 2)

        assert len(nearest) <= 2
        assert "S1" in nearest

    def test_walking_time_calculation(self, mock_graph_service):
        """Test walking time calculation between stops"""
        walking_time = mock_graph_service.calculate_walking_time("S1", "S2")

        assert walking_time > 0
        # Stops should be within walking distance
        assert walking_time != float('inf')

    @pytest.mark.asyncio
    async def test_no_path_exists(self, mock_graph_service):
        """Test behavior when no path exists"""
        # Create isolated stop
        mock_graph_service.stops_cache["S5"] = Stop(
            stop_id="S5",
            name="Isolated Stop",
            location=Location(coordinates=[77.0000, 12.0000]),
            connections=[]
        )

        route = await mock_graph_service._dijkstra_with_transfers("S1", "S5", "time")
        assert route is None

    def test_coordinate_extraction(self, mock_graph_service):
        """Test extracting coordinates from stop"""
        lat, lon = mock_graph_service.get_stop_coordinates("S1")

        assert lat == 12.9716
        assert lon == 77.5946

    @pytest.mark.asyncio
    async def test_optimize_for_transfers(self, mock_graph_service):
        """Test optimization for minimum transfers"""
        route = await mock_graph_service._dijkstra_with_transfers("S1", "S4", "transfers")

        assert route is not None
        # Should prefer route with fewer transfers over faster/cheaper routes
