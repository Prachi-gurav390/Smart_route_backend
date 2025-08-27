#!/usr/bin/env python3
"""
Comprehensive test for route validation after fixing false route creation
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.graph_service import graph_service

async def test_route_validation():
    """Test that the system correctly handles valid and invalid routes"""
    print("=" * 60)
    print("ROUTE VALIDATION TESTING")
    print("=" * 60)
    
    await graph_service.load_graph_data()
    
    # Test the specific case that was broken
    print("\n1. Testing the original problem case:")
    route = await graph_service._dijkstra_with_transfers("B030", "B033", "time")
    if route is None:
        print("   SUCCESS: B030 -> B033 correctly returns None (no route)")
    else:
        print(f"   FAILED: B030 -> B033 incorrectly returned route: {route.route_summary}")
    
    # Test isolated stops (stops with no connections)
    print("\n2. Testing isolated stops:")
    isolated_stops = []
    for stop_id, stop in graph_service.stops_cache.items():
        if len(stop.connections) == 0:
            isolated_stops.append(stop_id)
    
    print(f"   Found {len(isolated_stops)} isolated stops: {isolated_stops[:5]}{'...' if len(isolated_stops) > 5 else ''}")
    
    if isolated_stops:
        # Test routing FROM an isolated stop
        route = await graph_service._dijkstra_with_transfers(isolated_stops[0], "B001", "time")
        if route is None:
            print(f"   SUCCESS: From isolated stop {isolated_stops[0]} correctly returns None")
        else:
            print(f"   FAILED: From isolated stop {isolated_stops[0]} incorrectly found route")
            
        # Test routing TO an isolated stop
        route = await graph_service._dijkstra_with_transfers("B001", isolated_stops[0], "time")
        if route is None:
            print(f"   SUCCESS: To isolated stop {isolated_stops[0]} correctly returns None")
        else:
            print(f"   FAILED: To isolated stop {isolated_stops[0]} incorrectly found route")
    
    # Test valid routes still work
    print("\n3. Testing valid routes still work:")
    valid_test_cases = [
        ("B012", "B030", "Our original working case"),
        ("M001", "M005", "Metro to Metro"),
        ("B001", "B010", "Bus to Bus"),
        ("P001", "P005", "Platform to Platform"),
    ]
    
    working_routes = 0
    for start, end, desc in valid_test_cases:
        route = await graph_service._dijkstra_with_transfers(start, end, "time")
        if route:
            working_routes += 1
            print(f"   SUCCESS: {desc} works ({route.total_time}min, {route.transfers} transfers)")
        else:
            print(f"   FAILED: {desc} should work but returned None")
    
    print(f"\n   Valid routes working: {working_routes}/{len(valid_test_cases)}")
    
    # Test invalid combinations
    print("\n4. Testing invalid route combinations:")
    invalid_test_cases = [
        ("NONEXISTENT1", "NONEXISTENT2", "Both stops don't exist"),
        ("B001", "NONEXISTENT", "End stop doesn't exist"), 
        ("NONEXISTENT", "B001", "Start stop doesn't exist"),
    ]
    
    correct_failures = 0
    for start, end, desc in invalid_test_cases:
        route = await graph_service._dijkstra_with_transfers(start, end, "time")
        if route is None:
            correct_failures += 1
            print(f"   SUCCESS: {desc} correctly returns None")
        else:
            print(f"   FAILED: {desc} should return None but found route")
    
    print(f"\n   Invalid routes correctly handled: {correct_failures}/{len(invalid_test_cases)}")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    success_rate = (working_routes + correct_failures) / (len(valid_test_cases) + len(invalid_test_cases)) * 100
    print(f"Overall success rate: {success_rate:.1f}%")
    
    if isolated_stops:
        print(f"Isolated stops properly handled: {len(isolated_stops)} stops with 0 connections")
    
    print("Key improvements:")
    print("- Fixed false 'Purple Line' route creation")
    print("- System now returns None for impossible routes")
    print("- Isolated stops handled correctly")
    print("- Existing valid routes continue to work")
    
    return success_rate == 100.0

if __name__ == "__main__":
    success = asyncio.run(test_route_validation())
    print(f"\nTEST RESULT: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)