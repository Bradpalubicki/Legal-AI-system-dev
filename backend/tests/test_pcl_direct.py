#!/usr/bin/env python
"""
Direct PCL API Test - No Backend Involvement
Tests the PCL API directly to isolate the issue
"""

import asyncio
import httpx
import json

async def test_pcl_api():
    """Test PCL API with various header combinations"""

    url = "https://pcl.uscourts.gov/pcl-public-api/rest/cases/find"

    # Test payload - simple case search
    payload = {
        "caseSearch": {
            "caseTitle": "Apple",
            "courtId": "canb"
        },
        "page": 1,
        "pageSize": 10
    }

    print("="*70)
    print("PCL API DIRECT TEST")
    print("="*70)
    print(f"\nURL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n" + "-"*70)

    # Test 1: Minimal headers (no auth)
    print("\nTEST 1: Minimal headers (no authentication)")
    print("-"*70)
    headers1 = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    print(f"Headers: {json.dumps(headers1, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            response = await client.post(url, json=payload, headers=headers1)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            if response.status_code < 300:
                print(f"Response Body: {response.json()}")
            else:
                print(f"Error Body: {response.text[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")

    print("\n" + "-"*70)

    # Test 2: With wildcard Accept
    print("\nTEST 2: With Accept: */*")
    print("-"*70)
    headers2 = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0"
    }
    print(f"Headers: {json.dumps(headers2, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            response = await client.post(url, json=payload, headers=headers2)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            if response.status_code < 300:
                print(f"Response Body: {response.json()}")
            else:
                print(f"Error Body: {response.text[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")

    print("\n" + "-"*70)

    # Test 3: Different payload structure
    print("\nTEST 3: Simpler payload structure")
    print("-"*70)
    payload3 = {
        "caseTitle": "Apple",
        "courtId": "canb",
        "page": 1,
        "pageSize": 10
    }
    print(f"Payload: {json.dumps(payload3, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            response = await client.post(url, json=payload3, headers=headers1)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            if response.status_code < 300:
                print(f"Response Body: {response.json()}")
            else:
                print(f"Error Body: {response.text[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")

    print("\n" + "-"*70)

    # Test 4: Just check if endpoint is accessible with GET
    print("\nTEST 4: GET request to endpoint (should fail but shows accessibility)")
    print("-"*70)

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            response = await client.get(url, headers=headers1)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_pcl_api())
