#!/usr/bin/env python3
"""
Simple test suite for SmartRoute pathfinding algorithm
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.graph_service import graph_service

async def run_tests():
    """Run simple routing tests"""
    print("Loading graph data...")
    await graph_service.load_graph_data()
    
    stops = list(graph_service.stops_cache.keys())
    print(f"Loaded {len(stops)} stops and {len(graph_service.routes_cache)} routes")
    
    # Test the original failing case
    print(f"\nTesting B012 to B030 (original failing case):")
    route = await graph_service._dijkstra_with_transfers("B012", "B030", "time")
    if route:
        print(f"SUCCESS: Found path with {len(route.path)} stops, {route.transfers} transfers, {route.total_time}min")
        print(f"Path: {' -> '.join(route.path)}")
    else:
        print("FAILED: No route found")
    
    # Test a few more cases
    test_cases = [
        ("M001", "M005", "Metro to Metro"),
        ("B001", "B010", "Bus to Bus"), 
        ("P001", "P005", "Platform to Platform"),
        ("B001", "M001", "Bus to Metro"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for start, end, description in test_cases:
        print(f"\nTesting {description} ({start} to {end}):")
        try:
            route = await graph_service._dijkstra_with_transfers(start, end, "time")
            if route:
                print(f"SUCCESS: {len(route.path)} stops, {route.transfers} transfers, {route.total_time}min")
                success_count += 1
            else:
                print("FAILED: No route found")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\n" + "="*50)
    print(f"SUMMARY: {success_count}/{total_tests + 1} tests passed")
    
    # Test algorithm steps visualization
    print(f"\nTesting algorithm steps visualization:")
    try:
        steps = await graph_service.get_algorithm_execution_steps("B012", "B030", "time")
        print(f"Generated {len(steps)} visualization steps")
        
        # Check if destination was found
        found_destination = any(step.get('found_destination', False) for step in steps)
        if found_destination:
            print("Visualization shows destination found")
        else:
            print("Visualization did not find destination (likely hit step limit)")
            
    except Exception as e:
        print(f"Visualization test failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())