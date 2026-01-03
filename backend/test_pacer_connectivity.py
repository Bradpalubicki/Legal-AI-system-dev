"""
Test PACER connectivity and API response
"""
import asyncio
import httpx

async def test_pacer():
    print("="*60)
    print("PACER Connectivity Test")
    print("="*60)

    # Test production PACER (correct subdomain!)
    base_url = "https://pacer.login.uscourts.gov"
    auth_url = f"{base_url}/services/cso-auth"

    print(f"\nTesting: {auth_url}")
    print("-"*60)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Sending test request to PACER...")

            # Send a test auth request (will fail but shows if API is responding)
            response = await client.post(
                auth_url,
                json={
                    "loginId": "test_connectivity",
                    "password": "test_password"
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            try:
                data = response.json()
                print(f"Response Body: {data}")

                if "loginResult" in data:
                    print(f"\n[OK] PACER API is responding!")
                    print(f"Login Result Code: {data.get('loginResult')}")
                    print(f"Error Description: {data.get('errorDescription', 'None')}")
                else:
                    print(f"\n[WARNING] Unexpected response format from PACER")

            except Exception as e:
                print(f"\n[ERROR] Could not parse JSON response: {e}")
                print(f"Raw response: {response.text[:500]}")

    except httpx.TimeoutException:
        print("[ERROR] Connection to PACER timed out")
        print("Possible causes:")
        print("  - PACER servers are down")
        print("  - Network/firewall blocking connection")
        print("  - DNS issues")

    except httpx.ConnectError as e:
        print(f"[ERROR] Cannot connect to PACER: {e}")
        print("Possible causes:")
        print("  - PACER servers are down")
        print("  - Network is offline")
        print("  - Firewall blocking connection")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_pacer())
