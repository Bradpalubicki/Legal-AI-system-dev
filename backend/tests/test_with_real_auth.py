#!/usr/bin/env python
"""Test PCL API with actual authentication token from our system"""

import asyncio
import httpx
import json
import sys
sys.path.insert(0, ".")

async def main():
    # First, get a real auth token from our backend
    print("="*70)
    print("STEP 1: Getting authentication token from backend...")
    print("="*70)

    backend_url = "http://localhost:8000"

    # Authenticate
    async with httpx.AsyncClient(timeout=30.0) as client:
        auth_response = await client.post(
            f"{backend_url}/api/v1/pacer/authenticate",
            headers={"Content-Type": "application/json"},
            json={}
        )

        if not auth_response.is_success:
            print(f"❌ Auth failed: {auth_response.status_code}")
            print(auth_response.text)
            return

        print("✅ Authentication successful!")

    # Now try PCL search with different payload formats
    print("\n" + "="*70)
    print("STEP 2: Testing PCL API with authentication...")
    print("="*70)

    url = "https://pcl.uscourts.gov/pcl-public-api/rest/cases/find"

    # Test A: Remove the caseSearch wrapper
    print("\nTEST A: Flat structure at root")
    print("-"*70)
    payload_a = {
        "caseTitle": "Apple Inc",
        "courtId": "canb"
    }
    print(f"Payload: {json.dumps(payload_a, indent=2)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response_a = await client.post(
            url,
            json=payload_a,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        print(f"Status: {response_a.status_code}")
        if response_a.status_code < 300:
            print("SUCCESS!")
            print(json.dumps(response_a.json(), indent=2)[:500])
        else:
            print(f"Error: {response_a.text[:300]}")

    print("\n" + "="*70)
    print("DONE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
