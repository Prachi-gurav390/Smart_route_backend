#!/usr/bin/env python3
"""
Test script to verify the B012 -> B030 routing fix
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.graph_service import graph_service

async def test_b012_to_b030():
    """Test the specific B012 to B030 routing issue"""
    print("Loading graph data...")
    await graph_service.load_graph_data()
    
    print(f"Loaded {len(graph_service.stops_cache)} stops and {len(graph_service.routes_cache)} routes")
    
    # Check if both stops exist
    if 'B012' not in graph_service.stops_cache:
        print("ERROR: B012 stop not found!")
        return
        
    if 'B030' not in graph_service.stops_cache:
        print("ERROR: B030 stop not found!")
        return
    
    print("Both stops found. Testing routing...")
    
    # Test the actual routing
    route = await graph_service._dijkstra_with_transfers('B012', 'B030', 'time')
    
    if route:
        print("SUCCESS: Route found!")
        print(f"Path: {' -> '.join(route.path)}")
        print(f"Segments: {len(route.segments)}")
        print(f"Transfers: {route.transfers}")
        print(f"Total time: {route.total_time} minutes")
        print(f"Total cost: {route.total_cost}")
        
        print("\nDetailed segments:")
        for i, segment in enumerate(route.segments):
            print(f"  {i+1}. {segment.from_stop} to {segment.to_stop} via {segment.route_name} ({segment.time}min, ${segment.cost})")
    else:
        print("FAILED: No route found")
        
        # Let's check connections from B012
        b012_stop = graph_service.stops_cache['B012']
        print(f"\nB012 connections ({len(b012_stop.connections)}):")
        for conn in b012_stop.connections:
            print(f"  to {conn.to_stop_id} via {conn.route_id} ({conn.time}min, ${conn.cost})")
            
        # Let's check connections to B030
        print(f"\nConnections TO B030:")
        count = 0
        for stop_id, stop in graph_service.stops_cache.items():
            for conn in stop.connections:
                if conn.to_stop_id == 'B030':
                    print(f"  {stop_id} to B030 via {conn.route_id} ({conn.time}min, ${conn.cost})")
                    count += 1
        print(f"Total connections to B030: {count}")

async def test_algorithm_steps():
    """Test algorithm steps visualization"""
    print("\n" + "="*50)
    print("TESTING ALGORITHM STEPS VISUALIZATION")
    print("="*50)
    
    steps = await graph_service.get_algorithm_execution_steps('B012', 'B030', 'time')
    
    print(f"Algorithm executed {len(steps)} steps")
    
    # Show first few and last few steps
    for i, step in enumerate(steps[:5]):
        print(f"Step {step['step']}: {step['action']} - {step['description']}")
        if 'current_node' in step:
            print(f"  Current node: {step['current_node']}")
        if 'path' in step and len(step['path']) > 1:
            print(f"  Path: {' to '.join(step['path'])}")
        print()
    
    if len(steps) > 10:
        print("...")
        for i, step in enumerate(steps[-3:]):
            print(f"Step {step['step']}: {step['action']} - {step['description']}")
            if 'current_node' in step:
                print(f"  Current node: {step['current_node']}")
            if 'path' in step and len(step['path']) > 1:
                print(f"  Path: {' to '.join(step['path'])}")
            print()
    
    # Check if destination was found
    found_destination = any(step.get('found_destination', False) for step in steps)
    print(f"Destination found in visualization: {found_destination}")

if __name__ == "__main__":
    asyncio.run(test_b012_to_b030())
    asyncio.run(test_algorithm_steps())