#!/usr/bin/env python
"""Test the corrected PCL API format"""

import asyncio
import httpx
import json

async def test():
    url = "https://pcl.uscourts.gov/pcl-public-api/rest/cases/find"

    # CORRECTED FORMAT: Put search criteria at root level
    payload = {
        "caseTitle": "Apple",
        "courtId": "canb",
        "page": 1,
        "pageSize": 10
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    print("="*70)
    print("TESTING CORRECTED FORMAT")
    print("="*70)
    print(f"\nPayload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print(f"\nStatus: {response.status_code}")

            if response.status_code < 300:
                print("\n[SUCCESS!]")
                data = response.json()
                print(f"\nResults found: {data.get('totalCount', len(data.get('results', [])))}")
                print(f"Response structure: {list(data.keys())}")
            else:
                print(f"\n[FAILED]")
                print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"\n[ERROR]: {e}")

    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(test())
