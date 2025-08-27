# SmartRoute - Intelligent Public Transport API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A production-ready public transport route optimization API with multi-modal routing, real-time optimization, and advanced transit features.

## 🚀 **Project Overview**

SmartRoute is a comprehensive backend system that provides intelligent routing for urban public transport networks. Built with modern Python technologies and designed with big tech engineering standards, it demonstrates advanced algorithmic thinking, scalable architecture, and production-ready implementation.

### **Key Achievements**

- 🎯 **Advanced Graph Algorithms**: Implemented modified Dijkstra with transfer state tracking
- 🚇 **Multi-Modal Routing**: Seamless integration of bus, metro, and walking
- ⚡ **High Performance**: Sub-second response times for complex route queries
- 📍 **Realistic Modeling**: Includes boarding times, transfer penalties, walking distances
- 🔧 **Production Ready**: Comprehensive testing, validation, and error handling

## 🏗️ **Architecture & Technology Stack**

### **Backend Framework**
- **FastAPI**: Modern, high-performance web framework with automatic API documentation
- **Python 3.8+**: Type hints, async/await, modern Python features
- **Pydantic**: Data validation and serialization with type safety

### **Database & Caching**
- **MongoDB**: Geospatial indexing for efficient location-based queries
- **Motor**: Async MongoDB driver for non-blocking database operations
- **In-memory Caching**: Route caching for improved performance

### **Algorithms & Libraries**
- **Modified Dijkstra**: Custom implementation with transfer state tracking
- **Geopy**: Accurate distance calculations using geodesic formulas
- **Heapq**: Priority queue for efficient graph traversal

## 🌟 **Advanced Features**

### **1. Intelligent Route Optimization**
```python
# Three optimization strategies
optimize_for = "time"      # Minimizes total journey time
optimize_for = "cost"      # Minimizes fare cost
optimize_for = "transfers" # Minimizes number of transfers
```

### **2. Realistic Transit Modeling**
- **Mode-Specific Penalties**: Different boarding times for bus (2min) vs metro (1min)
- **Transfer Handling**: Walking time between platforms + waiting time
- **Distance Validation**: Coordinates must be within service area
- **Walking Integration**: Automatic calculation of walking portions


### **3. Enhanced User Experience**
- **Route Summaries**: Human-readable journey descriptions
- **Walking Directions**: Turn-by-turn pedestrian navigation
- **Nearby Stops**: Find stops within walking distance
- **Stop Search**: Autocomplete for stop names

## 📊 **Network Coverage**

### **Comprehensive Test Data**
- **67 Transit Stops** across Bangalore metropolitan area
- **12 Routes** including 2 metro lines and 10 bus routes
- **Multi-Modal Network** with realistic transfer points
- **Geographic Coverage** from tech hubs to residential areas

### **Realistic Route Types**
- 🚇 **Metro Lines**: Red Line (North-South), Purple Line (East-West)
- 🚌 **Express Routes**: High-speed inter-zone connectivity
- 🚐 **Local Routes**: Neighborhood feeder services
- 🏢 **Tech Shuttles**: Corporate campus connections

## 🔧 **Coding Standards**

### **Code Quality**
- **Type Safety**: Full type annotations with mypy compatibility
- **Clean Architecture**: Separation of concerns with service layers
- **Error Handling**: Comprehensive validation and proper HTTP status codes
- **Documentation**: Detailed API docs and inline code documentation

### **Performance & Scalability**
- **Async Operations**: Non-blocking I/O for high concurrency
- **Database Optimization**: Geospatial indexing and query optimization
- **Caching Strategy**: Intelligent route caching with TTL
- **Resource Management**: Proper connection pooling and cleanup

### **Testing & Reliability**
- **Comprehensive Test Suite**: Unit, integration, and performance tests
- **Edge Case Handling**: Validation for invalid inputs and edge conditions
- **Stress Testing**: Concurrent request handling and load testing
- **Error Recovery**: Graceful failure handling and logging

## 🚀 **Quick Start**

### **Prerequisites**
```bash
- Python 3.8+
- MongoDB 6.0+
- pip or poetry for dependency management
```

### **Installation**
```bash
# Clone the repository
git clone https://github.com/Prachi-gurav390/Smart_route_backend.git
cd smartroute-backend

# Install dependencies
pip install -r requirements.txt

# Load comprehensive test data
python scripts/load_comprehensive_data.py

# Start the server
python app/main.py
```

### **API Usage**
```bash
# Find route between coordinates
curl -X POST "http://localhost:8000/api/v1/route" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 12.9716, "lon": 77.5946},
    "end": {"lat": 12.9759, "lon": 77.6081},
    "optimize_for": "time"
  }'

# Find nearby stops
curl "http://localhost:8000/api/v1/stops/nearby?lat=12.9759&lon=77.6081"

# Search stops by name
curl "http://localhost:8000/api/v1/stops/search?q=MG Road"
```

## 📈 **Performance Benchmarks**

| Metric | Target | Achieved |
|--------|--------|----------|
| Response Time | < 1s | ~200ms |
| Concurrent Users | 10+ | ✅ Tested |
| Success Rate | > 95% | > 98% |
| Error Handling | Comprehensive | ✅ Complete |

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_enhanced_api.py::TestEnhancedSmartRouteAPI -v
pytest tests/test_enhanced_api.py::TestBigTechScenarios -v

# Performance testing
pytest tests/test_enhanced_api.py::TestEnhancedSmartRouteAPI::test_performance_benchmarks -v
```

### **Test Coverage**
- ✅ **API Endpoints**: All routes with success and error cases
- ✅ **Algorithm Logic**: Graph traversal and optimization algorithms
- ✅ **Edge Cases**: Invalid inputs, extreme coordinates, empty results
- ✅ **Performance**: Response times and concurrent load handling
- ✅ **Data Consistency**: Cross-endpoint data validation

## 📚 **API Documentation**

### **Interactive Documentation**
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### **Comprehensive Guide**
See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed endpoint documentation, examples, and integration guides.

## 🎯 **Resume Highlights**

This project demonstrates:

### **Technical Skills**
- **Advanced Algorithms**: Graph theory, optimization, pathfinding
- **System Design**: Scalable architecture, database design, caching
- **API Development**: RESTful design, validation, documentation
- **Python Expertise**: Async programming, type hints, modern patterns

- **Problem Solving**: Complex routing optimization with multiple constraints
- **Code Quality**: Production-ready code with comprehensive testing
- **Performance**: Sub-second response times with efficient algorithms
- **User Experience**: Intuitive API design with rich feature set

### **Production Readiness**
- **Reliability**: Comprehensive error handling and validation
- **Scalability**: Async architecture supporting concurrent users
- **Maintainability**: Clean code structure with proper documentation
- **Monitoring**: Structured logging and health check endpoints

## 🔮 **Future Enhancements**

### **Planned Features**
- 🔄 **Real-time Integration**: Live vehicle tracking and delay updates
- 🚴 **Multi-Modal**: Integration with bike sharing and ride sharing

### **Scalability Improvements**
- 📈 **Horizontal Scaling**: Microservices architecture
- 🚀 **Performance**: Graph preprocessing and advanced caching
- 🌐 **Geographic Expansion**: Support for multiple cities
- 📱 **Mobile SDK**: Native mobile app integration

