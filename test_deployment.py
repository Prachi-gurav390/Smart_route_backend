#!/usr/bin/env python3
"""
Test the deployed SmartRoute API
"""
import asyncio
import aiohttp
import json
import sys

async def test_api(base_url):
    """Test the deployed API endpoints"""
    
    print(f"Testing API at: {base_url}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Check
        print("1. Testing health check...")
        try:
            async with session.get(f"{base_url}/api/v1/health", timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✓ Health check passed: {data}")
                else:
                    print(f"   ✗ Health check failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"   ✗ Health check error: {e}")
            return False
        
        # Test 2: Graph Nodes
        print("\n2. Testing graph nodes endpoint...")
        try:
            async with session.get(f"{base_url}/api/v1/graph/nodes", timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    node_count = len(data.get('nodes', []))
                    print(f"   ✓ Graph nodes loaded: {node_count} nodes")
                else:
                    print(f"   ✗ Graph nodes failed: {resp.status}")
        except Exception as e:
            print(f"   ⚠ Graph nodes error: {e}")
        
        # Test 3: Route Finding
        print("\n3. Testing route finding...")
        try:
            route_request = {
                "start_stop_id": "B012",
                "end_stop_id": "B030",
                "optimize_for": "time"
            }
            async with session.post(
                f"{base_url}/api/v1/route/stops",
                json=route_request,
                timeout=60
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    path_length = len(data.get('path', []))
                    transfers = data.get('transfers', 0)
                    total_time = data.get('total_time', 0)
                    print(f"   ✓ Route found: {path_length} stops, {transfers} transfers, {total_time}min")
                elif resp.status == 404:
                    print(f"   ✓ No route found (expected for some pairs)")
                else:
                    print(f"   ✗ Route finding failed: {resp.status}")
                    error_text = await resp.text()
                    print(f"     Error: {error_text}")
        except Exception as e:
            print(f"   ⚠ Route finding error: {e}")
        
        # Test 4: Algorithm Steps
        print("\n4. Testing algorithm visualization...")
        try:
            algo_request = {
                "start_stop_id": "B012", 
                "end_stop_id": "B030",
                "optimize_for": "time"
            }
            async with session.post(
                f"{base_url}/api/v1/graph/algorithm-steps",
                json=algo_request,
                timeout=60
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    steps_count = len(data.get('steps', []))
                    print(f"   ✓ Algorithm steps: {steps_count} steps generated")
                else:
                    print(f"   ⚠ Algorithm steps failed: {resp.status}")
        except Exception as e:
            print(f"   ⚠ Algorithm steps error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")
    print("\nIf you see ✓ marks above, your deployment is working correctly.")
    print("You can now connect your frontend to this API.")
    
    return True

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_deployment.py <API_URL>")
        print("Example: python test_deployment.py https://your-app.onrender.com")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    await test_api(api_url)

if __name__ == "__main__":
    asyncio.run(main())