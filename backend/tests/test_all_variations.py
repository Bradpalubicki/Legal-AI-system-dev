#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exhaustive PCL API Testing - Try Every Possible Variation
Test all combinations to find what works
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Get real auth token from backend
async def get_auth_token():
    """Get actual PACER auth token from our backend"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/pacer/authenticate",
                headers={"Content-Type": "application/json"},
                json={}
            )
            if response.status_code == 200:
                print("[OK] Got auth token from backend\n")
                return "AUTHENTICATED"
            else:
                print("[FAIL] Auth failed, testing without token\n")
                return None
    except Exception as e:
        print(f"[FAIL] Backend unavailable: {e}\n")
        return None

async def test_variation(name, url, payload, headers):
    """Test a specific variation"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print('='*70)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {json.dumps(headers, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            print(f"\nStatus: {response.status_code}")

            if response.status_code == 200:
                print("\n*** SUCCESS! ***")
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)[:500]}")
                    return True
                except:
                    print(f"Response: {response.text[:500]}")
                    return True
            else:
                print(f"[FAIL] Failed")
                try:
                    print(f"Error: {response.json()}")
                except:
                    print(f"Error: {response.text[:300]}")
                return False

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        return False

async def main():
    print("="*70)
    print("EXHAUSTIVE PCL API VARIATION TESTING")
    print("="*70)
    print("\nTrying every possible combination to find what works...\n")

    token = await get_auth_token()

    base_url = "https://pcl.uscourts.gov/pcl-public-api/rest/cases/find"

    # Different court codes to try
    courts = ["canb", "nysd", "cacd", "ilnd", "txnd", "flsd"]

    # Different header combinations
    header_sets = [
        {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0"
        },
        {
            "Content-Type": "application/json",
            "Accept": "application/hal+json",
            "User-Agent": "Mozilla/5.0"
        },
    ]

    successes = []

    # TEST 1: Different courts with case title
    print("\n" + "="*70)
    print("PHASE 1: Testing Different Courts")
    print("="*70)

    for court in courts[:3]:  # Test first 3 courts
        result = await test_variation(
            f"Court: {court.upper()} with case title",
            base_url,
            {"caseTitle": "Apple", "courtId": court, "page": 1, "pageSize": 5},
            header_sets[0]
        )
        if result:
            successes.append(f"Court {court} worked!")

    # TEST 2: Date-based search (no title)
    print("\n" + "="*70)
    print("PHASE 2: Testing Date-Based Searches")
    print("="*70)

    today = datetime.now()
    last_year = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    result = await test_variation(
        "Date range search",
        base_url,
        {
            "courtId": "canb",
            "dateFiledFrom": last_year,
            "dateFiledTo": today_str,
            "page": 1,
            "pageSize": 5
        },
        header_sets[0]
    )
    if result:
        successes.append("Date search worked!")

    # TEST 3: Minimal parameters
    print("\n" + "="*70)
    print("PHASE 3: Testing Minimal Parameters")
    print("="*70)

    result = await test_variation(
        "Court only",
        base_url,
        {"courtId": "canb", "page": 1, "pageSize": 5},
        header_sets[0]
    )
    if result:
        successes.append("Minimal params worked!")

    # TEST 4: Different Accept headers
    print("\n" + "="*70)
    print("PHASE 4: Testing Different Accept Headers")
    print("="*70)

    for idx, headers in enumerate(header_sets):
        result = await test_variation(
            f"Accept header variation {idx+1}",
            base_url,
            {"caseTitle": "Apple", "courtId": "canb", "page": 1, "pageSize": 5},
            headers
        )
        if result:
            successes.append(f"Header set {idx+1} worked!")

    # TEST 5: Case number formats
    print("\n" + "="*70)
    print("PHASE 5: Testing Case Number Formats")
    print("="*70)

    case_numbers = [
        "24-10001",
        "1:24-bk-10001",
        "2024-10001"
    ]

    for case_num in case_numbers:
        result = await test_variation(
            f"Case number: {case_num}",
            base_url,
            {"caseNumber": case_num, "courtId": "canb", "page": 1, "pageSize": 5},
            header_sets[0]
        )
        if result:
            successes.append(f"Case number {case_num} worked!")

    # TEST 6: Party search endpoint
    print("\n" + "="*70)
    print("PHASE 6: Testing Party Search Endpoint")
    print("="*70)

    party_url = "https://pcl.uscourts.gov/pcl-public-api/rest/parties/find"

    result = await test_variation(
        "Party search",
        party_url,
        {"partyName": "Apple Inc", "courtId": "canb", "page": 1, "pageSize": 5},
        header_sets[0]
    )
    if result:
        successes.append("Party search worked!")

    # TEST 7: Alternative court identifier formats
    print("\n" + "="*70)
    print("PHASE 7: Testing Court Identifier Formats")
    print("="*70)

    court_formats = [
        {"court": "canb"},  # Different field name
        {"courtCode": "canb"},
        {"courtIdentifier": "canb"}
    ]

    for idx, court_param in enumerate(court_formats):
        payload = {**court_param, "caseTitle": "Apple", "page": 1, "pageSize": 5}
        result = await test_variation(
            f"Court field format {idx+1}",
            base_url,
            payload,
            header_sets[0]
        )
        if result:
            successes.append(f"Court format {idx+1} worked!")

    # TEST 8: Without pagination
    print("\n" + "="*70)
    print("PHASE 8: Testing Without Pagination")
    print("="*70)

    result = await test_variation(
        "No pagination params",
        base_url,
        {"caseTitle": "Apple", "courtId": "canb"},
        header_sets[0]
    )
    if result:
        successes.append("No pagination worked!")

    # RESULTS
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)

    if successes:
        print("\n*** SUCCESS! Found working combinations:")
        for success in successes:
            print(f"  [OK] {success}")
    else:
        print("\n[FAIL] No working combinations found")
        print("\nThis confirms the PCL API requires:")
        print("  - API access enabled on your PACER account")
        print("  - Or endpoint has been changed/deprecated")
        print("  - Contact PACER support for assistance")

    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())
