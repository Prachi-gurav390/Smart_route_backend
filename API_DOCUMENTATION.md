# SmartRoute API Documentation

## Overview

SmartRoute is a comprehensive public transport route optimization API designed for multi-modal urban transit systems. It provides intelligent routing, real-time optimization, and enhanced features suitable for production-grade applications.

### Key Features

- **Multi-Modal Routing**: Supports bus, metro, and walking combinations
- **Multiple Optimization Criteria**: Time, cost, and transfer minimization
- **Realistic Transit Modeling**: Includes boarding times, transfer penalties, and mode-specific delays
- **Environmental Impact**: CO2 savings and calorie calculations
- **Walking Directions**: Detailed pedestrian navigation
- **Comprehensive Validation**: Input validation and proper error handling
- **High Performance**: Sub-second response times for complex queries

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. This would be added in production deployments.

## Endpoints

### 1. Route Finding (Coordinate-based)

Find optimal routes between two geographic coordinates.

```http
POST /route
```

#### Request Body

```json
{
  "start": {
    "lat": 12.9716,
    "lon": 77.5946
  },
  "end": {
    "lat": 12.9759,
    "lon": 77.6081
  },
  "optimize_for": "time"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start.lat` | float | Yes | Start latitude (-90 to 90) |
| `start.lon` | float | Yes | Start longitude (-180 to 180) |
| `end.lat` | float | Yes | End latitude (-90 to 90) |
| `end.lon` | float | Yes | End longitude (-180 to 180) |
| `optimize_for` | string | No | Optimization criteria: "time" (default), "cost", "transfers" |

#### Response

```json
{
  "path": ["S001", "S002"],
  "segments": [
    {
      "route_id": "METRO_RED",
      "route_name": "Metro Red Line - Baiyappanahalli to Mysuru Road",
      "route_type": "metro",
      "from_stop": "S001",
      "to_stop": "S002", 
      "from_stop_name": "Central Station",
      "to_stop_name": "MG Road",
      "time": 7,
      "cost": 15.0,
      "sequence_start": 1,
      "sequence_end": 2,
      "boarding_time": 1,
      "transfer_time": 0,
      "walking_directions": []
    }
  ],
  "total_time": 12,
  "total_cost": 15.0,
  "transfers": 0,
  "walking_time": 5,
  "total_distance_km": 0.45,
  "start_walking_time": 3,
  "end_walking_time": 2,
  "route_summary": "Walk 3min to Central Station → Take metro METRO_RED for 1 stops → Walk 2min to destination",
  "alternative_routes_count": 0,
  "co2_saved_kg": 0.95,
  "calories_burned": 20
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `path` | array | Ordered list of stop IDs in the route |
| `segments` | array | Detailed route segments |
| `total_time` | integer | Total journey time in minutes |
| `total_cost` | float | Total fare cost |
| `transfers` | integer | Number of transfers required |
| `walking_time` | integer | Total walking time in minutes |
| `total_distance_km` | float | Total walking distance in kilometers |
| `route_summary` | string | Human-readable route description |
| `co2_saved_kg` | float | CO2 saved vs private car (kg) |
| `calories_burned` | integer | Calories burned from walking |

### 2. Route Finding (Stop-based)

Find optimal routes between specific transit stops.

```http
POST /route/stops
```

#### Request Body

```json
{
  "start_stop_id": "M006",
  "end_stop_id": "M010",
  "optimize_for": "time"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_stop_id` | string | Yes | Starting stop ID |
| `end_stop_id` | string | Yes | Destination stop ID |
| `optimize_for` | string | No | Optimization criteria: "time" (default), "cost", "transfers" |

#### Response

Same structure as coordinate-based routing, but without walking portions.

### 3. Nearby Stops Search

Find transit stops near given coordinates.

```http
GET /stops/nearby?lat=12.9759&lon=77.6081&limit=10
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | float | Yes | Latitude (-90 to 90) |
| `lon` | float | Yes | Longitude (-180 to 180) |
| `limit` | integer | No | Maximum results (default: 10, max: 50) |

#### Response

```json
{
  "nearby_stops": [
    {
      "stop_id": "M006",
      "name": "MG Road",
      "latitude": 12.9759,
      "longitude": 77.6081,
      "distance_km": 0.045,
      "walking_time_minutes": 1
    }
  ]
}
```

### 4. Stop Name Search

Search for stops by name with autocomplete functionality.

```http
GET /stops/search?q=MG Road&limit=10
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `limit` | integer | No | Maximum results (default: 10, max: 50) |

#### Response

```json
{
  "suggestions": [
    {
      "stop_id": "M006",
      "name": "MG Road",
      "latitude": 12.9759,
      "longitude": 77.6081
    }
  ]
}
```

### 5. Health Check

Check API health and status.

```http
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "service": "SmartRoute API"
}
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages.

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid start coordinates. Latitude must be between -90 and 90, longitude between -180 and 180"
}
```

#### 404 Not Found
```json
{
  "detail": "No route found. Check if coordinates are within service area and walking distance limits."
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "float_parsing",
      "loc": ["query", "lat"],
      "msg": "Input should be a valid number",
      "input": "invalid"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred while finding route"
}
```

## Optimization Algorithms

### Dijkstra with Transfers

The core routing algorithm uses a modified Dijkstra's algorithm that:

- **State Tracking**: Maintains (stop_id, route_id) state to handle transfers correctly
- **Mode-Specific Penalties**: Applies different boarding and transfer times for bus vs metro
- **Transfer Optimization**: Minimizes transfers while considering time and cost
- **Walking Integration**: Calculates walking time to/from nearest stops

### Optimization Criteria

1. **Time Optimization** (default)
   - Minimizes total journey time including walking, waiting, and transfers
   - Applies transfer penalties: 5min base + 3min walking + 5min waiting
   - Includes mode-specific boarding times

2. **Cost Optimization**
   - Minimizes total fare cost
   - Applies monetary transfer penalties
   - Considers different fare structures for bus vs metro

3. **Transfer Optimization**
   - Minimizes number of transfers required
   - Useful for users with heavy luggage or mobility constraints
   - May result in longer journey times

## Data Model

### Network Coverage

- **67 Transit Stops** across Bangalore
- **2 Metro Lines**: Red Line (North-South), Purple Line (East-West)
- **10 Bus Routes**: Including express, local, and tech park shuttles
- **Multi-Modal Integration**: Seamless transfers between bus and metro

### Geographic Coverage

- **Central Bangalore**: MG Road, Brigade Road, Commercial Street
- **Tech Hubs**: Whitefield, Electronic City, Outer Ring Road
- **Transport Hubs**: Majestic, Central Station, major metro stations
- **Residential Areas**: Koramangala, Jayanagar, Malleswaram

## Performance Characteristics

- **Response Time**: < 1 second for most queries
- **Concurrent Users**: Supports 10+ concurrent requests
- **Data Refresh**: Real-time updates to transit network
- **Caching**: Intelligent route caching for frequent queries

## Implementation Highlights

### Big Tech Engineering Practices

1. **Scalable Architecture**
   - Async/await pattern for concurrent request handling
   - Database connection pooling and efficient queries
   - Caching layer for performance optimization

2. **Comprehensive Testing**
   - Unit tests for core algorithms
   - Integration tests for API endpoints
   - Performance benchmarks and stress testing
   - Edge case validation

3. **Production-Ready Features**
   - Structured logging and monitoring
   - Input validation and sanitization
   - Proper error handling and status codes
   - Environmental impact calculations

4. **Code Quality**
   - Type hints and Pydantic models
   - Clean architecture with service layers
   - Comprehensive documentation
   - Following Python best practices

## Examples

### Example 1: Tech Park Commute

```bash
curl -X POST "http://localhost:8000/api/v1/route" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 12.9698, "lon": 77.7500},
    "end": {"lat": 12.9769, "lon": 77.5703},
    "optimize_for": "time"
  }'
```

**Use Case**: Commuting from Whitefield tech parks to Majestic transport hub.

### Example 2: Cost-Optimized Route

```bash
curl -X POST "http://localhost:8000/api/v1/route" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 12.8456, "lon": 77.6603},
    "end": {"lat": 12.9759, "lon": 77.6081},
    "optimize_for": "cost"
  }'
```

**Use Case**: Budget-conscious travel from Electronic City to MG Road.

### Example 3: Minimal Transfers

```bash
curl -X POST "http://localhost:8000/api/v1/route" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 12.9716, "lon": 77.5946},
    "end": {"lat": 12.9698, "lon": 77.7500},
    "optimize_for": "transfers"
  }'
```

**Use Case**: Comfortable travel with minimal transfers for elderly or disabled users.

## Future Enhancements

1. **Real-time Data Integration**
   - Live vehicle tracking
   - Dynamic delay adjustments
   - Crowding information

2. **Advanced Features**
   - Accessibility routing for disabled users
   - Bike sharing integration
   - Real-time fare pricing

3. **Performance Optimizations**
   - Graph preprocessing for faster queries
   - Machine learning for delay prediction
   - Distributed caching system

## Support

For technical support or feature requests, please contact the development team or raise an issue in the project repository.

---

*This API demonstrates production-ready public transport routing suitable for large-scale urban transit systems.*