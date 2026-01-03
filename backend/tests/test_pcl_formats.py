#!/usr/bin/env python
"""
Test different PCL API payload formats to find the correct one
"""

import asyncio
import httpx
import json

async def test_format(name, payload):
    """Test a specific payload format"""
    url = "https://pcl.uscourts.gov/pcl-public-api/rest/cases/find"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print('='*70)
    print(f"Payload:\n{json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print(f"\nStatus: {response.status_code}")

            if response.status_code < 300:
                print("[SUCCESS]")
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
                return True
            else:
                print(f"[FAILED]")
                print(f"Error: {response.text[:300]}")
                return False
    except Exception as e:
        print(f"[ERROR]: {e}")
        return False

async def main():
    print("="*70)
    print("PCL API PAYLOAD FORMAT TESTING")
    print("="*70)

    # Format 1: Flat structure with all fields at root
    await test_format("Format 1: Flat with snake_case", {
        "case_title": "Apple",
        "court_id": "canb",
        "page": 1,
        "page_size": 10
    })

    # Format 2: Flat with camelCase
    await test_format("Format 2: Flat with camelCase", {
        "caseTitle": "Apple",
        "courtId": "canb",
        "page": 1,
        "pageSize": 10
    })

    # Format 3: Just required fields
    await test_format("Format 3: Minimal fields", {
        "courtId": "canb"
    })

    # Format 4: With caseNumber instead
    await test_format("Format 4: With case number", {
        "caseNumber": "1:24-bk-10001",
        "courtId": "canb"
    })

    # Format 5: Different field names
    await test_format("Format 5: Alternative field names", {
        "caseName": "Apple",
        "court": "canb"
    })

    # Format 6: Query style
    await test_format("Format 6: Query object", {
        "query": {
            "caseTitle": "Apple",
            "courtId": "canb"
        }
    })

    # Format 7: Criteria style
    await test_format("Format 7: Criteria object", {
        "criteria": {
            "caseTitle": "Apple",
            "courtId": "canb"
        }
    })

    # Format 8: Empty search (to see what API expects)
    await test_format("Format 8: Empty object", {})

    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
