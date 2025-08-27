#!/usr/bin/env python3
"""
Comprehensive test suite for SmartRoute pathfinding algorithm
"""
import asyncio
import sys
import os
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.graph_service import graph_service

async def test_all_routing_scenarios():
    """Test various routing scenarios comprehensively"""
    print("Loading graph data...")
    await graph_service.load_graph_data()
    
    stops = list(graph_service.stops_cache.keys())
    print(f"Loaded {len(stops)} stops and {len(graph_service.routes_cache)} routes")
    
    # Test cases: (start, end, description)
    test_cases = [
        ("B012", "B030", "Original failing case"),
        ("M001", "M010", "Metro to Metro"),
        ("B001", "B020", "Bus to Bus"),
        ("P001", "P010", "Platform to Platform"),
        ("T001", "T005", "Terminal to Terminal"),
        ("B001", "M001", "Bus to Metro transfer"),
        ("M001", "P001", "Metro to Platform transfer"),
        ("P001", "T001", "Platform to Terminal transfer"),
    ]
    
    # Add some random test cases
    for i in range(10):
        start = random.choice(stops)
        end = random.choice(stops)
        if start != end:
            test_cases.append((start, end, f"Random test {i+1}"))
    
    results = {"success": 0, "failed": 0, "details": []}
    
    for start, end, description in test_cases:
        print(f"\nTesting: {description} ({start} to {end})")
        
        try:
            # Test all optimization criteria
            for optimize_for in ["time", "cost", "transfers"]:
                route = await graph_service._dijkstra_with_transfers(start, end, optimize_for)
                
                if route:
                    print(f"  ✓ {optimize_for}: Found path with {len(route.path)} stops, {route.transfers} transfers, {route.total_time}min")
                    results["success"] += 1
                    results["details"].append({
                        "start": start, "end": end, "optimize_for": optimize_for,
                        "success": True, "path_length": len(route.path),
                        "transfers": route.transfers, "time": route.total_time
                    })
                else:
                    print(f"  ✗ {optimize_for}: No route found")
                    results["failed"] += 1
                    results["details"].append({
                        "start": start, "end": end, "optimize_for": optimize_for,
                        "success": False
                    })
        except Exception as e:
            print(f"  ERROR: {e}")
            results["failed"] += 1
    
    print(f"\n{'='*60}")
    print(f"TEST RESULTS: {results['success']} successful, {results['failed']} failed")
    print(f"Success rate: {results['success']/(results['success']+results['failed'])*100:.1f}%")
    
    # Analyze failed cases
    failed_cases = [d for d in results["details"] if not d["success"]]
    if failed_cases:
        print(f"\nFAILED CASES ({len(failed_cases)}):")
        for case in failed_cases:
            print(f"  {case['start']} to {case['end']} (optimize: {case['optimize_for']})")
    
    return results

async def test_edge_cases():
    """Test edge cases and error conditions"""
    print(f"\n{'='*60}")
    print("TESTING EDGE CASES")
    print(f"{'='*60}")
    
    # Test same start/end
    print("\n1. Same start and end stop:")
    route = await graph_service._dijkstra_with_transfers("B001", "B001", "time")
    if route:
        print("  ✓ Route found (should be empty path)")
        print(f"    Path: {route.path}")
    else:
        print("  ✗ No route found (expected)")
    
    # Test non-existent stops
    print("\n2. Non-existent stops:")
    route = await graph_service._dijkstra_with_transfers("NONEXISTENT1", "NONEXISTENT2", "time")
    print(f"  Route result: {route is not None}")
    
    # Test isolated stops (if any)
    print("\n3. Testing connectivity:")
    stops = list(graph_service.stops_cache.keys())
    isolated_stops = []
    for stop_id in stops[:10]:  # Test first 10 stops
        stop = graph_service.stops_cache[stop_id]
        if len(stop.connections) == 0:
            isolated_stops.append(stop_id)
    
    if isolated_stops:
        print(f"  Found {len(isolated_stops)} isolated stops: {isolated_stops}")
    else:
        print("  No isolated stops found in sample")
    
    # Test maximum transfers
    print("\n4. Testing maximum transfers limit:")
    route = await graph_service._dijkstra_pathfinding("B001", "M010", "transfers", max_transfers=0)
    if route:
        print(f"  ✓ Route found with 0 transfers allowed: {route.transfers} transfers")
    else:
        print("  ✗ No route found with 0 transfers allowed")

async def test_performance():
    """Test performance with different graph sizes"""
    print(f"\n{'='*60}")
    print("PERFORMANCE TESTING")
    print(f"{'='*60}")
    
    import time
    
    stops = list(graph_service.stops_cache.keys())
    
    # Test performance with different distances
    test_pairs = [
        (stops[0], stops[1]),   # Close stops
        (stops[0], stops[len(stops)//2]),  # Medium distance
        (stops[0], stops[-1]),  # Far stops
    ]
    
    for i, (start, end) in enumerate(test_pairs):
        print(f"\nTest {i+1}: {start} to {end}")
        
        start_time = time.time()
        route = await graph_service._dijkstra_with_transfers(start, end, "time")
        end_time = time.time()
        
        if route:
            print(f"  ✓ Found route in {end_time - start_time:.3f} seconds")
            print(f"    Path length: {len(route.path)} stops")
            print(f"    Transfers: {route.transfers}")
        else:
            print(f"  ✗ No route found in {end_time - start_time:.3f} seconds")

async def test_algorithm_consistency():
    """Test that algorithm gives consistent results"""
    print(f"\n{'='*60}")
    print("CONSISTENCY TESTING")
    print(f"{'='*60}")
    
    # Test same route multiple times
    test_cases = [("B012", "B030"), ("M001", "M005"), ("P001", "T001")]
    
    for start, end in test_cases:
        print(f"\nTesting consistency: {start} to {end}")
        routes = []
        
        for i in range(3):  # Run 3 times
            route = await graph_service._dijkstra_with_transfers(start, end, "time")
            if route:
                routes.append((route.path, route.total_time, route.transfers))
            else:
                routes.append(None)
        
        # Check if all results are the same
        if all(r == routes[0] for r in routes):
            print("  ✓ Consistent results across multiple runs")
            if routes[0]:
                path, time, transfers = routes[0]
                print(f"    Path: {' to '.join(path)}")
                print(f"    Time: {time}min, Transfers: {transfers}")
        else:
            print("  ✗ Inconsistent results!")
            for i, route in enumerate(routes):
                if route:
                    path, time, transfers = route
                    print(f"    Run {i+1}: {' to '.join(path)} ({time}min, {transfers} transfers)")
                else:
                    print(f"    Run {i+1}: No route found")

if __name__ == "__main__":
    asyncio.run(test_all_routing_scenarios())
    asyncio.run(test_edge_cases())
    asyncio.run(test_performance())
    asyncio.run(test_algorithm_consistency())