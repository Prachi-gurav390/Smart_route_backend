#!/usr/bin/env python3
"""
Final test specifically for the B030 -> B033 fix
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.graph_service import graph_service

async def test_b030_b033_fix():
    """Test that B030 -> B033 no longer creates false routes"""
    print("=" * 60)
    print("TESTING B030 -> B033 FIX")
    print("=" * 60)
    
    await graph_service.load_graph_data()
    
    # Test the exact case the user reported
    print("Testing B030 (Commercial Street) -> B033 (Richmond Road):")
    
    # Get the actual stop information
    b030 = graph_service.stops_cache.get('B030')
    b033 = graph_service.stops_cache.get('B033')
    
    if b030:
        print(f"  B030: {b030.name} - {len(b030.connections)} connections")
        for conn in b030.connections:
            print(f"    -> {conn.to_stop_id} via {conn.route_id}")
    
    if b033:
        print(f"  B033: {b033.name} - {len(b033.connections)} connections")
        if b033.connections:
            for conn in b033.connections:
                print(f"    -> {conn.to_stop_id} via {conn.route_id}")
        else:
            print("    (No outgoing connections)")
        
        # Check incoming connections
        incoming = []
        for stop_id, stop in graph_service.stops_cache.items():
            for conn in stop.connections:
                if conn.to_stop_id == 'B033':
                    incoming.append((stop_id, conn.route_id))
        
        if incoming:
            print(f"    Incoming connections: {len(incoming)}")
            for stop_id, route_id in incoming:
                print(f"      {stop_id} -> B033 via {route_id}")
        else:
            print(f"    (No incoming connections)")
    
    # Test route finding
    print(f"\nRoute finding result:")
    route = await graph_service._dijkstra_with_transfers("B030", "B033", "time")
    
    if route is None:
        print("  ✓ SUCCESS: No route found (correct - B033 is isolated)")
        print("  ✓ System correctly returns None instead of creating fake route")
    else:
        print("  ✗ FAILED: System still creates false route!")
        print(f"    Path: {' -> '.join(route.path)}")
        print(f"    Route summary: {route.route_summary}")
        print(f"    Segments: {len(route.segments)}")
        for segment in route.segments:
            print(f"      {segment.from_stop} -> {segment.to_stop} via {segment.route_name}")
        return False
    
    # Test the reverse direction too
    print(f"\nTesting reverse direction B033 -> B030:")
    route = await graph_service._dijkstra_with_transfers("B033", "B030", "time")
    
    if route is None:
        print("  ✓ SUCCESS: No route found (correct)")
    else:
        print("  ✗ FAILED: System creates false reverse route!")
        return False
    
    print(f"\n" + "=" * 60)
    print("CONCLUSION:")
    print("The false 'Purple Line' route issue has been COMPLETELY FIXED!")
    print("- B030 -> B033: Correctly returns None")
    print("- B033 -> B030: Correctly returns None") 
    print("- No more fake metro routes created")
    print("- Frontend will now show 'No route found' message")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_b030_b033_fix())
    if success:
        print("\n🎉 TEST PASSED: B030 -> B033 issue completely resolved!")
    else:
        print("\n❌ TEST FAILED: Issue still exists")
    sys.exit(0 if success else 1)